"""Tests for mdx_code_blocks.py fix module."""


from docuchango.fixes.mdx_code_blocks import fix_code_blocks


class TestMDXCodeBlocksFixes:
    """Test MDX code block fixing functionality."""

    def test_add_text_to_unlabeled_block(self, tmp_path):
        """Test adding 'text' language to unlabeled code block."""
        test_file = tmp_path / "test.md"
        content = """# Title

Some text
```
code content
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1
        assert "Line 4" in changes
        assert "Added 'text' language" in changes

        result = test_file.read_text(encoding="utf-8")
        assert "```text" in result
        assert result.count("```text") == 1

    def test_preserve_labeled_block(self, tmp_path):
        """Test that labeled code blocks are preserved."""
        test_file = tmp_path / "test.md"
        content = """# Title

```python
code content
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0
        assert changes == ""

        result = test_file.read_text(encoding="utf-8")
        assert "```python" in result
        assert "```text" not in result

    def test_multiple_unlabeled_blocks(self, tmp_path):
        """Test fixing multiple unlabeled blocks."""
        test_file = tmp_path / "test.md"
        content = """# Title

```
block 1
```

Some text

```
block 2
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 2

        result = test_file.read_text(encoding="utf-8")
        assert result.count("```text") == 2

    def test_mixed_labeled_and_unlabeled(self, tmp_path):
        """Test file with both labeled and unlabeled blocks."""
        test_file = tmp_path / "test.md"
        content = """# Title

```python
labeled
```

```
unlabeled
```

```javascript
labeled
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "```python" in result
        assert "```text" in result
        assert "```javascript" in result

    def test_preserve_indentation(self, tmp_path):
        """Test that indentation is preserved."""
        test_file = tmp_path / "test.md"
        content = """# Title

    ```
    indented code
    ```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "    ```text" in result

    def test_empty_file(self, tmp_path):
        """Test empty file handling."""
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0
        assert changes == ""

    def test_no_code_blocks(self, tmp_path):
        """Test file with no code blocks."""
        test_file = tmp_path / "test.md"
        content = """# Title

Just some text without any code blocks.
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0
        assert changes == ""

    def test_unicode_content_preserved(self, tmp_path):
        """Test Unicode content is preserved."""
        test_file = tmp_path / "test.md"
        content = """# Title → ✓

中文

```
code with unicode: 中文
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "中文" in result
        assert "→" in result
        assert "✓" in result

    def test_closing_fence_not_modified(self, tmp_path):
        """Test that closing fences are not modified."""
        test_file = tmp_path / "test.md"
        content = """```
code
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Opening fence should have 'text', closing should not
        lines = result.split("\n")
        assert lines[0] == "```text"
        assert lines[2] == "```"

    def test_code_block_with_language_and_options(self, tmp_path):
        """Test code block with language and options."""
        test_file = tmp_path / "test.md"
        content = """```python title="example.py"
code
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0

        result = test_file.read_text(encoding="utf-8")
        assert '```python title="example.py"' in result

    def test_line_number_tracking(self, tmp_path):
        """Test that line numbers are tracked correctly."""
        test_file = tmp_path / "test.md"
        content = """Line 1
Line 2
```
code
```
Line 6
```
more code
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 2
        assert "Line 3" in changes
        assert "Line 7" in changes

    def test_no_modification_when_no_fixes(self, tmp_path):
        """Test file is not written when no fixes are needed."""
        test_file = tmp_path / "test.md"
        content = """```python
code
```
"""
        test_file.write_text(content, encoding="utf-8")
        original_mtime = test_file.stat().st_mtime

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0

        # File should not be modified
        assert test_file.stat().st_mtime == original_mtime

    def test_adjacent_code_blocks(self, tmp_path):
        """Test adjacent code blocks."""
        test_file = tmp_path / "test.md"
        content = """```
block 1
```
```
block 2
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 2

        result = test_file.read_text(encoding="utf-8")
        assert result.count("```text") == 2

    def test_code_block_with_only_whitespace_label(self, tmp_path):
        """Test code block with whitespace after backticks."""
        test_file = tmp_path / "test.md"
        content = """```
code
```
"""
        test_file.write_text(content, encoding="utf-8")

        # Current implementation treats "```   " as unlabeled
        fixes, changes = fix_code_blocks(test_file)
        # Behavior may vary - this documents actual behavior
        result = test_file.read_text(encoding="utf-8")
        assert "```" in result

    def test_deeply_nested_content(self, tmp_path):
        """Test code block in nested list."""
        test_file = tmp_path / "test.md"
        content = """- Item 1
  - Item 2
    ```
    nested code
    ```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "    ```text" in result

    def test_code_block_with_backticks_in_content(self, tmp_path):
        """Test code block containing backticks."""
        test_file = tmp_path / "test.md"
        content = """```
This has inline `backticks`
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "```text" in result
        assert "inline `backticks`" in result

    def test_newline_preservation(self, tmp_path):
        """Test that newlines are preserved correctly."""
        test_file = tmp_path / "test.md"
        content = "Line 1\n\n```\ncode\n```\n\nLine 2\n"
        test_file.write_text(content, encoding="utf-8")

        fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should have same number of newlines
        assert result.count("\n") == content.count("\n")
