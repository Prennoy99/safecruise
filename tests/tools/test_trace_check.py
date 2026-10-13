"""tools/trace_check.py: link rules, coverage, ASIL inheritance (ADR-005).

The needs below are fixtures, not project requirements.
"""

import json
from pathlib import Path

import pytest

from tools import trace_check
from tools.trace_check import achieved_asil, check, target_asil


def _need(nid: str, asil: str = "", status: str = "approved", **links: list[str]) -> dict:
    return {"id": nid, "type": nid.split("_")[0].lower(), "asil": asil, "status": status, **links}


def _with_back_links(*needs: dict) -> dict[str, dict]:
    """Add the *_back lists that sphinx-needs writes into needs.json."""
    by_id = {n["id"]: n for n in needs}
    for n in needs:
        for option in trace_check.LINK_OPTIONS:
            for target in n.get(option, []):
                if target in by_id:
                    by_id[target].setdefault(f"{option}_back", []).append(n["id"])
    return by_id


def _chain() -> list[dict]:
    return [
        _need("HE_OS1_M1", "B"),
        _need("SG_X_1", "B", derives_from=["HE_OS1_M1"]),
        _need("STK_X_1"),
        _need("ARC_X"),
        _need("FSR_X_1", "B", derives_from=["SG_X_1"], allocated_to=["ARC_X"]),
        _need("TSR_X_1", "B(B)", derives_from=["FSR_X_1"], allocated_to=["ARC_X"]),
        _need("TSR_X_2", "QM(B)", derives_from=["FSR_X_1"], allocated_to=["ARC_X"]),
        _need("AOU_X_1", "B", derives_from=["FSR_X_1"]),
        _need("SYS_X_1", "QM", satisfies=["STK_X_1"]),
        _need("TC_X_1", verifies=["SYS_X_1", "TSR_X_1", "TSR_X_2"]),
    ]


def test_complete_chain_passes() -> None:
    report = check(_with_back_links(*_chain()))
    assert (report.errors, report.warnings) == ([], [])


@pytest.mark.parametrize(
    ("asil", "target", "achieved"),
    [
        ("B", "B", "B"),
        ("B(D)", "D", "B"),
        ("QM(B)", "B", "QM"),
        ("", None, None),
        ("E", None, None),
    ],
)
def test_asil_parts(asil: str, target: str | None, achieved: str | None) -> None:
    assert (target_asil(asil), achieved_asil(asil)) == (target, achieved)


def _replace(chain: list[dict], nid: str, **changes: object) -> list[dict]:
    return [{**n, **changes} if n["id"] == nid else n for n in chain]


@pytest.mark.parametrize(
    ("nid", "changes", "error"),
    [
        (
            "TSR_X_1",
            {"derives_from": ["FSR_GONE"]},
            "TSR_X_1: derives_from FSR_GONE does not exist",
        ),
        (
            "TSR_X_1",
            {"derives_from": ["SG_X_1"]},
            "TSR_X_1: derives_from SG_X_1 (SG) is not allowed",
        ),
        ("SYS_X_1", {"allocated_to": ["STK_X_1"]}, "SYS_X_1: allocated_to STK_X_1 (STK) is not"),
        ("TC_X_1", {"verifies": ["ARC_X"]}, "TC_X_1: verifies ARC_X (ARC) is not allowed"),
        ("TSR_X_1", {"allocated_to": []}, "TSR_X_1: not allocated to an architecture element"),
        ("SYS_X_1", {"satisfies": []}, "SYS_X_1: satisfies no stakeholder need"),
        ("TSR_X_1", {"asil": "B(C)"}, "TSR_X_1: target ASIL C does not inherit its parents' B"),
        ("FSR_X_1", {"asil": "A"}, "FSR_X_1: target ASIL A does not inherit its parents' B"),
    ],
)
def test_link_errors(nid: str, changes: dict, error: str) -> None:
    report = check(_with_back_links(*_replace(_chain(), nid, **changes)))
    assert any(e.startswith(error) for e in report.errors), report.errors


def test_safety_goal_without_fsr() -> None:
    chain = [n for n in _chain() if n["id"] not in ("FSR_X_1", "TSR_X_1", "TSR_X_2", "AOU_X_1")]
    assert "SG_X_1: no FSR derives from this safety goal" in check(_with_back_links(*chain)).errors


def test_fsr_without_tsr_or_aou() -> None:
    chain = [n for n in _chain() if n["id"] not in ("TSR_X_1", "TSR_X_2", "AOU_X_1")]
    chain = _replace(chain, "TC_X_1", verifies=["SYS_X_1"])
    assert "FSR_X_1: no TSR or AOU derives from this FSR" in check(_with_back_links(*chain)).errors


def test_fsr_covered_by_aou_only_is_enough() -> None:
    chain = [n for n in _chain() if n["id"] not in ("TSR_X_1", "TSR_X_2")]
    chain = _replace(chain, "TC_X_1", verifies=["SYS_X_1"])
    assert check(_with_back_links(*chain)).errors == []


def test_warnings_for_missing_tests_and_drafts() -> None:
    chain = _replace(_chain(), "TC_X_1", verifies=["TSR_X_1"])
    chain = _replace(chain, "TSR_X_1", status="draft")
    report = check(_with_back_links(*chain))
    assert report.errors == []
    assert report.warnings == [
        "SYS_X_1: no test case verifies it",
        "TSR_X_1: ASIL B(B) but status draft",
        "TSR_X_2: no test case verifies it",
    ]


def test_strict_turns_warnings_into_failure(tmp_path: Path) -> None:
    chain = _replace(_chain(), "TSR_X_1", status="draft")
    path = tmp_path / "needs.json"
    needs = _with_back_links(*chain)
    path.write_text(json.dumps({"current_version": "", "versions": {"": {"needs": needs}}}))
    assert trace_check.main([str(path)]) == 0
    assert trace_check.main(["--strict", str(path)]) == 1
