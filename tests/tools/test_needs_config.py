"""Checks the sphinx-needs configuration in docs/conf.py (brief §6.1, ADR-000, ADR-004).

Builds a throw-away Sphinx project that uses the real conf.py and one need of every type,
then reads back needs.json. The example needs are fixtures, not project requirements.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[2] / "docs"

FIXTURE_RST = """
Fixture
=======

.. he:: Fixture hazardous event
   :id: HE_FIX_1
   :status: draft
   :situation: OS1
   :malfunction: M1
   :severity: ⟨pb⟩
   :severity_rationale: ⟨pb⟩
   :exposure: ⟨pb⟩
   :exposure_rationale: ⟨pb⟩
   :controllability: ⟨pb⟩
   :controllability_rationale: ⟨pb⟩
   :asil: ⟨pb⟩

.. sg:: Fixture safety goal
   :id: SG_FIX_1
   :status: draft
   :derives_from: HE_FIX_1
   :asil: ⟨pb⟩
   :safe_state: ⟨pb⟩
   :ftti_ms: ⟨pb⟩

.. stk:: Fixture stakeholder need
   :id: STK_FIX_1
   :status: draft

.. sys:: Fixture system requirement
   :id: SYS_FIX_1
   :status: draft
   :satisfies: STK_FIX_1

.. fsr:: Fixture functional safety requirement
   :id: FSR_FIX_1
   :status: draft
   :derives_from: SG_FIX_1

.. arc:: Fixture element
   :id: ARC_FIX_1
   :status: draft

.. tsr:: Fixture technical safety requirement
   :id: TSR_FIX_1
   :status: draft
   :derives_from: FSR_FIX_1
   :allocated_to: ARC_FIX_1

.. aou:: Fixture assumption of use
   :id: AOU_FIX_1
   :status: draft

.. swr:: Fixture software requirement
   :id: SWR_FIX_1
   :status: draft
   :derives_from: TSR_FIX_1
   :allocated_to: ARC_FIX_1

.. tc:: Fixture test case
   :id: TC_FIX_1
   :status: draft
   :verifies: SYS_FIX_1, SWR_FIX_1
   :level: mil, sil
   :method: scenario
"""


def _build(srcdir: Path, outdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "needs", "-W", "-q", str(srcdir), str(outdir)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def srcdir(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    shutil.copy(DOCS / "conf.py", src / "conf.py")
    return src


def test_every_need_type_and_link_type_exports_to_needs_json(srcdir: Path, tmp_path: Path) -> None:
    (srcdir / "index.rst").write_text(FIXTURE_RST, encoding="utf-8")
    result = _build(srcdir, tmp_path / "out")
    assert result.returncode == 0, result.stderr

    data = json.loads((tmp_path / "out" / "needs.json").read_text(encoding="utf-8"))
    needs = data["versions"][data["current_version"]]["needs"]

    expected_types = {"STK", "HE", "SG", "SYS", "FSR", "TSR", "AOU", "SWR", "ARC", "TC"}
    assert {nid.split("_")[0] for nid in needs} == expected_types
    assert {n["type"] for n in needs.values()} == {t.lower() for t in expected_types}

    assert needs["SG_FIX_1"]["safe_state"] == "⟨pb⟩"
    assert needs["HE_FIX_1"]["controllability_rationale"] == "⟨pb⟩"
    assert needs["HE_FIX_1"]["derives_from_back"] == ["SG_FIX_1"]
    assert needs["TC_FIX_1"]["verifies"] == ["SYS_FIX_1", "SWR_FIX_1"]
    assert needs["TC_FIX_1"]["level"] == "mil, sil"
    assert needs["TSR_FIX_1"]["allocated_to"] == ["ARC_FIX_1"]
    assert needs["STK_FIX_1"]["satisfies_back"] == ["SYS_FIX_1"]
    assert needs["SWR_FIX_1"]["verifies_back"] == ["TC_FIX_1"]
    assert needs["FSR_FIX_1"]["derives_from_back"] == ["TSR_FIX_1"]


@pytest.mark.parametrize(
    ("directive", "reason"),
    [
        (".. sys:: Bad id\n   :id: REQ_1\n   :status: draft\n", "does not match configured regex"),
        (".. sys:: Bad status\n   :id: SYS_X_1\n   :status: done\n", "not in 'needs_statuses'"),
        (".. sys:: No id\n   :status: draft\n", "No ID defined"),
        (
            ".. tc:: Dangling link\n   :id: TC_X_1\n   :status: draft\n   :verifies: SYS_MISSING\n",
            "unknown outgoing link 'SYS_MISSING'",
        ),
    ],
)
def test_malformed_needs_fail_the_build(
    srcdir: Path, tmp_path: Path, directive: str, reason: str
) -> None:
    (srcdir / "index.rst").write_text(f"Fixture\n=======\n\n{directive}", encoding="utf-8")
    result = _build(srcdir, tmp_path / "out")
    assert result.returncode != 0
    assert reason in result.stderr
