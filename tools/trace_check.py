"""Trace gate: check the links between needs in needs.json.

M2 first version, ADR-005 (brief §6.3, ADR-000 D-17, D-18). Errors:

- a link points to a need that does not exist, or to a need of the wrong type (LINK_TARGETS);
- a safety goal without an FSR, an FSR without a TSR or AOU, a TSR without an allocation,
  a system requirement that satisfies no stakeholder need;
- a derived safety requirement whose ASIL does not inherit its parents' ASIL: the target
  ASIL (the bracketed part of a decomposed ASIL such as B(D), else the ASIL itself) must
  equal the highest target ASIL of its parents.

Warnings (errors with --strict, which M6 switches on):

- a SYS_, TSR_ or SWR_ that no TC_ verifies;
- a need with ASIL A or higher that is still ``draft`` (a milestone is done only with none).

Checking test results from JUnit XML is added in M6.

Usage: python tools/trace_check.py [--strict] NEEDS.json
Exit code 0 if there is no error (and, with --strict, no warning), 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

LINK_OPTIONS = ("satisfies", "derives_from", "allocated_to", "verifies")
REQUIREMENTS = {"sys", "fsr", "tsr", "aou", "swr"}

# (source type, link option) -> allowed target types
LINK_TARGETS = {
    ("sg", "derives_from"): {"he"},
    ("sys", "satisfies"): {"stk"},
    ("fsr", "derives_from"): {"sg"},
    ("tsr", "derives_from"): {"fsr"},
    ("aou", "derives_from"): {"fsr", "sys"},
    ("swr", "derives_from"): {"sys", "tsr"},
    ("sys", "allocated_to"): {"arc"},
    ("fsr", "allocated_to"): {"arc"},
    ("tsr", "allocated_to"): {"arc"},
    ("swr", "allocated_to"): {"arc"},
    ("tc", "verifies"): REQUIREMENTS,
}

ASIL_ORDER = ("QM", "A", "B", "C", "D")
ASIL = re.compile(r"(QM|[A-D])(?:\((QM|[A-D])\))?")


def target_asil(asil: str) -> str | None:
    """Target ASIL: the bracketed part of a decomposed ASIL, else the ASIL; None if invalid."""
    m = ASIL.fullmatch(asil.strip())
    return (m.group(2) or m.group(1)) if m else None


def achieved_asil(asil: str) -> str | None:
    """ASIL the element itself is developed to: the part before the brackets."""
    m = ASIL.fullmatch(asil.strip())
    return m.group(1) if m else None


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _back(need: dict, option: str, needs: dict[str, dict], types: set[str]) -> list[str]:
    return [n for n in need.get(f"{option}_back", []) if n in needs and needs[n]["type"] in types]


def check(needs: dict[str, dict]) -> Report:
    report = Report()
    for nid in sorted(needs):
        need = needs[nid]
        ntype = need["type"]

        for option in LINK_OPTIONS:
            for target in need.get(option, []):
                if target not in needs:
                    report.errors.append(f"{nid}: {option} {target} does not exist")
                    continue
                allowed = LINK_TARGETS.get((ntype, option))
                if allowed is None or needs[target]["type"] not in allowed:
                    report.errors.append(
                        f"{nid}: {option} {target} ({needs[target]['type'].upper()}) "
                        f"is not allowed from {ntype.upper()}"
                    )

        if ntype == "sg" and not _back(need, "derives_from", needs, {"fsr"}):
            report.errors.append(f"{nid}: no FSR derives from this safety goal")
        if ntype == "fsr" and not _back(need, "derives_from", needs, {"tsr", "aou"}):
            report.errors.append(f"{nid}: no TSR or AOU derives from this FSR")
        if ntype == "tsr" and not need.get("allocated_to"):
            report.errors.append(f"{nid}: not allocated to an architecture element")
        if ntype == "sys" and not need.get("satisfies"):
            report.errors.append(f"{nid}: satisfies no stakeholder need")

        if ntype in ("fsr", "tsr", "aou"):
            parents = [needs[p] for p in need.get("derives_from", []) if p in needs and p != nid]
            parent_targets = [target_asil(p.get("asil", "")) for p in parents]
            own = target_asil(need.get("asil", ""))
            if parents and own and None not in parent_targets:
                expected = max(parent_targets, key=ASIL_ORDER.index)
                if own != expected:
                    report.errors.append(
                        f"{nid}: target ASIL {own} does not inherit its parents' {expected}"
                    )

        if ntype in ("sys", "tsr", "swr") and not _back(need, "verifies", needs, {"tc"}):
            report.warnings.append(f"{nid}: no test case verifies it")
        achieved = achieved_asil(need.get("asil", ""))
        if achieved not in (None, "QM") and need.get("status") != "approved":
            report.warnings.append(f"{nid}: ASIL {need['asil']} but status {need.get('status')}")
    return report


def load_needs(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["versions"][data["current_version"]]["needs"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("needs_json", type=Path)
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args(argv)

    needs = load_needs(args.needs_json)
    report = check(needs)
    print(f"Trace gate: {len(needs)} needs" + (" (strict)" if args.strict else ""))
    for title, items in (("Errors", report.errors), ("Warnings", report.warnings)):
        if items:
            print(f"{title}: {len(items)}")
            for item in items:
                print(f"  {item}")
    failed = bool(report.errors or (args.strict and report.warnings))
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
