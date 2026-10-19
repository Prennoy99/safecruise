"""SysML model check: the SysML v2 model against the requirements database (needs.json).

M3, ADR-009 (brief §6.3, §12 M3; ADR-001). Loads the model files in one Pilot kernel
session, in dependency order, exports every package as JSON and reads the parsed model
from that export, not from the source text. Errors:

- a model file does not parse or a name does not resolve;
- an ID used as a short name in the model does not exist in needs.json, or the need has
  the wrong type (a requirement usage must name a requirement, a part def an ``ARC_``);
- an ID written anywhere in the model text, comments included, does not exist;
- the same ID is the short name of more than one model element;
- ``ARC_`` needs and ``ARC_`` part defs do not match one to one, by ID and by name
  (part def name = need title);
- a ``satisfy`` names a requirement without an ID, or a part whose definition has no
  ``ARC_`` ID;
- for a ``SYS_``, ``TSR_`` or ``SWR_``, the ``ARC_`` elements whose parts satisfy it in
  the model differ from its ``allocated_to`` set in needs.json (both directions).

With --views, also renders the views listed in VIEWS as SVG files into the given folder;
a view the renderer marks as possibly incomplete is an error.

Usage: python tools/sysml_check.py NEEDS.json [--views DIR] [FILE.sysml ...]
Without files, checks MODEL_FILES. Exit code 0 if there is no error, 1 otherwise.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):  # run as a script: make `tools` importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.sysml_parse import KernelSession, print_result
from tools.trace_check import load_needs

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model" / "sysml"
# Dependency order: a file may only use packages of the files before it (ADR-001).
MODEL_FILES = [
    MODEL_DIR / name
    for name in (
        "Interfaces.sysml",
        "AccModes.sysml",
        "SafeCruise.sysml",
        "Requirements.sysml",
        "Allocation.sysml",
    )
]
# (file name, %viz arguments) of the views shown in docs/07_architecture.rst.
VIEWS = [
    ("item_context.svg", "--view=interconnection --style=LR SafeCruise::SafeCruiseItem"),
    ("ecu_structure.svg", "--view=interconnection --style=LR --style=ORTHOLINE SafeCruise::AccEcu"),
    ("ecu_cycle.svg", "--view=action SafeCruise::EcuCycle"),
    ("acc_modes.svg", "--view=state SafeCruiseModes::AccModes"),
]
# The renderer stops after a fixed number of model elements and then marks the view as
# possibly incomplete; such a view must not reach the docs (ADR-009).
VIEW_LIMIT_MARK = "EXCEEDS THE LIMIT"

ID = re.compile(r"\b(?:STK|HE|SG|SYS|FSR|TSR|AOU|SWR|ARC|TC)(?:_[A-Z0-9]+)+\b")
REQUIREMENT_TYPES = {"sys", "fsr", "tsr", "aou", "swr"}
ALLOCATION_TYPES = {"sys", "tsr", "swr"}
PACKAGE = re.compile(r"^Package (\S+) \(", re.MULTILINE)


@dataclass
class Satisfy:
    requirement: str | None  # ID (short name) of the satisfied requirement
    requirement_name: str
    arc: str | None  # ARC_ ID of the satisfying part's definition
    part: str


@dataclass
class ModelFacts:
    requirements: dict[str, list[str]] = field(default_factory=dict)  # ID -> qualified names
    parts: dict[str, list[str]] = field(default_factory=dict)  # ARC_ ID -> part def names
    other_ids: dict[str, list[str]] = field(default_factory=dict)  # ID on any other element
    satisfies: list[Satisfy] = field(default_factory=list)
    text_ids: dict[str, list[str]] = field(default_factory=dict)  # ID -> "file:line"


def facts_from_export(elements: list[dict]) -> ModelFacts:
    """Collect the facts the check needs from the JSON export of the model packages."""
    by_id = {e["payload"]["@id"]: e["payload"] for e in elements}
    facts = ModelFacts()

    def ref(ref_: dict | None) -> dict:
        return by_id.get(ref_["@id"], {}) if ref_ else {}

    for el in by_id.values():
        short, kind = el.get("declaredShortName"), el["@type"]
        name = el.get("qualifiedName") or el.get("declaredName") or ""
        if el.get("isLibraryElement"):  # referenced library elements, e.g. <km> in SI
            short = None
        if short and kind in ("RequirementUsage", "RequirementDefinition"):
            facts.requirements.setdefault(short, []).append(name)
        elif short and kind == "PartDefinition":
            facts.parts.setdefault(short, []).append(el.get("declaredName") or "")
        elif short and ID.fullmatch(short):
            facts.other_ids.setdefault(short, []).append(f"{kind} {name}")
        if kind == "SatisfyRequirementUsage":
            req = ref(el.get("satisfiedRequirement"))
            part = ref(el.get("satisfyingFeature"))
            defs = [ref(d) for d in part.get("partDefinition", [])]
            arcs = [d["declaredShortName"] for d in defs if d.get("declaredShortName")]
            facts.satisfies.append(
                Satisfy(
                    requirement=req.get("declaredShortName"),
                    requirement_name=req.get("qualifiedName") or "?",
                    arc=arcs[0] if len(arcs) == 1 else None,
                    part=part.get("qualifiedName") or "?",
                )
            )
    return facts


def text_ids(files: list[Path]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    for path in files:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for nid in ID.findall(line):
                found[nid].append(f"{_rel(path)}:{lineno}")
    return dict(found)


def check(model: ModelFacts, needs: dict[str, dict]) -> list[str]:
    errors: list[str] = []

    def ntype(nid: str) -> str | None:
        return needs[nid]["type"] if nid in needs else None

    for nid, names in sorted(model.requirements.items()):
        if ntype(nid) not in REQUIREMENT_TYPES:
            errors.append(f"{nid}: requirement {names[0]} " + _missing_or_type(nid, needs))
    for nid, names in sorted(model.parts.items()):
        if ntype(nid) != "arc":
            errors.append(f"{nid}: part def {names[0]} " + _missing_or_type(nid, needs))
    for nid, names in sorted(model.other_ids.items()):
        if nid not in needs:
            errors.append(f"{nid}: {names[0]} does not exist in needs.json")
    for nid, where in sorted(model.text_ids.items()):
        if nid not in needs:
            errors.append(f"{nid}: written in {', '.join(where)}, does not exist in needs.json")

    all_short: dict[str, list[str]] = defaultdict(list)
    for group in (model.requirements, model.parts, model.other_ids):
        for nid, names in group.items():
            all_short[nid].extend(names)
    for nid, names in sorted(all_short.items()):
        if len(names) > 1:
            errors.append(f"{nid}: short name of {len(names)} model elements ({', '.join(names)})")

    for nid in sorted(n for n, need in needs.items() if need["type"] == "arc"):
        title = needs[nid].get("title", "")
        if nid not in model.parts:
            errors.append(f"{nid}: no part def with this short name in the model")
        elif model.parts[nid][0] != title:
            errors.append(f"{nid}: part def is named {model.parts[nid][0]}, need title is {title}")

    satisfied: dict[str, set[str]] = defaultdict(set)
    for sat in model.satisfies:
        if sat.requirement is None:
            errors.append(f"satisfy {sat.requirement_name} by {sat.part}: requirement has no ID")
        if sat.arc is None:
            errors.append(f"satisfy {sat.requirement_name} by {sat.part}: part has no ARC_ ID")
        if sat.requirement and sat.arc:
            satisfied[sat.requirement].add(sat.arc)
    allocated_needs = {n for n, need in needs.items() if need.get("allocated_to")}
    for nid in sorted(set(satisfied) | allocated_needs):
        if ntype(nid) not in ALLOCATION_TYPES:
            continue
        allocated = {a for a in needs[nid].get("allocated_to", []) if ntype(a) == "arc"}
        in_model = satisfied.get(nid, set())
        for arc in sorted(allocated - in_model):
            errors.append(f"{nid}: allocated to {arc} in needs.json, not satisfied in the model")
        for arc in sorted(in_model - allocated):
            errors.append(f"{nid}: satisfied by {arc} in the model, not allocated in needs.json")
    return errors


def _missing_or_type(nid: str, needs: dict[str, dict]) -> str:
    if nid not in needs:
        return "does not exist in needs.json"
    return f"is a {needs[nid]['type'].upper()} in needs.json"


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _export(kernel: KernelSession, package: str) -> list[dict]:
    res = kernel.run(f"%export {package}")
    html = res.data.get("text/html", "")
    m = re.search(r"base64,([A-Za-z0-9+/=]+)", html)
    if not res.ok or not m:
        raise RuntimeError(f"%export {package} failed: {''.join(res.text)}")
    return json.loads(base64.b64decode(m.group(1)))


def _clean_svg(svg: str) -> str:
    """Drop the kernel's psysml: links; they point into the kernel session."""
    svg = re.sub(r"<a [^>]*>", "<g>", svg)
    return svg.replace("</a>", "</g>")


def load_model(files: list[Path], views_dir: Path | None) -> tuple[ModelFacts | None, list[str]]:
    """Parse the files in one kernel session; return the facts, or None if parsing failed."""
    elements: list[dict] = []
    failures: list[str] = []
    with KernelSession() as kernel:
        packages: list[str] = []
        for path in files:
            res = kernel.run(path.read_text(encoding="utf-8"))
            print_result(Path(_rel(path)), res)
            if not res.ok:
                failures.append(f"{_rel(path)}: does not parse")
            packages += PACKAGE.findall("".join(res.text))
        if failures:
            return None, failures
        for package in packages:
            elements += _export(kernel, package)
        if views_dir is not None:
            views_dir.mkdir(parents=True, exist_ok=True)
            for name, viz in VIEWS:
                res = kernel.run(f"%viz {viz}")
                svg = res.data.get("image/svg+xml")
                if not res.ok or not svg:
                    failures.append(f"view {name} ({viz}) did not render: {''.join(res.text)}")
                    continue
                if VIEW_LIMIT_MARK in svg:
                    failures.append(f"view {name}: exceeds the renderer's element limit")
                (views_dir / name).write_text(_clean_svg(svg), encoding="utf-8")
                print(f"[VIEW] {_rel(views_dir / name)}")
    facts = facts_from_export(elements)
    facts.text_ids = text_ids(files)
    return facts, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("needs_json", type=Path)
    parser.add_argument("files", nargs="*", type=Path, help="model files in load order")
    parser.add_argument("--views", type=Path, metavar="DIR", help="render the views into DIR")
    args = parser.parse_args(argv)

    files = args.files or MODEL_FILES
    needs = load_needs(args.needs_json)
    facts, errors = load_model(files, args.views)
    if facts is not None:
        errors += check(facts, needs)
        print(
            f"SysML check: {len(files)} files, {len(facts.requirements)} requirement IDs, "
            f"{len(facts.parts)} ARC_ part defs, {len(facts.satisfies)} satisfy relations"
        )
    if errors:
        print(f"Errors: {len(errors)}")
        for err in errors:
            print(f"  {err}")
    print("Result: " + ("FAIL" if errors else "PASS"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
