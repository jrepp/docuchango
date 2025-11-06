"""Tests for code_blocks_proper.py fix module."""

from docuchango.fixes.code_blocks_proper import fix_code_blocks


class TestCodeBlocksProperFixes:
    """Test proper code block fixing functionality."""

    def test_add_text_to_bare_opening_fence(self, tmp_path):
        """Test adding 'text' to bare opening fence."""
        test_file = tmp_path / "test.md"
        content = """```
code without language
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1
        assert "text" in changes
        assert "bare opening" in changes.lower()

        result = test_file.read_text(encoding="utf-8")
        assert "```text\n" in result

    def test_remove_language_from_closing_fence(self, tmp_path):
        """Test removing language from closing fence."""
        test_file = tmp_path / "test.md"
        content = """```python
code here
```python
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1
        assert "closing fence" in changes.lower()

        result = test_file.read_text(encoding="utf-8")
        lines = result.strip().split("\n")
        assert lines[-1] == "```"

    def test_close_unclosed_block(self, tmp_path):
        """Test adding closing fence to unclosed block."""
        test_file = tmp_path / "test.md"
        content = """```python
code without closing
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1
        assert "missing closing fence" in changes.lower()

        result = test_file.read_text(encoding="utf-8")
        assert result.strip().endswith("```")

    def test_no_fixes_needed(self, tmp_path):
        """Test file with correct code blocks."""
        test_file = tmp_path / "test.md"
        content = """```python
code here
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0
        assert changes == ""

    def test_multiple_issues_in_one_file(self, tmp_path):
        """Test fixing multiple issues in one file."""
        test_file = tmp_path / "test.md"
        content = """```
first block without language
```

```python
second block
```python

```bash
third block
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 2  # Bare opening + closing with language
        assert "text" in changes
        assert "python" in changes.lower()

    def test_preserve_indentation(self, tmp_path):
        """Test that indentation is preserved."""
        test_file = tmp_path / "test.md"
        content = """Some list:
- Item 1
    ```
    indented code
    ```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should preserve indentation
        assert "    ```text" in result

    def test_multiple_code_blocks(self, tmp_path):
        """Test multiple code blocks in sequence."""
        test_file = tmp_path / "test.md"
        content = """```python
block 1
```

```bash
block 2
```

```javascript
block 3
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0  # All blocks are properly formatted

    def test_bare_closing_fence(self, tmp_path):
        """Test that bare closing fences are preserved."""
        test_file = tmp_path / "test.md"
        content = """```python
code
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0

        result = test_file.read_text(encoding="utf-8")
        assert result == content

    def test_language_with_options(self, tmp_path):
        """Test fence with language and options."""
        test_file = tmp_path / "test.md"
        content = """```python {1,3-5}
line 1
line 2
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        # Should not break language options
        assert fixes == 0

    def test_unicode_in_code_blocks(self, tmp_path):
        """Test handling of Unicode in code blocks."""
        test_file = tmp_path / "test.md"
        content = """```python
# Unicode: → ✓ ✗
print("Hello 世界")
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should preserve Unicode
        assert "→" in result
        assert "世界" in result

    def test_empty_file(self, tmp_path):
        """Test handling of empty file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0
        assert changes == ""

    def test_no_code_blocks(self, tmp_path):
        """Test file with no code blocks."""
        test_file = tmp_path / "test.md"
        content = """# Title

Just regular markdown content.

No code blocks here.
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0
        assert changes == ""

    def test_consecutive_fences(self, tmp_path):
        """Test handling of consecutive code fences."""
        test_file = tmp_path / "test.md"
        content = """```python
block1
```
```bash
block2
```
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 0  # Both blocks are properly formatted

    def test_fence_with_whitespace_after_language(self, tmp_path):
        """Test fence with whitespace after language."""
        test_file = tmp_path / "test.md"
        content = """```python
code
```python
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1
        assert "closing fence" in changes.lower()

    def test_only_opening_fence(self, tmp_path):
        """Test file with only opening fence (unclosed)."""
        test_file = tmp_path / "test.md"
        content = "```python\ncode"
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1
        assert "missing closing" in changes.lower()

        result = test_file.read_text(encoding="utf-8")
        assert result.endswith("```")

    def test_bare_opening_and_bad_closing(self, tmp_path):
        """Test bare opening fence and closing with language."""
        test_file = tmp_path / "test.md"
        content = """```
code
```text
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 2  # Both opening and closing need fixes

    def test_four_backtick_fence(self, tmp_path):
        """Test that four-backtick fences are handled."""
        test_file = tmp_path / "test.md"
        content = """````markdown
```code
nested
```
````
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        # Should handle 4-backtick fences as separate blocks
        result = test_file.read_text(encoding="utf-8")
        assert "````" in result

    def test_preserve_blank_lines_in_code(self, tmp_path):
        """Test that blank lines in code blocks are preserved."""
        test_file = tmp_path / "test.md"
        content = """```python
line1

line3
```
"""
        test_file.write_text(content, encoding="utf-8")

        fix_code_blocks(test_file)
        result = test_file.read_text(encoding="utf-8")

        # Should preserve blank line
        assert "line1\n\nline3" in result

    def test_closing_fence_with_long_language(self, tmp_path):
        """Test closing fence with long language string."""
        test_file = tmp_path / "test.md"
        content = """```javascript
code
```javascript {1,2-5} title="example"
"""
        test_file.write_text(content, encoding="utf-8")

        fixes, changes = fix_code_blocks(test_file)
        assert fixes == 1
        # Should remove everything after closing fence
        result = test_file.read_text(encoding="utf-8")
        lines = result.strip().split("\n")
        assert lines[-1] == "```"
