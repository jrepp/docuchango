"""Regression tests for user-facing command references in documentation."""

from pathlib import Path

import pytest

from docuchango.schemas import VALID_ADR_STATUSES, VALID_RFC_STATUSES

REPO_ROOT = Path(__file__).resolve().parents[1]

USER_FACING_DOCS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "AGENT_GUIDE.md",
    REPO_ROOT / "docs" / "BOOTSTRAP_GUIDE.md",
    REPO_ROOT / "docs" / "BEST_PRACTICES.md",
    REPO_ROOT / "docs" / "CONFIGURATION.md",
    REPO_ROOT / "docs" / "VALIDATION_REFERENCE.md",
    REPO_ROOT / "templates" / "README.md",
    REPO_ROOT / "docuchango" / "templates" / "README.md",
    REPO_ROOT / "docs-cms" / "prd" / "prd-001-validation-framework.md",
]

STALE_COMMAND_REFERENCES = [
    "docuchango fix",
    "dcc-fix",
    "docuchango validate --fix",
    "docuchango validate --check-links",
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
    quick_start = readme.split("## Two-minute start", maxsplit=1)[1].split("## What a document looks like", maxsplit=1)[
        0
    ]

    assert "docuchango init" in quick_start
    assert "docuchango bootstrap" not in quick_start


STATUS_LIST_REFERENCES = [
    # (path, line prefix identifying the enumeration, valid status list)
    (REPO_ROOT / "templates" / "adr-template.md", "status: Proposed  # Valid values: ", VALID_ADR_STATUSES),
    (
        REPO_ROOT / "templates" / "adr-amendment-template.md",
        "status: Proposed  # Valid values: ",
        VALID_ADR_STATUSES,
    ),
    (REPO_ROOT / "templates" / "rfc-template.md", "status: Draft  # Valid values: ", VALID_RFC_STATUSES),
]


@pytest.mark.parametrize("doc_path,prefix,valid_statuses", STATUS_LIST_REFERENCES)
def test_template_status_comments_match_schema(doc_path: Path, prefix: str, valid_statuses: list[str]):
    """Shipped templates must enumerate exactly the statuses the schema accepts."""
    for line in doc_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            listed = [value.strip() for value in line[len(prefix) :].split(",")]
            assert listed == valid_statuses
            return

    pytest.fail(f"No status enumeration found in {doc_path}")


@pytest.mark.parametrize(
    "doc_path",
    [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs" / "AGENT_GUIDE.md",
        REPO_ROOT / "docs" / "BOOTSTRAP_GUIDE.md",
        REPO_ROOT / "docs" / "BEST_PRACTICES.md",
    ],
)
def test_user_facing_docs_do_not_use_retired_adr_rfc_statuses(doc_path: Path):
    """'In Review' and 'Approved' are PRD statuses; they are not valid for ADRs or RFCs."""
    for line in doc_path.read_text(encoding="utf-8").splitlines():
        if "PRD" in line or "prd" in line:
            continue
        for retired in ("In Review", "Approved"):
            assert retired not in line, f"{doc_path}: {line}"
