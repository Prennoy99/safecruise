"""Lint the requirements in needs.json: EARS form, wording, values, attributes and IDs.

M2, ADR-005 (brief §6.2, ADR-000 D-17). Requirements are the needs of type SYS, FSR, TSR,
AOU and SWR. Their statement is the first paragraph of the need's content; later paragraphs
(rationale, notes) are not linted. Checks:

- the statement matches one EARS template and contains exactly one "shall";
- it contains none of the vague words in VAGUE;
- every number in it carries a unit (or belongs to a list whose last number does);
- the need has the attributes its type requires, with allowed values;
- for every need (not only requirements): the ID prefix matches the directive, and no
  field or content holds a ``⟨pb: …⟩`` placeholder.

Usage: python tools/ears_lint.py NEEDS.json
Exit code 0 if no finding, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIREMENT_TYPES = ("sys", "fsr", "tsr", "aou", "swr")
PLACEHOLDER = "⟨pb"

EARS = re.compile(
    r"^(?:"
    r"The (?P<u>.+?)"  # ubiquitous
    r"|(?:While|When|Where) .+?, the (?P<c>.+?)"  # state-, event-driven, optional (or mixed)
    r"|If .+?, then the (?P<i>.+?)"  # unwanted behaviour
    r") shall .+\.$"
)
SHALL = re.compile(r"\bshall\b", re.IGNORECASE)
VAGUE = (
    "fast",
    "quick",
    "quickly",
    "immediately",
    "timely",
    "as soon as possible",
    "appropriate",
    "appropriately",
    "adequate",
    "sufficient",
    "sufficiently",
    "reasonable",
    "user-friendly",
    "approximately",
    "about",
    "if possible",
    "etc",
    "and/or",
)
VAGUE_RE = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(w) for w in VAGUE) + r")(?![\w-])", re.IGNORECASE
)

# A number that stands alone: not part of an ID (SG_ACC_001), an assumption (A-04), a name
# (E2E, CRC-8, J1850) or a hex value.
NUMBER = re.compile(r"(?<![\w\-./])\d+(?:\.\d+)?(?!\w|\.\d)")
UNIT = re.compile(
    r"\s?(?:consecutive\s)?(?:km/h|m/s²|m/s³|m/s|ms|Hz|%|s|m"
    r"|cycles?|frames?|messages?|objects?|errors?|ticks?|bits?|times)(?![A-Za-z])"
    r"|-bit\b"
)
# Joins between list items; \u2013 is an en dash, \u2212 a minus sign.
LIST_JOIN = re.compile(r"\s*(?:,|/|\u2013|-|\bor\b|\band\b|\bto\b)\s*(?=[+\u2212-]?\d)")

ASIL = re.compile(r"(?:QM|[A-D])(?:\((?:QM|[A-D])\))?")
VERIFICATION_METHODS = ("test", "analysis", "inspection", "review")
REQUIRED = {
    # type: (needs asil, needs verification_method)
    "sys": (True, True),
    "fsr": (True, True),
    "tsr": (True, True),
    "aou": (True, False),
    "swr": (True, True),
}


def statement(content: str) -> str:
    """First paragraph of a need's content, with inline reStructuredText markup removed."""
    first = re.split(r"\n\s*\n", content.strip(), maxsplit=1)[0]
    text = " ".join(line.strip() for line in first.splitlines())
    text = re.sub(r":\w+:`([^`<]*?)(?:\s*<[^>]+>)?`", r"\1", text)  # roles, :need:`X`
    text = re.sub(r"``([^`]*)``", r"\1", text)
    return re.sub(r"\*\*?([^*]+)\*\*?", r"\1", text)


def numbers_without_unit(text: str) -> list[str]:
    """Numbers in text that carry no unit, directly or as part of a list that ends in one."""
    matches = list(NUMBER.finditer(text))
    has_unit: dict[int, bool] = {}
    for i in range(len(matches) - 1, -1, -1):
        m = matches[i]
        rest = text[m.end() :]
        if UNIT.match(rest):
            has_unit[i] = True
        elif (
            i + 1 < len(matches)
            and (j := LIST_JOIN.match(rest))
            and m.end() + j.end() + (1 if text[m.end() + j.end()] in "+\u2212-" else 0)
            == matches[i + 1].start()
        ):
            has_unit[i] = has_unit[i + 1]
        else:
            has_unit[i] = False
    return [m.group() for i, m in enumerate(matches) if not has_unit[i]]


def lint_requirement(need: dict) -> list[str]:
    findings = []
    text = statement(need.get("content", ""))
    if not text:
        return ["no requirement statement"]
    if len(SHALL.findall(text)) != 1:
        findings.append(f'{len(SHALL.findall(text))} times "shall", expected exactly 1')
    elif not EARS.match(text):
        findings.append("matches no EARS template")
    for word in sorted({m.group(1).lower() for m in VAGUE_RE.finditer(text)}):
        findings.append(f'vague word "{word}"')
    for number in numbers_without_unit(text):
        findings.append(f"number {number} without unit")

    needs_asil, needs_method = REQUIRED[need["type"]]
    asil = need.get("asil", "")
    if needs_asil and not ASIL.fullmatch(asil):
        findings.append(f"asil {asil!r} is not QM, A-D or decomposed like B(D)")
    method = need.get("verification_method", "")
    if needs_method and method not in VERIFICATION_METHODS:
        findings.append(
            f"verification_method {method!r} is not one of {', '.join(VERIFICATION_METHODS)}"
        )
    return findings


def lint_any(need: dict) -> list[str]:
    findings = []
    prefix = need["type"].upper() + "_"
    if not need["id"].startswith(prefix):
        findings.append(f"ID does not start with {prefix} for a '{need['type']}' need")
    open_fields = [k for k, v in sorted(need.items()) if isinstance(v, str) and PLACEHOLDER in v]
    if open_fields:
        findings.append(f"placeholder in {', '.join(open_fields)}")
    return findings


def lint(needs: dict[str, dict]) -> dict[str, list[str]]:
    report: dict[str, list[str]] = {}
    for nid in sorted(needs):
        need = needs[nid]
        findings = lint_any(need)
        if need["type"] in REQUIREMENT_TYPES:
            findings += lint_requirement(need)
        if findings:
            report[nid] = findings
    return report


def load_needs(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["versions"][data["current_version"]]["needs"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("needs_json", type=Path)
    args = parser.parse_args(argv)

    needs = load_needs(args.needs_json)
    report = lint(needs)
    count = sum(1 for n in needs.values() if n["type"] in REQUIREMENT_TYPES)
    print(f"EARS lint: {count} requirements, {len(needs)} needs")
    for nid, findings in report.items():
        for finding in findings:
            print(f"  {nid}: {finding}")
    print("Result: " + ("FAIL" if report else "PASS"))
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
