"""Test suite for fix functionality using temporary filesystem."""

from docuchango.fixes.docs import (
    add_missing_frontmatter_fields,
    fix_blank_lines_before_fences,
    fix_code_fence_languages,
    fix_trailing_whitespace,
)


class TestFixTrailingWhitespace:
    """Test trailing whitespace fix functionality."""

    def test_fix_trailing_whitespace(self, tmp_path):
        """Test that trailing whitespace is removed."""
        test_file = tmp_path / "test.md"
        content = "Line 1   \nLine 2\t\nLine 3\n"
        test_file.write_text(content)

        changes = fix_trailing_whitespace(test_file)
        assert changes == 2  # Lines 1 and 2 had trailing whitespace

        result = test_file.read_text()
        assert result == "Line 1\nLine 2\nLine 3\n"

    def test_fix_no_trailing_whitespace(self, tmp_path):
        """Test that files without trailing whitespace are unchanged."""
        test_file = tmp_path / "test.md"
        content = "Line 1\nLine 2\nLine 3\n"
        test_file.write_text(content)

        changes = fix_trailing_whitespace(test_file)
        assert changes == 0

        result = test_file.read_text()
        assert result == content


class TestFixCodeFenceLanguages:
    """Test code fence language fix functionality."""

    def test_add_text_to_empty_fence(self, tmp_path):
        """Test that empty code fences get 'text' added."""
        test_file = tmp_path / "test.md"
        content = """# Header

```
code here
```

More text
"""
        test_file.write_text(content)

        changes = fix_code_fence_languages(test_file)
        assert changes == 1

        result = test_file.read_text()
        assert "```text\n" in result
        assert result.count("```\n") == 1  # Only closing fence

    def test_preserve_existing_languages(self, tmp_path):
        """Test that fences with languages are preserved."""
        test_file = tmp_path / "test.md"
        content = """```python
def foo():
    pass
```
"""
        test_file.write_text(content)

        changes = fix_code_fence_languages(test_file)
        assert changes == 0

        result = test_file.read_text()
        assert "```python\n" in result

    def test_fix_closing_fence_with_language(self, tmp_path):
        """Test that closing fences with language text are fixed."""
        test_file = tmp_path / "test.md"
        content = """```python
code
```python
"""
        test_file.write_text(content)

        changes = fix_code_fence_languages(test_file)
        assert changes == 1

        result = test_file.read_text()
        lines = result.split("\n")
        assert lines[-2] == "```"  # Closing fence should be clean


class TestFixBlankLinesBeforeFences:
    """Test blank line before fence fix functionality."""

    def test_add_blank_line_before_fence(self, tmp_path):
        """Test that blank lines are added before code fences."""
        test_file = tmp_path / "test.md"
        content = """Some text
```python
code
```
"""
        test_file.write_text(content)

        changes = fix_blank_lines_before_fences(test_file)
        assert changes == 1

        result = test_file.read_text()
        assert "Some text\n\n```python" in result

    def test_preserve_existing_blank_lines(self, tmp_path):
        """Test that existing blank lines are preserved."""
        test_file = tmp_path / "test.md"
        content = """Some text

```python
code
```
"""
        test_file.write_text(content)

        changes = fix_blank_lines_before_fences(test_file)
        assert changes == 0

        result = test_file.read_text()
        assert content == result

    def test_skip_fence_after_frontmatter(self, tmp_path):
        """Test that fences right after frontmatter are not affected."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test
---
```bash
command
```
"""
        test_file.write_text(content)

        changes = fix_blank_lines_before_fences(test_file)
        assert changes == 0


class TestAddMissingFrontmatterFields:
    """Test frontmatter field addition functionality."""

    def test_add_missing_project_id(self, tmp_path):
        """Test that missing project_id is added."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test
---

# Content
"""
        test_file.write_text(content)

        changes = add_missing_frontmatter_fields(test_file)
        assert changes == 2  # project_id and doc_uuid

        result = test_file.read_text()
        assert "project_id:" in result
        assert "doc_uuid:" in result

    def test_skip_file_without_frontmatter(self, tmp_path):
        """Test that files without frontmatter are skipped."""
        test_file = tmp_path / "test.md"
        content = """# Header

No frontmatter here
"""
        test_file.write_text(content)

        changes = add_missing_frontmatter_fields(test_file)
        assert changes == 0

        result = test_file.read_text()
        assert result == content

    def test_preserve_existing_fields(self, tmp_path):
        """Test that existing frontmatter fields are preserved."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test
project_id: "existing-project"
doc_uuid: "12345678-1234-4123-8123-123456789abc"
---

# Content
"""
        test_file.write_text(content)

        changes = add_missing_frontmatter_fields(test_file)
        assert changes == 0

        result = test_file.read_text()
        assert 'project_id: "existing-project"' in result


class TestFixIntegration:
    """Integration tests for fix functionality."""

    def test_fix_multiple_issues(self, tmp_path):
        """Test fixing multiple issues in one file."""
        test_file = tmp_path / "broken.md"
        content = """---
title: Test Doc
---
Some text
```
code here
```
Another line
```python
more code
```text
"""
        test_file.write_text(content)

        # Apply all fixes
        fix_trailing_whitespace(test_file)
        lang_changes = fix_code_fence_languages(test_file)
        blank_changes = fix_blank_lines_before_fences(test_file)
        fm_changes = add_missing_frontmatter_fields(test_file)

        # Verify at least some fixes were applied
        assert lang_changes == 2  # Empty fence gets 'text', closing fence fixed
        assert blank_changes == 2  # Two fences need blank lines
        assert fm_changes == 2  # project_id and doc_uuid added

        result = test_file.read_text()

        # Verify all fixes were applied
        assert "```text\n" in result  # Language added
        assert "\n\n```" in result  # Blank line before fence
        assert "project_id:" in result  # Frontmatter added
        assert "doc_uuid:" in result

    def test_fix_creates_valid_document(self, tmp_path):
        """Test that fixes create a document that passes validation."""
        # Create a broken document
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        broken_content = """---
title: Test Decision Record
status: Proposed
date: 2025-10-13
deciders: Team
tags: ["test"]
id: "adr-001"
---
Some text
```
code
```
More text
"""
        doc_file.write_text(broken_content)

        # Apply fixes
        fix_trailing_whitespace(doc_file)
        fix_code_fence_languages(doc_file)
        fix_blank_lines_before_fences(doc_file)
        add_missing_frontmatter_fields(doc_file)

        # Validate with docuchango
        from docuchango.validator import DocValidator

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        # Collect errors
        all_errors = list(validator.errors)
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        # Should have minimal errors (only missing project_id/uuid are auto-fixable)
        # Frontmatter validation errors might still exist
        format_errors = [e for e in all_errors if "whitespace" in e.lower() or "code block" in e.lower()]
        assert len(format_errors) == 0, f"Format errors remain after fix: {format_errors}"
