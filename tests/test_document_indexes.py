"""Tests for configured document index validation."""

import tempfile
from pathlib import Path

import yaml

from docuchango.validator import DocValidator


def write_config(repo_root: Path, config_data: dict) -> None:
    with (repo_root / "docs-project.yaml").open("w") as f:
        yaml.dump(config_data, f)


def test_document_index_requires_all_targets():
    """Configured indexes must link every matching target by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        docs = repo_root / "docs"
        decisions = docs / "decisions"
        decisions.mkdir(parents=True)

        (decisions / "decision-a.md").write_text("# Decision A\n")
        (decisions / "decision-b.md").write_text("# Decision B\n")
        (docs / "design-index.md").write_text(
            """# Design Index

- [Decision A](./decisions/decision-a.md)
"""
        )

        write_config(
            repo_root,
            {
                "project": {"id": "index-project", "name": "Index Project"},
                "indexes": [
                    {
                        "name": "Shared Design Index",
                        "path": "docs/design-index.md",
                        "targets": ["docs/decisions/*.md"],
                    }
                ],
            },
        )

        validator = DocValidator(repo_root, verbose=False)
        validator.check_document_indexes()

        assert (
            "Document index 'Shared Design Index' is missing target: docs/decisions/decision-b.md" in validator.errors
        )


def test_weekly_document_index_requires_bucket_headings_and_placement():
    """Weekly indexes require each target link under its ISO week bucket."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        docs = repo_root / "docs"
        notes = docs / "release-notes"
        notes.mkdir(parents=True)

        (notes / "release-2026-05-18.md").write_text(
            """---
title: Release 2026-05-18
created: 2026-05-18
project_id: index-project
doc_uuid: 11111111-1111-4111-8111-111111111111
---

# Release
"""
        )
        (notes / "release-2026-05-25.md").write_text(
            """---
title: Release 2026-05-25
created: 2026-05-25
project_id: index-project
doc_uuid: 22222222-2222-4222-8222-222222222222
---

# Release
"""
        )
        (docs / "release-index.md").write_text(
            """# Release Index

## 2026-W21

- [Release 2026-05-18](./release-notes/release-2026-05-18.md)
- [Release 2026-05-25](./release-notes/release-2026-05-25.md)

## 2026-W22
"""
        )

        write_config(
            repo_root,
            {
                "project": {"id": "index-project", "name": "Index Project"},
                "indexes": [
                    {
                        "name": "Weekly Release Notes",
                        "path": "docs/release-index.md",
                        "targets": ["docs/release-notes/*.md"],
                        "time_bucket": {
                            "cadence": "weekly",
                            "field": "created",
                            "heading_pattern": r"^\d{4}-W\d{2}$",
                        },
                    }
                ],
            },
        )

        validator = DocValidator(repo_root, verbose=False)
        validator.check_document_indexes()

        assert (
            "Document index 'Weekly Release Notes' links docs/release-notes/release-2026-05-25.md "
            "under '2026-W21' instead of '2026-W22'"
        ) in validator.errors


def test_milestone_document_index_uses_configured_frontmatter_field():
    """Milestone indexes can bucket targets by a configured frontmatter field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        docs = repo_root / "docs"
        plans = docs / "plans"
        plans.mkdir(parents=True)

        (plans / "checkout-plan.md").write_text(
            """---
title: Checkout Plan
milestone: M2
project_id: index-project
doc_uuid: 11111111-1111-4111-8111-111111111111
---

# Checkout Plan
"""
        )
        (docs / "plan-index.md").write_text(
            """# Plan Index

## M1

- [Checkout Plan](./plans/checkout-plan.md)
"""
        )

        write_config(
            repo_root,
            {
                "project": {"id": "index-project", "name": "Index Project"},
                "indexes": [
                    {
                        "name": "Plan Index",
                        "path": "docs/plan-index.md",
                        "targets": ["docs/plans/*.md"],
                        "time_bucket": {"cadence": "milestone", "milestone_field": "milestone"},
                    }
                ],
            },
        )

        validator = DocValidator(repo_root, verbose=False)
        validator.check_document_indexes()

        assert "Document index 'Plan Index' missing bucket heading: M2" in validator.errors
