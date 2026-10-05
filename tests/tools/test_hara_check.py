"""tools/hara_check.py: ASIL arithmetic, completeness and consistency of HE_ and SG_ (ADR-004).

The needs below are fixtures, not project ratings.
"""

import json
from pathlib import Path

import pytest

from tools import hara_check
from tools.hara_check import check_needs, determine_asil


@pytest.mark.parametrize(
    ("s", "e", "c", "asil"),
    [
        (3, 4, 3, "D"),
        (3, 4, 2, "C"),
        (3, 3, 2, "B"),
        (2, 4, 3, "C"),
        (1, 4, 3, "B"),
        (1, 3, 3, "A"),
        (3, 1, 3, "A"),
        (2, 2, 3, "A"),
        (3, 1, 2, "QM"),
        (1, 4, 1, "QM"),
        (0, 4, 3, "QM"),
        (3, 0, 3, "QM"),
        (3, 4, 0, "QM"),
    ],
)
def test_determine_asil(s: int, e: int, c: int, asil: str) -> None:
    assert determine_asil(s, e, c) == asil


@pytest.mark.parametrize(("s", "e", "c"), [(4, 1, 1), (1, 5, 1), (1, 1, 4), (-1, 1, 1)])
def test_determine_asil_rejects_classes_out_of_range(s: int, e: int, c: int) -> None:
    with pytest.raises(ValueError):
        determine_asil(s, e, c)


def test_determine_asil_never_decreases_with_any_class() -> None:
    order = hara_check.ASILS.index
    for s in range(4):
        for e in range(5):
            for c in range(4):
                here = order(determine_asil(s, e, c))
                if s < 3:
                    assert order(determine_asil(s + 1, e, c)) >= here
                if e < 4:
                    assert order(determine_asil(s, e + 1, c)) >= here
                if c < 3:
                    assert order(determine_asil(s, e, c + 1)) >= here


def _he(nid: str, s: str, e: str, c: str, asil: str, goals: list[str]) -> dict:
    situation, malfunction = nid.split("_")[1:3]
    return {
        "id": nid,
        "type": "he",
        "situation": situation,
        "malfunction": malfunction,
        "severity": s,
        "severity_rationale": "reason",
        "exposure": e,
        "exposure_rationale": "reason",
        "controllability": c,
        "controllability_rationale": "reason",
        "asil": asil,
        "derives_from_back": goals,
    }


def _sg(nid: str, asil: str, events: list[str], ftti: str = "500") -> dict:
    return {
        "id": nid,
        "type": "sg",
        "asil": asil,
        "safe_state": "ACC off, TOR on",
        "ftti_ms": ftti,
        "derives_from": events,
    }


def _needs(*needs: dict) -> dict[str, dict]:
    return {n["id"]: n for n in needs}


def _consistent() -> dict[str, dict]:
    return _needs(
        _he("HE_OS1_M1", "S3", "E4", "C2", "C", ["SG_X_1"]),
        _he("HE_OS2_M1", "S2", "E3", "C2", "A", ["SG_X_1"]),
        _he("HE_OS5_M2", "S1", "E2", "C1", "QM", []),
        _sg("SG_X_1", "C", ["HE_OS1_M1", "HE_OS2_M1"]),
    )


def test_consistent_hara_passes() -> None:
    report = check_needs(_consistent())
    assert (report.open, report.errors) == ([], [])
    assert report.ok
    assert (report.hazardous_events, report.safety_goals) == (3, 1)


def test_placeholders_are_open_not_errors() -> None:
    needs = _consistent()
    needs["HE_OS1_M1"].update(severity="⟨pb: S⟩", exposure_rationale="⟨pb: why⟩", asil="⟨pb⟩")
    needs["SG_X_1"].update(ftti_ms="⟨pb: FTTI⟩", safe_state="")
    report = check_needs(needs)
    assert report.errors == []
    assert report.open == [
        "HE_OS1_M1: severity, exposure_rationale, asil",
        "SG_X_1: safe_state, ftti_ms",
    ]
    assert not report.ok


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (("HE_OS1_M1", "asil", "B"), "HE_OS1_M1: asil B does not match S3/E4/C2 (gives C)"),
        (("HE_OS1_M1", "severity", "S4"), "HE_OS1_M1: severity 'S4' is not S0..S3"),
        (("HE_OS1_M1", "exposure", "3"), "HE_OS1_M1: exposure '3' is not E0..E4"),
        (("HE_OS1_M1", "asil", "E"), "HE_OS1_M1: asil 'E' is not one of QM, A, B, C, D"),
        (("HE_OS1_M1", "situation", "OS2"), "HE_OS1_M1: situation 'OS2' does not match ID"),
        (("HE_OS1_M1", "derives_from_back", []), "HE_OS1_M1: ASIL C but no safety goal"),
        (("SG_X_1", "asil", "B"), "SG_X_1: asil B is not the highest ASIL of its hazardous"),
        (("SG_X_1", "ftti_ms", "0.5 s"), "SG_X_1: ftti_ms '0.5 s' is not a positive whole"),
        (("SG_X_1", "derives_from", []), "SG_X_1: derives from no hazardous event"),
        (("SG_X_1", "derives_from", ["FSR_X"]), "SG_X_1: derives_from FSR_X is not a hazardous"),
    ],
)
def test_inconsistencies_are_errors(change: tuple[str, str, object], message: str) -> None:
    needs = _consistent()
    nid, attr, value = change
    needs[nid][attr] = value
    report = check_needs(needs)
    assert any(e.startswith(message) for e in report.errors), report.errors
    assert not report.ok


def test_malformed_he_id_is_an_error() -> None:
    needs = _consistent()
    needs["HE_7"] = {**needs.pop("HE_OS5_M2"), "id": "HE_7"}
    assert "HE_7: ID must be HE_OS<n>_M<n>[_SUFFIX]" in check_needs(needs).errors


def test_suffixed_he_id_is_allowed() -> None:
    needs = _consistent()
    needs["HE_OS5_M2_WET"] = {**needs.pop("HE_OS5_M2"), "id": "HE_OS5_M2_WET"}
    assert check_needs(needs).ok


def test_no_hazardous_events_fails() -> None:
    report = check_needs({})
    assert report.errors == ["no hazardous events (HE_) found"]
    assert not report.ok


def test_source_scan_skips_need_options(tmp_path: Path) -> None:
    rst = tmp_path / "x.rst"
    rst.write_text(".. he:: T\n   :asil: ⟨pb: ASIL⟩\n\nProse with ⟨pb: decide⟩.\n", "utf-8")
    report = hara_check.Report()
    hara_check.check_sources([rst], report)
    assert report.open == [f"{rst}:4: Prose with ⟨pb: decide⟩."]


def _write_needs_json(path: Path, needs: dict[str, dict]) -> Path:
    path.write_text(json.dumps({"current_version": "", "versions": {"": {"needs": needs}}}))
    return path


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = _write_needs_json(tmp_path / "good.json", _consistent())
    assert hara_check.main([str(good)]) == 0
    assert "Result: PASS" in capsys.readouterr().out

    needs = _consistent()
    needs["HE_OS2_M1"]["controllability"] = "⟨pb: C⟩"
    bad = _write_needs_json(tmp_path / "bad.json", needs)
    assert hara_check.main([str(bad)]) == 1
    out = capsys.readouterr().out
    assert "Open (pb): 1\n  HE_OS2_M1: controllability\n" in out
    assert "Result: FAIL" in out
