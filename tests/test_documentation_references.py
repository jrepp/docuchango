"""Regression tests for user-facing command references in documentation."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

USER_FACING_DOCS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "AGENT_GUIDE.md",
    REPO_ROOT / "docs" / "BOOTSTRAP_GUIDE.md",
    REPO_ROOT / "docs" / "BEST_PRACTICES.md",
    REPO_ROOT / "templates" / "README.md",
    REPO_ROOT / "docuchango" / "templates" / "README.md",
]

STALE_COMMAND_REFERENCES = [
    "docuchango fix",
    "dcc-fix",
    "docuchango validate --fix",
]


@pytest.mark.parametrize("doc_path", USER_FACING_DOCS)
def test_user_facing_docs_do_not_reference_removed_fix_commands(doc_path: Path):
    """User-facing docs should match the current CLI surface."""
    content = doc_path.read_text(encoding="utf-8")

    for stale_reference in STALE_COMMAND_REFERENCES:
        assert stale_reference not in content


def test_readme_quick_start_uses_init_not_bootstrap():
    """The README quick start should point users at the init command."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    quick_start = readme.split("## Quick Start", maxsplit=1)[1].split("## Usage Examples", maxsplit=1)[0]

    assert "docuchango init" in quick_start
    assert "docuchango bootstrap" not in quick_start
