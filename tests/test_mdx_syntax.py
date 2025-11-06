"""Tests for mdx_syntax.py fix module."""

import time

from docuchango.fixes.mdx_syntax import fix_mdx_issues, process_file


class TestMDXSyntaxFixes:
    """Test MDX syntax fixing functionality."""

    def test_fix_basic_number(self):
        """Test fixing basic <number pattern."""
        content = "Takes <10ms"
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 1
        assert "`<10ms`" in fixed
        assert "<10" not in fixed or "`<10" in fixed

    def test_fix_number_with_percentage(self):
        """Test fixing <number% pattern."""
        content = "CPU usage <100%."
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 1
        assert "`<100%`" in fixed

    def test_fix_number_with_units(self):
        """Test fixing numbers with different units."""
        content = """Memory <5MB.
CPU <2.5GB.
Cache <1KB."""
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 3
        assert "`<5MB`" in fixed
        assert "`<2.5GB`" in fixed
        assert "`<1KB`" in fixed

    def test_fix_number_with_words(self):
        """Test fixing <number word patterns."""
        content = """Takes <1 minute.
Waits <10 seconds.
Duration <5 milliseconds."""
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 3
        assert "`<1 minute`" in fixed
        assert "`<10 seconds`" in fixed
        assert "`<5 milliseconds`" in fixed

    def test_preserve_backticked_content(self):
        """Test that already backticked content is preserved."""
        content = "Already wrapped `<10ms` stays same"
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 0
        assert fixed == content

    def test_skip_code_blocks(self):
        """Test that code blocks are skipped."""
        content = """# Title

```python
if x < 10:
    print("less than")
```

Text with <5ms."""
        fixed, changes = fix_mdx_issues(content)
        # Only the text outside code block should be fixed
        assert len(changes) == 1
        assert "if x < 10:" in fixed  # Code block unchanged
        assert "`<5ms`" in fixed  # Text fixed

    def test_multiple_patterns_in_line(self):
        """Test multiple patterns in one line."""
        content = "Takes <10ms, uses <100% CPU"
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 2
        # Both patterns should be wrapped
        assert "`<10ms`" in fixed or "`<10ms,`" in fixed
        assert "`<100%`" in fixed or "`<100% CPU`" in fixed

    def test_decimal_numbers(self):
        """Test decimal numbers."""
        content = "Value <2.5GB, <1.25ms"
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 2
        assert "`<2.5GB`" in fixed or "`<2.5GB,`" in fixed
        assert "`<1.25ms`" in fixed

    def test_no_changes_needed(self):
        """Test content with no MDX issues."""
        content = "Normal text without problems"
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 0
        assert fixed == content

    def test_empty_content(self):
        """Test empty content."""
        content = ""
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 0
        assert fixed == ""

    def test_unicode_content_preserved(self):
        """Test Unicode characters are preserved."""
        content = "Title → <10ms, ✓ success 中文"
        fixed, changes = fix_mdx_issues(content)
        assert "→" in fixed
        assert "✓" in fixed
        assert "中文" in fixed

    def test_redos_protection(self):
        """Test that regex doesn't suffer from ReDoS (catastrophic backtracking)."""
        # Create adversarial input with long words
        adversarial = "<123 " + "a" * 100 + " more text"

        start = time.time()
        fixed, changes = fix_mdx_issues(adversarial)
        elapsed = time.time() - start

        # ReDoS would cause timeout (seconds/minutes), not milliseconds
        # Use generous threshold (2s) to account for slow CI systems
        assert elapsed < 2.0, f"Regex took too long: {elapsed}s (possible ReDoS)"
        assert len(changes) >= 1  # Should match

    def test_word_length_boundary(self):
        """Test word length is bounded to 20 characters."""
        # Word over boundary - won't fully match but won't hang
        content = "<10 " + "a" * 30
        start = time.time()
        fixed, changes = fix_mdx_issues(content)
        elapsed = time.time() - start
        # Use generous threshold to avoid flaky tests on slow systems
        assert elapsed < 1.0, f"Regex took too long: {elapsed}s"

    def test_line_number_tracking(self):
        """Test that line numbers are tracked in changes."""
        content = """Line 1
Line 2 <10ms.
Line 3
Line 4 <5s."""
        fixed, changes = fix_mdx_issues(content)
        assert len(changes) == 2
        assert "Line 2:" in changes[0]
        assert "Line 4:" in changes[1]


class TestMDXSyntaxFileProcessing:
    """Test file-level MDX syntax processing."""

    def test_process_file_no_changes(self, tmp_path):
        """Test processing file with no changes needed."""
        test_file = tmp_path / "test.md"
        content = "Normal content"
        test_file.write_text(content, encoding="utf-8")

        result = process_file(test_file, dry_run=False)
        assert result is False

    def test_process_file_error_handling(self, tmp_path, capsys):
        """Test error handling for nonexistent file."""
        test_file = tmp_path / "nonexistent.md"

        result = process_file(test_file, dry_run=False)
        assert result is False

        captured = capsys.readouterr()
        assert "error" in captured.out.lower()

    def test_process_file_unicode(self, tmp_path):
        """Test processing file with Unicode."""
        test_file = tmp_path / "test.md"
        content = "速度 <10ms. → ✓"
        test_file.write_text(content, encoding="utf-8")

        # May succeed or fail depending on path resolution, but shouldn't crash
        process_file(test_file, dry_run=False)
        fixed = test_file.read_text(encoding="utf-8")

        # Unicode should be preserved either way
        assert "速度" in fixed
        assert "→" in fixed
        assert "✓" in fixed

    def test_process_file_preserves_newlines(self, tmp_path):
        """Test that newlines are preserved."""
        test_file = tmp_path / "test.md"
        content = "Line 1 <10ms.\nLine 2\nLine 3 <5s.\n"
        test_file.write_text(content, encoding="utf-8")

        process_file(test_file, dry_run=False)
        fixed = test_file.read_text(encoding="utf-8")

        # Should have same number of lines
        assert fixed.count("\n") == content.count("\n")
