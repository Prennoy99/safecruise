"""The CMake build refuses value-changing float flags (ADR-000 D-12)."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gcc-14") is None,
    reason="needs the toolchain image (cmake, gcc-14)",
)


@pytest.mark.parametrize("flag", ["-ffast-math", "-Ofast", "-funsafe-math-optimizations"])
def test_forbidden_float_flag_fails_configure(tmp_path: Path, flag: str) -> None:
    result = subprocess.run(
        [
            "cmake", "-S", str(ROOT), "-B", str(tmp_path), "-G", "Ninja",
            "-DCMAKE_C_COMPILER=gcc-14", "-DSAFECRUISE_BUILD_TESTS=OFF",
            f"-DCMAKE_C_FLAGS={flag}",
        ],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert result.returncode != 0
    assert "ADR-000 D-12" in result.stderr


def test_clean_flags_configure(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "cmake", "-S", str(ROOT), "-B", str(tmp_path), "-G", "Ninja",
            "-DCMAKE_C_COMPILER=gcc-14", "-DSAFECRUISE_BUILD_TESTS=OFF",
        ],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert result.returncode == 0, result.stderr
