"""Spike 1 (ADR-001): the SysML v2 Pilot kernel parses valid models and rejects broken ones."""

from pathlib import Path

import pytest
from jupyter_client.kernelspec import KernelSpecManager

from tools import sysml_parse

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.skipif(
    sysml_parse.KERNEL_NAME not in KernelSpecManager().find_kernel_specs(),
    reason="needs the SysML v2 kernel from the toolchain image",
)


def test_toy_model_parses(capsys: pytest.CaptureFixture[str]) -> None:
    assert sysml_parse.main([str(ROOT / "model/sysml/spike/Toy.sysml")]) == 0
    assert "Package SpikeToy" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        ("broken_syntax.sysml", "mismatched input"),
        ("broken_reference.sysml", "Couldn't resolve reference to Type 'NoSuchType'"),
    ],
)
def test_broken_model_fails(fixture: str, message: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert sysml_parse.main([str(FIXTURES / fixture)]) == 1
    assert message in capsys.readouterr().out
