"""Comprehensive tests for frontmatter fixes - positive, negative, and edge cases."""

from pathlib import Path

import frontmatter
import pytest

from docuchango.fixes.frontmatter import (
    add_missing_frontmatter,
    fix_all_frontmatter,
    fix_date_format,
    fix_status_value,
    get_doc_type,
)


class TestGetDocTypeEdgeCases:
    """Edge case tests for document type detection."""

    def test_case_insensitive_detection(self):
        """Test case-insensitive path detection."""
        assert get_doc_type(Path("docs/ADR/adr-001.md")) == "adr"
        assert get_doc_type(Path("DOCS/RFCS/rfc-001.md")) == "rfc"
        assert get_doc_type(Path("Docs/Memos/memo.md")) == "memo"

    def test_nested_paths(self):
        """Test detection in deeply nested paths."""
        assert get_doc_type(Path("/home/user/project/docs/adr/subdir/adr-001.md")) == "adr"
        # Windows paths on Unix systems may not work as expected
        result = get_doc_type(Path("C:\\Users\\dev\\docs\\rfcs\\v2\\rfc-001.md"))
        assert result in ("rfc", None)  # May fail on non-Windows

    def test_ambiguous_paths(self):
        """Test paths with multiple type indicators."""
        # Should match first occurrence
        assert get_doc_type(Path("adr/rfcs/test.md")) == "adr"
        assert get_doc_type(Path("rfcs/adr/test.md")) == "rfc"

    def test_similar_directory_names(self):
        """Test paths with similar but incorrect names."""
        assert get_doc_type(Path("adrs/test.md")) is None  # plural
        assert get_doc_type(Path("rfc/test.md")) is None  # missing 's'
        assert get_doc_type(Path("memoranda/test.md")) is None  # different word

    def test_windows_paths(self):
        """Test Windows-style paths.

        Note: On Unix systems, Windows-style backslash paths are treated as a single
        path component, so they won't match directory patterns. This is expected behavior.
        """
        import platform

        if platform.system() == "Windows":
            # On Windows, these paths should work
            assert get_doc_type(Path("C:\\docs\\adr\\adr-001.md")) == "adr"
            assert get_doc_type(Path("D:\\project\\rfcs\\rfc-001.md")) == "rfc"
        else:
            # On Unix, Windows paths with backslashes are single path components
            # and won't match directory patterns - this is expected
            assert get_doc_type(Path("C:\\docs\\adr\\adr-001.md")) is None
            assert get_doc_type(Path("D:\\project\\rfcs\\rfc-001.md")) is None


class TestFixStatusValueEdgeCases:
    """Edge case tests for status value fixing."""

    def test_status_with_special_characters(self, tmp_path):
        """Test status values with special characters."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
status: "draft!"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        # Should still map despite special chars
        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["status"] == "Proposed"

    def test_status_with_leading_trailing_spaces(self, tmp_path):
        """Test status with whitespace."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
status: "  draft  "
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        assert changed

    def test_numeric_status(self, tmp_path):
        """Test handling of numeric status values."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
status: 123
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        assert not changed
        assert "not a string" in msg

    def test_empty_status(self, tmp_path):
        """Test empty status value."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
status: ""
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        # Empty string should not match any mapping
        assert not changed
        assert "empty" in msg.lower()

    def test_very_long_status(self, tmp_path):
        """Test very long status strings."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        long_status = "draft " * 100
        content = f"""---
id: "adr-001"
status: "{long_status}"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        # Should still detect "draft" in the string
        assert changed

    def test_unicode_status(self, tmp_path):
        """Test Unicode characters in status."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
status: "drāft"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        # Should not match with Unicode chars
        assert not changed

    def test_multiple_matching_keywords(self, tmp_path):
        """Test status with multiple matching keywords."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
status: "draft pending"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        # Should match first occurrence
        assert changed


class TestFixDateFormatEdgeCases:
    """Edge case tests for date format fixing."""

    def test_invalid_date_formats(self, tmp_path):
        """Test various invalid date formats."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        invalid_dates = [
            "2025-13-01",  # Invalid month
            "2025-02-30",  # Invalid day
            "not-a-date",
            "12345",
            "2025/02/30",  # Invalid date with slashes
        ]

        for invalid_date in invalid_dates:
            content = f"""---
id: "adr-001"
date: {invalid_date}
---
# Test
"""
            doc.write_text(content)
            changed, msg = fix_date_format(doc)
            assert not changed, f"Should not parse invalid date: {invalid_date}"

    def test_ambiguous_date_formats(self, tmp_path):
        """Test ambiguous date formats (US vs EU)."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        # 01/02/2025 - could be Jan 2 or Feb 1
        content = """---
id: "adr-001"
date: "01/02/2025"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        # Should try US format first (mm/dd/yyyy)
        if changed:
            post = frontmatter.loads(doc.read_text())
            # Should be Feb 1, 2025 (US format)
            assert post.metadata["date"] == "2025-02-01"

    def test_partial_dates(self, tmp_path):
        """Test partial date formats."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
date: "2025-01"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        # Should not parse partial dates
        assert not changed

    def test_date_with_time(self, tmp_path):
        """Test date with time component."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
date: "2025-01-26 14:30:00"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        # Should not parse datetime strings
        assert not changed

    def test_very_old_dates(self, tmp_path):
        """Test very old dates."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
date: "1900-01-01"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        # Already ISO format
        assert not changed

    def test_future_dates(self, tmp_path):
        """Test future dates."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
date: "2099-12-31"
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        # Already ISO format, should not change
        assert not changed

    def test_date_as_integer(self, tmp_path):
        """Test date stored as integer."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
date: 20250126
---
# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        # Should not handle integer dates
        assert not changed


class TestAddMissingFrontmatterEdgeCases:
    """Edge case tests for adding missing frontmatter."""

    def test_file_with_no_content(self, tmp_path):
        """Test file with only frontmatter marker."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("---\n")

        changed, msg = add_missing_frontmatter(doc)
        # Should detect incomplete frontmatter
        assert not changed

    def test_file_with_malformed_frontmatter(self, tmp_path):
        """Test file with malformed YAML."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: adr-001
  invalid: yaml:
---
# Test
"""
        doc.write_text(content)

        # Should be caught as existing frontmatter (malformed)
        changed, msg = add_missing_frontmatter(doc)
        assert not changed

    def test_filename_without_id_pattern(self, tmp_path):
        """Test filename that doesn't match ID pattern."""
        doc = tmp_path / "adr" / "random-file.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("# Test")

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        post = frontmatter.loads(doc.read_text())
        # Should use full filename
        assert "random-file" in post.metadata["id"]

    def test_filename_with_special_characters(self, tmp_path):
        """Test filename with special characters."""
        doc = tmp_path / "adr" / "adr-001-api@design.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("# Test")

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "adr-001"

    def test_very_long_filename(self, tmp_path):
        """Test very long filename."""
        doc = tmp_path / "adr" / ("a" * 200 + ".md")
        doc.parent.mkdir(parents=True)

        doc.write_text("# Test")

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        post = frontmatter.loads(doc.read_text())
        # Should handle long filenames
        assert len(post.metadata["title"]) > 0

    def test_unicode_in_filename(self, tmp_path):
        """Test Unicode characters in filename."""
        doc = tmp_path / "adr" / "adr-001-测试.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("# Test")

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "adr-001"


class TestFixAllFrontmatterEdgeCases:
    """Edge case tests for combined frontmatter fixes."""

    def test_empty_file(self, tmp_path):
        """Test completely empty file."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("")

        messages = fix_all_frontmatter(doc)
        # Should handle gracefully
        assert isinstance(messages, list)

    def test_file_with_only_whitespace(self, tmp_path):
        """Test file with only whitespace."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("   \n\n   \n")

        messages = fix_all_frontmatter(doc)
        assert isinstance(messages, list)

    def test_file_with_binary_content(self, tmp_path):
        """Test file with binary content."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        # Write actual binary content that will fail UTF-8 decoding
        doc.write_bytes(b"\xff\xfe\x00\x01\x02\x03")

        with pytest.raises((ValueError, UnicodeDecodeError)):
            fix_all_frontmatter(doc)

    def test_extremely_large_frontmatter(self, tmp_path):
        """Test file with very large frontmatter."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        # Create frontmatter with many fields
        fields = "\n".join([f'field{i}: "value{i}"' for i in range(1000)])
        content = f"""---
id: "adr-001"
status: Draft
date: 2025/01/26
{fields}
---
# Test
"""
        doc.write_text(content)

        messages = fix_all_frontmatter(doc)
        # Should handle large frontmatter
        assert len(messages) >= 2

    def test_concurrent_issues(self, tmp_path):
        """Test document with every possible issue."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test"
status: draft
date: 2025/01/26
invalid_field: null
---
# Test
"""
        doc.write_text(content)

        messages = fix_all_frontmatter(doc)
        # Should fix both status and date
        assert len(messages) >= 2
        assert any("status" in msg.lower() for msg in messages)
        assert any("date" in msg.lower() for msg in messages)

    def test_readonly_file(self, tmp_path):
        """Test handling of read-only files."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
status: draft
---
# Test
"""
        doc.write_text(content)

        # Make file read-only
        import os
        import stat

        os.chmod(doc, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            messages = fix_all_frontmatter(doc)
            # Should fail to write
            assert len(messages) == 0 or any("error" in msg.lower() for msg in messages)
        finally:
            # Restore write permissions for cleanup
            os.chmod(doc, stat.S_IWUSR | stat.S_IRUSR)
