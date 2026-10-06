"""tools/ears_lint.py: EARS form, wording, values, attributes and IDs (ADR-005).

The requirements below are fixtures, not project requirements.
"""

import json
from pathlib import Path

import pytest

from tools import ears_lint
from tools.ears_lint import lint, numbers_without_unit, statement


def _req(nid: str, text: str, **attrs: str) -> dict:
    need = {
        "id": nid,
        "type": nid.split("_")[0].lower(),
        "content": text,
        "asil": "B",
        "verification_method": "test",
    }
    need.update(attrs)
    return need


@pytest.mark.parametrize(
    "text",
    [
        "The ACC system shall limit the acceleration request to +2.0 m/s².",
        "While ACC is in ACTIVE_SPEED, the ACC system shall hold ego speed within ±2 km/h of "
        "the set speed.",
        "When the driver presses the brake pedal, the ACC system shall change to STANDBY "
        "within 100 ms.",
        "If an input message fails its end-to-end check for 3 consecutive cycles, then the "
        "ACC system shall enter the safe state within 500 ms.",
        "Where the radar reports a stationary object, the ACC system shall ignore it.",
        "While ACC is active, when the speed falls below 25 km/h, the ACC system shall raise "
        "a takeover request.",
        "The ACC system shall offer time gaps of 1.0, 1.5 or 2.0 s.",
        "The AccMon element shall ramp the request from \u22123.5 to 0 m/s² at 2.5 m/s³.",
        "The E2E element shall use a 4-bit alive counter.",
        "The ACC system shall keep the request within A-04 and A-05 (SG_ACC_001).",
    ],
)
def test_valid_requirements_pass(text: str) -> None:
    assert lint({"SYS_X_1": _req("SYS_X_1", text)}) == {}


@pytest.mark.parametrize(
    ("text", "finding"),
    [
        ("The ACC system brakes when needed.", '0 times "shall", expected exactly 1'),
        ("The ACC shall brake and it shall warn.", '2 times "shall", expected exactly 1'),
        ("Brake when needed, the ACC system shall.", "matches no EARS template"),
        ("If the radar fails, the ACC system shall stop.", "matches no EARS template"),
        ("When the radar fails, then the ACC shall stop.", "matches no EARS template"),
        ("The ACC system shall react fast.", 'vague word "fast"'),
        ("The ACC system shall warn and/or brake.", 'vague word "and/or"'),
        ("The ACC system shall react within 100.", "number 100 without unit"),
        ("The ACC system shall ramp the request to 0.", "number 0 without unit"),
        ("", "no requirement statement"),
    ],
)
def test_bad_statements_are_found(text: str, finding: str) -> None:
    assert finding in lint({"SYS_X_1": _req("SYS_X_1", text)})["SYS_X_1"]


def test_only_the_first_paragraph_is_the_statement() -> None:
    text = "The ACC system shall stop.\n\nRationale: this is fast, see ``A-11`` and 3 more."
    assert lint({"SYS_X_1": _req("SYS_X_1", text)}) == {}


def test_inline_markup_is_removed() -> None:
    text = "If :need:`SG_ACC_001` is violated, then the **ACC system** shall ``stop``."
    assert statement(text) == "If SG_ACC_001 is violated, then the ACC system shall stop."


@pytest.mark.parametrize(
    ("text", "missing"),
    [
        ("speeds of 30 to 150 km/h", []),
        ("gaps of 1.0 / 1.5 / 2.0 s", []),
        ("gaps of 1.0, 1.5 and 2.0", ["1.0", "1.5", "2.0"]),
        ("ID SG_ACC_001, A-04, E2E, CRC-8, J1850, 0x1D", []),
        ("3 consecutive cycles and 2 frames", []),
        ("after 3 consecutive", ["3"]),
    ],
)
def test_numbers_without_unit(text: str, missing: list[str]) -> None:
    assert numbers_without_unit(text) == missing


@pytest.mark.parametrize(
    ("attrs", "finding"),
    [
        ({"asil": ""}, "asil '' is not QM, A-D or decomposed like B(D)"),
        ({"asil": "E"}, "asil 'E' is not QM, A-D or decomposed like B(D)"),
        ({"verification_method": "demo"}, "verification_method 'demo' is not one of"),
    ],
)
def test_attributes(attrs: dict, finding: str) -> None:
    findings = lint({"FSR_X_1": _req("FSR_X_1", "The ACC system shall stop.", **attrs)})
    assert any(f.startswith(finding) for f in findings["FSR_X_1"])


@pytest.mark.parametrize("asil", ["QM", "A", "D", "B(D)", "QM(B)"])
def test_valid_asils(asil: str) -> None:
    assert lint({"TSR_X_1": _req("TSR_X_1", "The ACC system shall stop.", asil=asil)}) == {}


def test_aou_needs_no_verification_method() -> None:
    aou = _req("AOU_X_1", "The radar shall report moving objects only.", verification_method="")
    assert lint({"AOU_X_1": aou}) == {}


def test_id_prefix_must_match_directive() -> None:
    need = {**_req("TC_X_1", "The ACC system shall stop."), "type": "sys"}
    assert "ID does not start with SYS_ for a 'sys' need" in lint({"TC_X_1": need})["TC_X_1"]


def test_placeholders_fail_in_any_need() -> None:
    needs = {
        "SYS_X_1": _req("SYS_X_1", "The ACC system shall stop within ⟨pb: T⟩."),
        "SG_X_1": {"id": "SG_X_1", "type": "sg", "content": "", "ftti_ms": "⟨pb: FTTI⟩"},
    }
    report = lint(needs)
    assert "placeholder in content" in report["SYS_X_1"]
    assert report["SG_X_1"] == ["placeholder in ftti_ms"]


def test_non_requirements_are_not_ears_linted() -> None:
    stk = {"id": "STK_X_1", "type": "stk", "content": "Drivers want less effort."}
    assert lint({"STK_X_1": stk}) == {}


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def write(needs: dict) -> str:
        path = tmp_path / "needs.json"
        path.write_text(json.dumps({"current_version": "", "versions": {"": {"needs": needs}}}))
        return str(path)

    good = {"SYS_X_1": _req("SYS_X_1", "The ACC system shall stop.")}
    assert ears_lint.main([write(good)]) == 0
    assert "Result: PASS" in capsys.readouterr().out

    bad = {"SYS_X_1": _req("SYS_X_1", "The ACC system shall stop fast.")}
    assert ears_lint.main([write(bad)]) == 1
    assert '  SYS_X_1: vague word "fast"\n' in capsys.readouterr().out
