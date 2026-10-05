"""Check the HARA and safety goals in needs.json for completeness and ASIL arithmetic.

M1, ADR-004. Reads the hazardous events (HE_) and safety goals (SG_) exported by
`sphinx-build -b needs` and reports two kinds of finding:

- open: a value pb still owes (a ``⟨pb: …⟩`` placeholder or an empty field);
- error: a value that is present but wrong (out of range, ASIL not matching the ratings,
  safety-goal ASIL not matching its hazardous events, missing links).

Optional source files are scanned for placeholders in prose; lines that set a need option
(``   :name: value``) are skipped there because the needs check already reports them.

Usage: python tools/hara_check.py NEEDS.json [SOURCE.rst ...]
Exit code 0 if nothing is open and nothing is wrong, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PLACEHOLDER = "⟨pb"
ASILS = ("QM", "A", "B", "C", "D")
HE_ID = re.compile(r"HE_(OS\d+)_(M\d+)(?:_[A-Z0-9]+)*")
NEED_OPTION_LINE = re.compile(r"^\s+:[a-z_]+:")

# (attribute, class letter, highest class) for the three ratings of a hazardous event
RATINGS = (("severity", "S", 3), ("exposure", "E", 4), ("controllability", "C", 3))


def determine_asil(s: int, e: int, c: int) -> str:
    """ASIL for severity class s, exposure class e and controllability class c.

    Implements the ASIL determination table of ISO 26262-3 (clause 6) through its sum
    form: any class 0 gives QM; otherwise s + e + c of 10, 9, 8, 7 gives D, C, B, A and
    any lower sum gives QM.
    """
    if not (0 <= s <= 3 and 0 <= e <= 4 and 0 <= c <= 3):
        raise ValueError(f"class out of range: S{s} E{e} C{c}")
    if 0 in (s, e, c):
        return "QM"
    return {10: "D", 9: "C", 8: "B", 7: "A"}.get(s + e + c, "QM")


@dataclass
class Report:
    hazardous_events: int = 0
    safety_goals: int = 0
    open: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.hazardous_events > 0 and not self.open and not self.errors


def _is_open(value: str) -> bool:
    return not value.strip() or PLACEHOLDER in value


def _parse_class(value: str, letter: str, highest: int) -> int | None:
    m = re.fullmatch(rf"{letter}([0-{highest}])", value.strip())
    return int(m.group(1)) if m else None


def _check_hazardous_event(need: dict, report: Report) -> str | None:
    """Check one HE_; return its ASIL if it is present and valid, else None."""
    nid = need["id"]
    m = HE_ID.fullmatch(nid)
    if not m:
        report.errors.append(f"{nid}: ID must be HE_OS<n>_M<n>[_SUFFIX]")
    else:
        for attr, expected in (("situation", m.group(1)), ("malfunction", m.group(2))):
            if need.get(attr, "") != expected:
                report.errors.append(f"{nid}: {attr} {need.get(attr)!r} does not match ID")

    open_fields = []
    classes: dict[str, int] = {}
    for attr, letter, highest in RATINGS:
        value = need.get(attr, "")
        if _is_open(value):
            open_fields.append(attr)
        elif (cls := _parse_class(value, letter, highest)) is None:
            report.errors.append(f"{nid}: {attr} {value!r} is not {letter}0..{letter}{highest}")
        else:
            classes[letter] = cls
        if _is_open(need.get(f"{attr}_rationale", "")):
            open_fields.append(f"{attr}_rationale")

    asil = need.get("asil", "")
    if _is_open(asil):
        open_fields.append("asil")
        asil = None
    elif asil not in ASILS:
        report.errors.append(f"{nid}: asil {asil!r} is not one of {', '.join(ASILS)}")
        asil = None
    elif len(classes) == 3:
        expected = determine_asil(classes["S"], classes["E"], classes["C"])
        if asil != expected:
            ratings = "/".join(need[a] for a, _, _ in RATINGS)
            report.errors.append(f"{nid}: asil {asil} does not match {ratings} (gives {expected})")

    if open_fields:
        report.open.append(f"{nid}: {', '.join(open_fields)}")
    if asil not in (None, "QM") and not any(
        g.startswith("SG_") for g in need.get("derives_from_back", [])
    ):
        report.errors.append(f"{nid}: ASIL {asil} but no safety goal derives from it")
    return asil


def _check_safety_goal(need: dict, he_asils: dict[str, str | None], report: Report) -> None:
    nid = need["id"]
    links = need.get("derives_from", [])
    if not links:
        report.errors.append(f"{nid}: derives from no hazardous event")
    for link in links:
        if link not in he_asils:
            report.errors.append(f"{nid}: derives_from {link} is not a hazardous event")

    open_fields = [a for a in ("asil", "safe_state", "ftti_ms") if _is_open(need.get(a, ""))]
    if open_fields:
        report.open.append(f"{nid}: {', '.join(open_fields)}")

    asil = need.get("asil", "")
    if "asil" not in open_fields:
        if asil not in ASILS:
            report.errors.append(f"{nid}: asil {asil!r} is not one of {', '.join(ASILS)}")
        else:
            linked = [he_asils.get(link) for link in links if link in he_asils]
            if linked and None not in linked:
                highest = max(linked, key=ASILS.index)
                if asil != highest:
                    report.errors.append(
                        f"{nid}: asil {asil} is not the highest ASIL of its hazardous "
                        f"events ({highest})"
                    )

    ftti = need.get("ftti_ms", "")
    if "ftti_ms" not in open_fields and not re.fullmatch(r"[1-9]\d*", ftti.strip()):
        report.errors.append(f"{nid}: ftti_ms {ftti!r} is not a positive whole number")


def check_needs(needs: dict[str, dict]) -> Report:
    report = Report()
    he_asils: dict[str, str | None] = {}
    for nid in sorted(needs):
        if needs[nid]["type"] == "he":
            report.hazardous_events += 1
            he_asils[nid] = _check_hazardous_event(needs[nid], report)
    for nid in sorted(needs):
        if needs[nid]["type"] == "sg":
            report.safety_goals += 1
            _check_safety_goal(needs[nid], he_asils, report)
    if not report.hazardous_events:
        report.errors.append("no hazardous events (HE_) found")
    return report


def check_sources(paths: list[Path], report: Report) -> None:
    for path in paths:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if PLACEHOLDER in line and not NEED_OPTION_LINE.match(line):
                report.open.append(f"{path}:{lineno}: {line.strip()}")


def load_needs(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["versions"][data["current_version"]]["needs"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("needs_json", type=Path)
    parser.add_argument("sources", nargs="*", type=Path, help="files to scan for placeholders")
    args = parser.parse_args(argv)

    report = check_needs(load_needs(args.needs_json))
    check_sources(args.sources, report)

    print(f"HARA check: {report.hazardous_events} hazardous events, {report.safety_goals} goals")
    for title, items in (("Open (pb)", report.open), ("Errors", report.errors)):
        if items:
            print(f"{title}: {len(items)}")
            for item in items:
                print(f"  {item}")
    print("Result: " + ("PASS" if report.ok else "FAIL"))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
