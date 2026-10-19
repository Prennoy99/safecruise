"""tools/sysml_check.py: model against needs.json (ADR-009).

The needs and models below are fixtures, not project requirements.
"""

import json
from pathlib import Path

import pytest
from jupyter_client.kernelspec import KernelSpecManager

from tools import sysml_check, sysml_parse
from tools.sysml_check import ModelFacts, Satisfy, check

FIXTURES = Path(__file__).parent / "fixtures" / "sysml_check"


def _need(nid: str, title: str = "", **links: list[str]) -> dict:
    return {"id": nid, "type": nid.split("_")[0].lower(), "title": title, **links}


def _needs() -> dict[str, dict]:
    needs = [
        _need("ARC_X_A", "ElementA"),
        _need("ARC_X_B", "ElementB"),
        _need("SYS_X_1", allocated_to=["ARC_X_A"]),
        _need("TSR_X_1", allocated_to=["ARC_X_A", "ARC_X_B"]),
        _need("FSR_X_1", allocated_to=["ARC_X_A"]),  # FSR_ allocations are not mirrored
    ]
    return {n["id"]: n for n in needs}


def _model() -> ModelFacts:
    return ModelFacts(
        requirements={"SYS_X_1": ["P::sys1"], "TSR_X_1": ["P::tsr1"]},
        parts={"ARC_X_A": ["ElementA"], "ARC_X_B": ["ElementB"]},
        satisfies=[
            Satisfy("SYS_X_1", "P::sys1", "ARC_X_A", "P::s.a"),
            Satisfy("TSR_X_1", "P::tsr1", "ARC_X_A", "P::s.a"),
            Satisfy("TSR_X_1", "P::tsr1", "ARC_X_B", "P::s.b"),
        ],
        text_ids={"SYS_X_1": ["M.sysml:3"]},
    )


def test_consistent_model_passes() -> None:
    assert check(_model(), _needs()) == []


def test_unknown_requirement_id_fails() -> None:
    model = _model()
    model.requirements["SYS_X_9"] = ["P::sys9"]
    assert check(model, _needs()) == ["SYS_X_9: requirement P::sys9 does not exist in needs.json"]


def test_requirement_id_of_wrong_type_fails() -> None:
    model = _model()
    model.requirements["ARC_X_B"] = ["P::notARequirement"]
    errors = check(model, _needs())
    assert "ARC_X_B: requirement P::notARequirement is a ARC in needs.json" in errors


def test_unknown_id_in_text_fails() -> None:
    model = _model()
    model.text_ids["AOU_X_7"] = ["M.sysml:9"]
    assert check(model, _needs()) == ["AOU_X_7: written in M.sysml:9, does not exist in needs.json"]


def test_duplicate_short_name_fails() -> None:
    model = _model()
    model.requirements["SYS_X_1"].append("P::again")
    errors = check(model, _needs())
    assert any(e.startswith("SYS_X_1: short name of 2 model elements") for e in errors)


def test_arc_need_without_part_def_fails() -> None:
    model = _model()
    del model.parts["ARC_X_B"]
    model.satisfies = [s for s in model.satisfies if s.arc != "ARC_X_B"]
    needs = _needs()
    needs["TSR_X_1"]["allocated_to"] = ["ARC_X_A"]
    assert check(model, needs) == ["ARC_X_B: no part def with this short name in the model"]


def test_part_def_name_must_match_need_title() -> None:
    model = _model()
    model.parts["ARC_X_B"] = ["Renamed"]
    assert check(model, _needs()) == ["ARC_X_B: part def is named Renamed, need title is ElementB"]


def test_satisfy_by_part_without_arc_id_fails() -> None:
    model = _model()
    model.satisfies.append(Satisfy("SYS_X_1", "P::sys1", None, "P::s.helper"))
    assert check(model, _needs()) == ["satisfy P::sys1 by P::s.helper: part has no ARC_ ID"]


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (
            "drop_satisfy",
            "TSR_X_1: allocated to ARC_X_B in needs.json, not satisfied in the model",
        ),
        (
            "extra_satisfy",
            "SYS_X_1: satisfied by ARC_X_B in the model, not allocated in needs.json",
        ),
    ],
)
def test_allocation_must_match_in_both_directions(change: str, expected: str) -> None:
    model = _model()
    if change == "drop_satisfy":
        model.satisfies = model.satisfies[:2]
    else:
        model.satisfies.append(Satisfy("SYS_X_1", "P::sys1", "ARC_X_B", "P::s.b"))
    assert check(model, _needs()) == [expected]


# --- With the Pilot kernel: the facts come from the parsed model --------------------------

needs_kernel = pytest.mark.skipif(
    sysml_parse.KERNEL_NAME not in KernelSpecManager().find_kernel_specs(),
    reason="needs the SysML v2 kernel from the toolchain image",
)


def _needs_json(tmp_path: Path) -> Path:
    path = tmp_path / "needs.json"
    path.write_text(json.dumps({"current_version": "", "versions": {"": {"needs": _needs()}}}))
    return path


@needs_kernel
def test_valid_fixture_model_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = sysml_check.main([str(_needs_json(tmp_path)), str(FIXTURES / "Valid.sysml")])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "2 requirement IDs, 2 ARC_ part defs, 3 satisfy relations" in out


@needs_kernel
def test_broken_id_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = sysml_check.main([str(_needs_json(tmp_path)), str(FIXTURES / "BrokenId.sysml")])
    out = capsys.readouterr().out
    assert rc == 1
    assert "SYS_X_9: requirement CheckFixture::systemRequirement does not exist" in out
    assert "SYS_X_1: allocated to ARC_X_A in needs.json, not satisfied in the model" in out
