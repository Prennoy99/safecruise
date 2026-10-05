#!/bin/sh
# Prints the toolchain versions of the current environment (CI evidence, ADR-000 D-20).
set -eu
echo '```'
gcc-14 --version | head -1
cmake --version | head -1
ninja --version | sed 's/^/ninja /'
cppcheck --version
clang-format --version
python --version
java -version 2>&1 | head -1
echo "jupyter-sysml-kernel ${SYSML_KERNEL_VERSION:-unknown}"
python - <<'PY'
from importlib.metadata import version
for pkg in ("sphinx", "sphinx-needs", "sphinx-test-reports", "pytest", "ruff", "cantools",
            "python-can", "numpy", "lizard", "gcovr"):
    print(f"{pkg} {version(pkg)}")
PY
echo '```'
