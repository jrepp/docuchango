"""Integration tests for the fixing pass of the `validate` command.

There is one fixing path: the Phase 1 fixers the `validate` command runs
before it builds a reporting-only `DocValidator`. These tests drive that path
through the real Click command, so a fix can never be exercised through an
entry point the CLI does not use.
"""

from pathlib import Path

import frontmatter
import pytest
from click.testing import CliRunner

from docuchango.cli import validate
from docuchango.validator import DocValidator

BROKEN_DOC = (
    "---\n"
    "title: Test Decision Record\n"
    "status: Proposed\n"
    "created: 2024-10-13\n"
    "deciders: Team\n"
    'tags: ["test"]\n'
    'id: "adr-001"\n'
    'doc_uuid: "12345678-1234-4123-8123-123456789abc"\n'
    "---\n"
    "Some text with trailing spaces   \n"  # Actual trailing spaces
    "```\n"
    "code without language\n"
    "```\n"
    "Another line\n"
    "```python\n"
    "more code\n"
    "```python\n"
)


def _project_config(doc_types: str = "") -> str:
    """A docs-project.yaml for a tmp_path tree, optionally with doc_types."""
    structure = doc_types or (
        "  adr_dir: adr\n  rfc_dir: rfcs\n  memo_dir: memos\n  document_folders:\n    - adr\n    - rfcs\n    - memos\n"
    )
    return (
        'version: "1"\n'
        "project:\n"
        "  id: fixture-project\n"
        "  name: Fixture Project\n"
        "  description: Synthetic project used by the fix integration tests\n"
        "structure:\n" + structure + "security:\n"
        "  allow_external_paths: false\n"
        "readability:\n"
        "  enabled: false\n"
    )


class TestValidateFixIntegration:
    """The fixing pass of `docuchango validate`."""

    @pytest.fixture
    def broken_doc(self, tmp_path):
        """Create a document with fixable formatting and code block issues."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test-decision.md"
        doc_file.write_text(BROKEN_DOC, encoding="utf-8")
        return docs_root, doc_file

    def test_dry_run_detects_errors_without_writing(self, broken_doc):
        """--dry-run reports the issues and leaves the file byte-identical."""
        docs_root, doc_file = broken_doc
        before = doc_file.read_bytes()

        result = CliRunner().invoke(validate, ["--repo-root", str(docs_root), "--skip-build", "--dry-run"])

        assert result.exit_code == 1
        output = result.output.lower()
        assert "trailing whitespace" in output
        assert "fence" in output or "code block" in output
        assert doc_file.read_bytes() == before

    def test_validate_applies_fixes(self, broken_doc):
        """A fixing run repairs the formatting and code block issues."""
        docs_root, doc_file = broken_doc

        result = CliRunner().invoke(validate, ["--repo-root", str(docs_root), "--skip-build"])

        fixed_content = doc_file.read_text(encoding="utf-8")
        assert result.exit_code == 0, result.output
        assert "   \n" not in fixed_content, "Trailing whitespace should be removed"
        assert "```text\n" in fixed_content, "Missing language should be added"

        lines = fixed_content.split("\n")
        closing_fences = [i for i, line in enumerate(lines) if line.strip() == "```" and i > 0]
        assert len(closing_fences) >= 1, "Should have at least one proper closing fence"
        assert "\n\n```" in fixed_content, "Blank lines should be added before fences"

    def test_validate_leaves_no_fixable_findings(self, broken_doc):
        """Re-validating the fixed tree reports none of the repaired findings."""
        docs_root, _doc_file = broken_doc

        CliRunner().invoke(validate, ["--repo-root", str(docs_root), "--skip-build"])

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        all_errors = list(validator.errors)
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        fixable_errors = [
            e
            for e in all_errors
            if any(keyword in e.lower() for keyword in ["trailing whitespace", "code fence", "blank line", "fence"])
        ]

        assert fixable_errors == [], f"Should have no fixable errors after fix: {fixable_errors}"

    def test_multiple_documents_are_fixed(self, tmp_path):
        """The fixing pass covers every discovered document."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        for i in range(1, 4):
            doc_file = doc_dir / f"adr-{i:03d}-test-decision.md"
            doc_file.write_text(
                f"""---
title: Test Decision {i} Record
status: Proposed
created: 2024-10-13
deciders: Team
tags: ["test"]
id: "adr-{i:03d}"
doc_uuid: "12345678-1234-4123-8123-12345678{i:03d}c"
---

Text with issues

```
code
```
""",
                encoding="utf-8",
            )

        result = CliRunner().invoke(validate, ["--repo-root", str(docs_root), "--skip-build"])

        assert result.exit_code == 0, result.output
        for i in range(1, 4):
            content = (doc_dir / f"adr-{i:03d}-test-decision.md").read_text(encoding="utf-8")
            assert "```text\n" in content, f"Document {i} should have language on code fence"

    def test_fixes_are_idempotent(self, broken_doc):
        """Running the fixing pass twice is a no-op the second time."""
        docs_root, doc_file = broken_doc
        runner = CliRunner()

        runner.invoke(validate, ["--repo-root", str(docs_root), "--skip-build"])
        content_after_first = doc_file.read_text(encoding="utf-8")

        result = runner.invoke(validate, ["--repo-root", str(docs_root), "--skip-build"])
        content_after_second = doc_file.read_text(encoding="utf-8")

        assert result.exit_code == 0, result.output
        assert content_after_first == content_after_second, "Fixes should be idempotent"


class TestValidateDocTypeFromConfig:
    """The frontmatter fixer shapes the block by the configured schema.

    Regression test for the fixer inferring the document type from the folder
    name even when docs-project.yaml bound that folder to another schema.
    """

    @staticmethod
    def _write_tree(root: Path, structure: str, folder: str, filename: str) -> Path:
        docs_cms = root / "docs-cms"
        (docs_cms / folder).mkdir(parents=True)
        (docs_cms / "docs-project.yaml").write_text(_project_config(structure), encoding="utf-8")
        doc_file = docs_cms / folder / filename
        doc_file.write_text("# A Document\n\nNo frontmatter here.\n", encoding="utf-8")
        return doc_file

    def test_adr_folder_bound_to_generic_gets_no_adr_fields(self, tmp_path):
        """A folder named `adr` with `schema: generic` is fixed as generic."""
        doc_file = self._write_tree(
            tmp_path,
            "  doc_types:\n    notes:\n      schema: generic\n      folders: [adr]\n",
            "adr",
            "adr-001-a-plain-note.md",
        )

        result = CliRunner().invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 0, result.output
        metadata = frontmatter.loads(doc_file.read_text(encoding="utf-8")).metadata
        assert "status" not in metadata, "a generic lane must not get an ADR status"
        assert "deciders" not in metadata, "a generic lane must not get ADR deciders"
        assert metadata["title"]
        assert metadata["project_id"]
        assert metadata["doc_uuid"]

    def test_non_standard_folder_bound_to_adr_gets_adr_fields(self, tmp_path):
        """A folder named `decisions` with `schema: adr` is fixed as an ADR."""
        doc_file = self._write_tree(
            tmp_path,
            "  doc_types:\n    adr:\n      schema: adr\n      folders: [decisions]\n",
            "decisions",
            "adr-001-pick-a-datastore.md",
        )

        result = CliRunner().invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 0, result.output
        metadata = frontmatter.loads(doc_file.read_text(encoding="utf-8")).metadata
        assert metadata["status"] == "Proposed"
        assert metadata["deciders"]
        assert metadata["id"] == "adr-001"

    def test_configured_generic_status_is_not_remapped(self, tmp_path):
        """An existing status in a generic lane is left alone, not ADR-mapped."""
        docs_cms = tmp_path / "docs-cms"
        (docs_cms / "adr").mkdir(parents=True)
        (docs_cms / "docs-project.yaml").write_text(
            _project_config("  doc_types:\n    notes:\n      schema: generic\n      folders: [adr]\n"),
            encoding="utf-8",
        )
        doc_file = docs_cms / "adr" / "adr-001-a-plain-note.md"
        doc_file.write_text(
            "---\n"
            'title: "A Plain Note"\n'
            "status: pending\n"
            "tags: []\n"
            'project_id: "fixture-project"\n'
            'doc_uuid: "12345678-1234-4123-8123-123456789abc"\n'
            "---\n\n"
            "# A Plain Note\n",
            encoding="utf-8",
        )

        result = CliRunner().invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 0, result.output
        metadata = frontmatter.loads(doc_file.read_text(encoding="utf-8")).metadata
        assert metadata["status"] == "pending", "a generic lane has no status vocabulary to map into"

    def test_without_config_the_folder_heuristic_still_applies(self, tmp_path):
        """With no docs-project.yaml, `adr/` still produces ADR frontmatter."""
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)
        doc_file = adr_dir / "adr-001-pick-a-datastore.md"
        doc_file.write_text("# A Document\n\nNo frontmatter here.\n", encoding="utf-8")

        result = CliRunner().invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 0, result.output
        metadata = frontmatter.loads(doc_file.read_text(encoding="utf-8")).metadata
        assert metadata["status"] == "Proposed"
        assert metadata["deciders"]
        assert metadata["id"] == "adr-001"
