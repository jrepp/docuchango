"""Integration test for the --fix flag in the validate command."""

import pytest

from docuchango.validator import DocValidator


class TestValidateFixIntegration:
    """Test the --fix flag integration in the validate command."""

    @pytest.fixture
    def broken_doc(self, tmp_path):
        """Create a document with fixable issues."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test-decision.md"
        # Use actual trailing spaces by concatenating
        broken_content = (
            "---\n"
            "title: Test Decision Record\n"
            "status: Proposed\n"
            "date: 2024-10-13\n"
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
        doc_file.write_text(broken_content)
        return docs_root, doc_file

    def test_validate_without_fix_detects_errors(self, broken_doc):
        """Test that validation detects errors without --fix flag."""
        docs_root, _doc_file = broken_doc

        validator = DocValidator(repo_root=docs_root, verbose=False, fix=False)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        # Collect all errors
        all_errors = list(validator.errors)
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        # Should have errors for:
        # 1. Trailing whitespace
        # 2. Missing language on opening fence
        # 3. Language on closing fence
        # 4. Missing blank lines before fences
        assert len(all_errors) > 0, "Should detect validation errors"

        # Check for specific error types
        trailing_ws_errors = [e for e in all_errors if "trailing whitespace" in e.lower()]
        code_block_errors = [e for e in all_errors if "code" in e.lower() or "fence" in e.lower()]

        assert len(trailing_ws_errors) > 0, "Should detect trailing whitespace"
        assert len(code_block_errors) > 0, "Should detect code block errors"

    def test_validate_with_fix_applies_fixes(self, broken_doc):
        """Test that validation with --fix applies fixes."""
        docs_root, doc_file = broken_doc

        # Validate with fix enabled
        validator = DocValidator(repo_root=docs_root, verbose=False, fix=True)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        # Read the fixed content
        fixed_content = doc_file.read_text()

        # Verify fixes were applied
        assert "   \n" not in fixed_content, "Trailing whitespace should be removed"
        assert "```text\n" in fixed_content, "Missing language should be added"

        # Check that closing fence no longer has language
        lines = fixed_content.split("\n")
        closing_fences = [i for i, line in enumerate(lines) if line.strip() == "```" and i > 0]
        assert len(closing_fences) >= 1, "Should have at least one proper closing fence"

        # Verify blank lines were added before fences
        assert "\n\n```" in fixed_content, "Blank lines should be added before fences"

    def test_validate_with_fix_passes_validation(self, broken_doc):
        """Test that documents pass validation after fixes are applied."""
        docs_root, _doc_file = broken_doc

        # First pass: apply fixes
        validator = DocValidator(repo_root=docs_root, verbose=False, fix=True)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        # Second pass: validate without fixes to check if issues are resolved
        validator2 = DocValidator(repo_root=docs_root, verbose=False, fix=False)
        validator2.scan_documents()
        validator2.check_code_blocks()
        validator2.check_formatting()

        # Collect errors
        all_errors = list(validator2.errors)
        for doc in validator2.documents:
            all_errors.extend(doc.errors)

        # Filter for formatting and code block errors (which should be fixed)
        fixable_errors = [
            e
            for e in all_errors
            if any(keyword in e.lower() for keyword in ["trailing whitespace", "code fence", "blank line", "fence"])
        ]

        assert len(fixable_errors) == 0, f"Should have no fixable errors after fix: {fixable_errors}"

    def test_multiple_documents_with_fix(self, tmp_path):
        """Test that --fix works across multiple documents."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        # Create multiple broken documents
        for i in range(1, 4):
            doc_file = doc_dir / f"adr-{i:03d}-test-decision.md"
            broken_content = f"""---
title: Test Decision {i}
status: Proposed
date: 2024-10-13
deciders: Team
tags: ["test"]
id: "adr-{i:03d}"
doc_uuid: "12345678-1234-4123-8123-12345678{i:03d}c"
---
Text with issues
```
code
```
"""
            doc_file.write_text(broken_content)

        # Apply fixes
        validator = DocValidator(repo_root=docs_root, verbose=False, fix=True)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        assert len(validator.documents) == 3, "Should find all 3 documents"

        # Verify all documents were fixed
        for i in range(1, 4):
            doc_file = doc_dir / f"adr-{i:03d}-test-decision.md"
            content = doc_file.read_text()
            assert "   \n" not in content, f"Document {i} should have no trailing whitespace"
            assert "```text\n" in content, f"Document {i} should have language on code fence"

    def test_fix_flag_idempotent(self, broken_doc):
        """Test that applying --fix multiple times is safe (idempotent)."""
        docs_root, doc_file = broken_doc

        # Apply fixes first time
        validator1 = DocValidator(repo_root=docs_root, verbose=False, fix=True)
        validator1.scan_documents()
        validator1.check_code_blocks()
        validator1.check_formatting()

        content_after_first = doc_file.read_text()

        # Apply fixes second time
        validator2 = DocValidator(repo_root=docs_root, verbose=False, fix=True)
        validator2.scan_documents()
        validator2.check_code_blocks()
        validator2.check_formatting()

        content_after_second = doc_file.read_text()

        # Content should be identical after both passes
        assert content_after_first == content_after_second, "Fixes should be idempotent"
