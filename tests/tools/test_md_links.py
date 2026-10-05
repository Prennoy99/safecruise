"""Every relative link in the repository's Markdown files points to an existing path."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", "build", ".venv", "node_modules"}
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def _markdown_files() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*.md") if not SKIP_DIRS.intersection(p.relative_to(ROOT).parts)
    )


def _relative_targets(md: Path) -> list[str]:
    text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.DOTALL)
    return [
        t for t in LINK.findall(text) if not re.match(r"^[a-z][a-z0-9+.-]*:|^#", t, re.IGNORECASE)
    ]


@pytest.mark.parametrize("md", _markdown_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_markdown_links_resolve(md: Path) -> None:
    missing = [
        t for t in _relative_targets(md) if not (md.parent / t.split("#", 1)[0]).resolve().exists()
    ]
    assert not missing, f"{md.relative_to(ROOT)}: broken links {missing}"
