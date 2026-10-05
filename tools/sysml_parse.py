"""Parse SysML v2 textual models headlessly with the SysML v2 Pilot Implementation kernel.

Spike 1 (M0, ADR-001). Starts the Pilot Jupyter kernel through jupyter_client, sends each
file as one cell and fails if the kernel reports an error. No notebook server is needed.

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


def _run_cell(client, code: str) -> CellResult:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true", help="show the kernel's own log")
    args = parser.parse_args(argv)

    quiet = {} if args.verbose else {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    manager, client = start_new_kernel(kernel_name=KERNEL_NAME, startup_timeout=TIMEOUT_S, **quiet)
    failures = 0
    try:
        for path in args.files:
            res = _run_cell(client, path.read_text(encoding="utf-8"))
            status = "OK  " if res.ok else "FAIL"
            print(f"[{status}] {path}")
            for line in "".join(res.text).splitlines():
                print(f"       {line}")
            failures += not res.ok
    finally:
        client.stop_channels()
        manager.shutdown_kernel(now=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
