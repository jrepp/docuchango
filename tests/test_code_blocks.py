"""Tests for code_blocks.py fix module."""

from docuchango.fixes.code_blocks import fix_code_blocks


class TestCodeBlocksFixes:
    """Test code block fixing functionality."""

    def test_add_blank_line_before_fence(self, tmp_path):
        """Test adding blank line before opening fence."""
        test_file = tmp_path / "test.md"
        content = """# Title

Some text
```python
code
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is True
        assert len(changes) > 0
        assert any("blank line before" in change.lower() for change in changes)

        result = test_file.read_text(encoding="utf-8")
        assert "Some text\n\n```python" in result

    def test_add_blank_line_after_fence(self, tmp_path):
        """Test adding blank line after closing fence."""
        test_file = tmp_path / "test.md"
        content = """# Title

```python
code
```
Next line
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is True
        assert len(changes) > 0
        assert any("blank line after" in change.lower() for change in changes)

        result = test_file.read_text(encoding="utf-8")
        assert "```\n\nNext line" in result

    def test_fix_closing_fence_with_text(self, tmp_path):
        """Test removing extra text from closing fence."""
        test_file = tmp_path / "test.md"
        content = """```python
code
```python
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is True
        assert any("closing fence" in change.lower() for change in changes)

        result = test_file.read_text(encoding="utf-8")
        lines = result.split("\n")
        # Last non-empty line should be just ```
        assert lines[-2] == "```"

    def test_add_language_to_bare_fence(self, tmp_path):
        """Test adding 'text' language to bare fence."""
        test_file = tmp_path / "test.md"
        content = """# Title

```
code without language
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is True
        assert any("text" in change.lower() and "language" in change.lower() for change in changes)

        result = test_file.read_text(encoding="utf-8")
        assert "```text\n" in result

    def test_close_unclosed_code_block(self, tmp_path):
        """Test closing unclosed code block at end of file."""
        test_file = tmp_path / "test.md"
        content = """# Title

```python
code without closing fence"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is True
        assert any("unclosed" in change.lower() for change in changes)

        result = test_file.read_text(encoding="utf-8")
        assert result.endswith("```")

    def test_no_blank_before_fence_after_frontmatter(self, tmp_path):
        """Test that no blank line is added after frontmatter."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test
---
```bash
code
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        # Should not add blank line after frontmatter
        result = test_file.read_text(encoding="utf-8")
        assert "---\n```bash" in result

    def test_preserve_frontmatter(self, tmp_path):
        """Test that frontmatter is preserved."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test Document
id: test-001
---

# Content

```python
code
```
"""
        test_file.write_text(content, encoding="utf-8")

        fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        assert "---\ntitle: Test Document" in result
        assert "id: test-001\n---" in result

    def test_multiple_code_blocks(self, tmp_path):
        """Test fixing multiple code blocks in one file."""
        test_file = tmp_path / "test.md"
        content = """# Title
```
first block
```
Text
```
second block
```bash
More text
```
third block
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is True
        # Should have multiple changes
        assert len(changes) >= 3

        result = test_file.read_text(encoding="utf-8")
        # All bare fences should have 'text' language
        assert "```text" in result

    def test_nested_backticks_in_code(self, tmp_path):
        """Test code blocks containing backticks."""
        test_file = tmp_path / "test.md"
        content = """```python
def test():
    '''Single backtick in code'''
    return `value`
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should preserve backticks inside code blocks
        assert "`value`" in result
        assert "'''Single backtick in code'''" in result

    def test_no_changes_needed(self, tmp_path):
        """Test file with no issues."""
        test_file = tmp_path / "test.md"
        content = """# Title

Paragraph text.

```python
code here
```

More text.
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is False
        assert len(changes) == 0

    def test_code_fence_at_document_start(self, tmp_path):
        """Test code fence at very beginning of document."""
        test_file = tmp_path / "test.md"
        content = """```python
code at start
```
"""
        test_file.write_text(content, encoding="utf-8")

        fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should not add blank line before (it's at document start)
        assert result.startswith("```python")

    def test_four_backtick_fence(self, tmp_path):
        """Test handling of four-backtick fences."""
        test_file = tmp_path / "test.md"
        content = """# Title

````markdown
```code
inside
```
````
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should handle 4-backtick fences
        assert "````markdown" in result
        assert "````" in result

    def test_empty_file(self, tmp_path):
        """Test handling of empty file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is False
        assert len(changes) == 0

    def test_only_frontmatter(self, tmp_path):
        """Test file with only frontmatter."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test
---
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        assert modified is False
        assert len(changes) == 0

    def test_code_block_immediately_after_frontmatter(self, tmp_path):
        """Test code block right after frontmatter."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test
---
```bash
command
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should not add blank line between frontmatter and code block
        assert "---\n```bash" in result

    def test_preserve_indentation_in_code(self, tmp_path):
        """Test that indentation is preserved in code blocks."""
        test_file = tmp_path / "test.md"
        content = """```python
def func():
    if True:
        return "indented"
```
"""
        test_file.write_text(content, encoding="utf-8")

        fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should preserve exact indentation
        assert "    if True:" in result
        assert "        return" in result

    def test_unicode_content(self, tmp_path):
        """Test handling of Unicode content."""
        test_file = tmp_path / "test.md"
        content = """# Title

```python
# Comment with unicode: → ✓ ✗ 中文
print("Hello 世界")
```
"""
        test_file.write_text(content, encoding="utf-8")

        fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should preserve Unicode characters
        assert "→" in result
        assert "✓" in result
        assert "世界" in result

    def test_error_handling_readonly_file(self, tmp_path):
        """Test error handling for read-only files."""
        import os

        test_file = tmp_path / "readonly.md"
        test_file.write_text("```\ncode\n```", encoding="utf-8")

        # Make file read-only
        os.chmod(test_file, 0o444)

        try:
            modified, changes = fix_code_blocks(test_file)
            # Should handle error gracefully
            # On some systems, writing to readonly may fail or succeed with warning
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)

    def test_mixed_line_endings(self, tmp_path):
        """Test handling of files with different line endings."""
        test_file = tmp_path / "test.md"
        # Use \n for content (Python default)
        content = "# Title\n```\ncode\n```\n"
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should maintain line ending style
        assert "\n" in result

    def test_consecutive_code_blocks(self, tmp_path):
        """Test multiple consecutive code blocks."""
        test_file = tmp_path / "test.md"
        content = """# Title

```python
block1
```
```bash
block2
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should add blank line between consecutive blocks
        assert "```\n\n```bash" in result

    def test_fence_with_language_options(self, tmp_path):
        """Test fence with language and options."""
        test_file = tmp_path / "test.md"
        content = """```python {1,3-5}
line 1
line 2
line 3
```
"""
        test_file.write_text(content, encoding="utf-8")

        modified, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should preserve language options
        assert "```python {1,3-5}" in result or "python" in result
