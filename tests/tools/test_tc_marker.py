"""Checks the @pytest.mark.tc hook in conftest.py (ADR-000 D-18)."""

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT_CONFTEST = Path(__file__).resolve().parents[2] / "conftest.py"


@pytest.fixture
def project(pytester: pytest.Pytester) -> pytest.Pytester:
    shutil.copy(ROOT_CONFTEST, pytester.path / "conftest.py")
    pytester.makeini("[pytest]\njunit_family = xunit1\naddopts = --strict-markers\n")
    return pytester


def _tc_properties(junit: Path) -> dict[str, list[str]]:
    cases = ET.parse(junit).getroot().iter("testcase")
    return {
        case.get("name"): [p.get("value") for p in case.iter("property") if p.get("name") == "tc"]
        for case in cases
    }


def test_tc_ids_are_written_as_junit_properties(project: pytest.Pytester) -> None:
    project.makepyfile(
        test_sample="""
        import pytest

        @pytest.mark.tc("TC_SYS_021")
        def test_one():
            pass

        @pytest.mark.tc("TC_SYS_010", "TC_FSR_003")
        def test_two():
            pass

        def test_unlinked():
            pass
        """
    )
    junit = project.path / "junit.xml"
    result = project.runpytest(f"--junitxml={junit}")
    result.assert_outcomes(passed=3)
    assert _tc_properties(junit) == {
        "test_one": ["TC_SYS_021"],
        "test_two": ["TC_SYS_010", "TC_FSR_003"],
        "test_unlinked": [],
    }


@pytest.mark.parametrize("marker", ['tc("SYS_021")', 'tc("TC_sys_021")', "tc()", "tc(21)"])
def test_malformed_tc_marker_is_a_usage_error(project: pytest.Pytester, marker: str) -> None:
    project.makepyfile(
        test_bad=f"""
        import pytest

        @pytest.mark.{marker}
        def test_bad():
            pass
        """
    )
    result = project.runpytest()
    assert result.ret == pytest.ExitCode.USAGE_ERROR
