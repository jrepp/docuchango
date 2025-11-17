"""Test suite for the documentation validator."""

from pathlib import Path

import pytest

from docuchango.validator import DocValidator


class TestMarkdownValidation:
    """Test markdown validation against known good and bad fixtures."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"

    def test_fixtures_exist(self, fixtures_dir):
        """Verify that test fixtures directory exists and contains files."""
        assert fixtures_dir.exists(), "Fixtures directory does not exist"
        assert (fixtures_dir / "pass").exists(), "Pass fixtures directory missing"
        assert (fixtures_dir / "fail").exists(), "Fail fixtures directory missing"

        pass_fixtures = list((fixtures_dir / "pass").glob("*.md"))
        fail_fixtures = list((fixtures_dir / "fail").glob("*.md"))

        assert len(pass_fixtures) > 0, "No passing fixtures found"
        assert len(fail_fixtures) > 0, "No failing fixtures found"

    def test_passing_fixtures(self, fixtures_dir, tmp_path):
        """Test that documents in pass directory validate successfully."""
        pass_dir = fixtures_dir / "pass"
        fixtures = list(pass_dir.glob("*.md"))

        assert len(fixtures) > 0, "No passing test fixtures found"

        for fixture_file in fixtures:
            docs_root = tmp_path / f"test_{fixture_file.stem}"

            if fixture_file.stem.startswith("adr-"):
                target_dir = docs_root / "docs-cms" / "adr"
            elif fixture_file.stem.startswith("rfc-"):
                target_dir = docs_root / "docs-cms" / "rfcs"
            elif fixture_file.stem.startswith("memo-"):
                target_dir = docs_root / "docs-cms" / "memos"
            else:
                pytest.fail(f"Unknown fixture type: {fixture_file.stem}")

            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / fixture_file.name
            target_file.write_text(fixture_file.read_text())

            validator = DocValidator(repo_root=docs_root, verbose=False)
            validator.scan_documents()
            validator.check_code_blocks()
            validator.check_formatting()

            # Collect all errors (validator-level + all document-level)
            all_errors = list(validator.errors)
            for doc in validator.documents:
                all_errors.extend(doc.errors)

            code_block_errors = [e for e in all_errors if "code block" in e.lower() or "fence" in e.lower()]
            format_errors = [e for e in all_errors if "whitespace" in e.lower()]

            assert len(code_block_errors) == 0, (
                f"Fixture {fixture_file.name} has code block errors: {code_block_errors}"
            )
            assert len(format_errors) == 0, f"Fixture {fixture_file.name} has formatting errors: {format_errors}"

    def test_failing_fixtures(self, fixtures_dir, tmp_path):
        """Test that documents in fail directory fail validation with expected errors."""
        fail_dir = fixtures_dir / "fail"
        fixtures = list(fail_dir.glob("*.md"))

        assert len(fixtures) > 0, "No failing test fixtures found"

        for fixture_file in fixtures:
            docs_root = tmp_path / f"test_{fixture_file.stem}"

            if fixture_file.stem.startswith("adr-"):
                target_dir = docs_root / "docs-cms" / "adr"
            elif fixture_file.stem.startswith("rfc-"):
                target_dir = docs_root / "docs-cms" / "rfcs"
            elif fixture_file.stem.startswith("memo-"):
                target_dir = docs_root / "docs-cms" / "memos"
            else:
                pytest.fail(f"Unknown fixture type: {fixture_file.stem}")

            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / fixture_file.name
            target_file.write_text(fixture_file.read_text())

            validator = DocValidator(repo_root=docs_root, verbose=False)
            validator.scan_documents()
            validator.check_code_blocks()
            validator.check_formatting()

            # Collect all errors (validator-level + all document-level)
            all_errors = list(validator.errors)
            for doc in validator.documents:
                all_errors.extend(doc.errors)

            assert len(all_errors) > 0, f"Fixture {fixture_file.name} should fail but passed validation"

    def test_unclosed_code_fence_error_message(self, tmp_path):
        """Test that unclosed code fence errors are clear and point to the root cause (Issue #31)."""
        docs_root = tmp_path / "test_issue31"
        target_dir = docs_root / "docs-cms" / "memos"
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create a document with an unclosed code fence that causes cascading errors
        content = """---
id: "memo-999"
slug: memo-999-test
title: "Test Unclosed Fence"
date: "2025-11-16"
author: "Test Author"
created: "2025-11-16"
updated: "2025-11-16"
tags: ["test"]
project_id: "test-project"
doc_uuid: "12345678-1234-4000-8000-123456789012"
---

## Section 1

Some content here.

```markdown
This is markdown content.
More markdown content here.

## Section 2

This should trigger confusion because the markdown fence above is unclosed.

```text
This looks like a new code block.
```

## Section 3

More content.
"""
        target_file = target_dir / "memo-999-test-unclosed.md"
        target_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.check_code_blocks()

        # Collect all errors
        all_errors = []
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        # Should have at least 2 errors: unclosed block + cascading error
        assert len(all_errors) >= 2, f"Expected at least 2 errors, got {len(all_errors)}: {all_errors}"

        # First error should mention the unclosed block at the original location (line 18)
        unclosed_errors = [e for e in all_errors if "Unclosed code block starting at line 18" in e]
        assert len(unclosed_errors) > 0, f"Should detect unclosed block at line 18. Errors: {all_errors}"

        # Should have a cascading error explanation
        cascading_errors = [e for e in all_errors if "appears to be a new opening fence" in e and "interpreted as a closing fence" in e]
        assert len(cascading_errors) > 0, f"Should explain cascading error. Errors: {all_errors}"

        # Should NOT have confusing "Closing fence has extra text" errors without context
        confusing_errors = [e for e in all_errors if "Closing code fence has extra text" in e and "appears to be" not in e]
        assert len(confusing_errors) == 0, f"Should not have confusing closing fence errors. Found: {confusing_errors}"
