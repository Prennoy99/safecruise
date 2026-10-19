"""Parse SysML v2 textual models headlessly with the SysML v2 Pilot Implementation kernel.

Spike 1 (M0, ADR-001). Starts the Pilot Jupyter kernel through jupyter_client, sends each
file as one cell and fails if the kernel reports an error. No notebook server is needed.
``KernelSession`` is reused by tools/sysml_check.py (M3, ADR-009).

Usage: python tools/sysml_parse.py FILE.sysml [FILE.sysml ...]
Exit code 0 if every file parses and resolves, 1 otherwise. Each file is sent in its own
cell; files are not isolated from each other, so later files can see earlier packages.
"""

from __future__ import annotations

import argparse
import queue
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from jupyter_client.manager import start_new_kernel

KERNEL_NAME = "sysml"
TIMEOUT_S = 180.0


@dataclass
class CellResult:
    ok: bool
    text: list[str] = field(default_factory=list)
    data: dict[str, str] = field(default_factory=dict)  # MIME type -> content of the result


class KernelSession:
    """One Pilot kernel; cells sent to it share one namespace (ADR-001)."""

    def __init__(self, verbose: bool = False) -> None:
        quiet = {} if verbose else {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        self._manager, self._client = start_new_kernel(
            kernel_name=KERNEL_NAME, startup_timeout=TIMEOUT_S, **quiet
        )

    def __enter__(self) -> KernelSession:
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.stop_channels()
        self._manager.shutdown_kernel(now=True)

    def run(self, code: str) -> CellResult:
        client = self._client
        msg_id = client.execute(code, store_history=False)
        result = CellResult(ok=True)
        while True:
            try:
                msg = client.get_iopub_msg(timeout=TIMEOUT_S)
            except queue.Empty as exc:
                raise TimeoutError(f"no kernel output within {TIMEOUT_S:.0f} s") from exc
            if msg["parent_header"].get("msg_id") != msg_id:
                continue
            kind, content = msg["msg_type"], msg["content"]
            if kind == "stream":
                result.text.append(content["text"])
                if content.get("name") == "stderr":
                    result.ok = False
            elif kind == "error":
                result.ok = False
                result.text.append(f"{content['ename']}: {content['evalue']}")
            elif kind in ("execute_result", "display_data"):
                result.data.update(content["data"])
                result.text.append(content["data"].get("text/plain", ""))
            elif kind == "status" and content["execution_state"] == "idle":
                break
        while True:  # skip replies to earlier requests (e.g. kernel_info at startup)
            reply = client.get_shell_msg(timeout=TIMEOUT_S)
            if reply["parent_header"].get("msg_id") == msg_id:
                break
        if reply["content"].get("status") != "ok":
            result.ok = False
        return result


def print_result(path: Path, res: CellResult) -> None:
    print(f"[{'OK  ' if res.ok else 'FAIL'}] {path}")
    for line in "".join(res.text).splitlines():
        print(f"       {line}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true", help="show the kernel's own log")
    args = parser.parse_args(argv)

    failures = 0
    with KernelSession(verbose=args.verbose) as kernel:
        for path in args.files:
            res = kernel.run(path.read_text(encoding="utf-8"))
            print_result(path, res)
            failures += not res.ok
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
