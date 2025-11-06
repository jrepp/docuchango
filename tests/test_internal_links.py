"""Tests for internal_links.py fix module."""

from docuchango.fixes.internal_links import fix_links_in_content, fix_links_in_file, process_directory


class TestInternalLinksContent:
    """Test content-level link fixing."""

    def test_fix_rfc_link_with_date_prefix(self):
        """Test removing date prefix from RFC link."""
        content = "[RFC](../rfcs/2025-10-13-rfc-001-test.md)"
        fixed, count = fix_links_in_content(content)
        assert count == 1
        assert "[RFC](../rfcs/rfc-001-test.md)" in fixed
        assert "2025-10-13" not in fixed

    def test_fix_adr_link_with_date_prefix(self):
        """Test removing date prefix from ADR link."""
        content = "[ADR](./2025-10-15-adr-003-decision.md)"
        fixed, count = fix_links_in_content(content)
        assert count == 1
        assert "[ADR](./adr-003-decision.md)" in fixed
        assert "2025-10-15" not in fixed

    def test_fix_memo_link_with_date_prefix(self):
        """Test removing date prefix from MEMO link."""
        content = "[Memo](../memos/2025-11-01-memo-005-note.md)"
        fixed, count = fix_links_in_content(content)
        assert count == 1
        assert "[Memo](../memos/memo-005-note.md)" in fixed

    def test_fix_link_without_directory_prefix(self):
        """Test link without directory path."""
        content = "[Link](2025-10-13-rfc-001-test.md)"
        fixed, count = fix_links_in_content(content)
        assert count == 1
        assert "[Link](rfc-001-test.md)" in fixed

    def test_fix_link_with_anchor(self):
        """Test link with URL anchor preserved."""
        content = "[Link](../rfcs/2025-10-13-rfc-001-test.md#section)"
        fixed, count = fix_links_in_content(content)
        assert count == 1
        assert "[Link](../rfcs/rfc-001-test.md#section)" in fixed
        assert "#section" in fixed

    def test_multiple_links_in_content(self):
        """Test fixing multiple links."""
        content = """[RFC 1](2025-10-13-rfc-001-test.md)
[RFC 2](../rfcs/2025-10-14-rfc-002-other.md)
[ADR](./2025-10-15-adr-003-decision.md)"""
        fixed, count = fix_links_in_content(content)
        assert count == 3
        assert "rfc-001-test.md" in fixed
        assert "rfc-002-other.md" in fixed
        assert "adr-003-decision.md" in fixed
        assert "2025-10" not in fixed

    def test_no_changes_needed(self):
        """Test content with no date-prefixed links."""
        content = "[Already correct](../rfcs/rfc-001-test.md)"
        fixed, count = fix_links_in_content(content)
        assert count == 0
        assert fixed == content

    def test_preserve_link_text(self):
        """Test that link text is preserved."""
        content = "[My Important RFC Document](2025-10-13-rfc-001-test.md)"
        fixed, count = fix_links_in_content(content)
        assert "[My Important RFC Document]" in fixed

    def test_preserve_non_doc_links(self):
        """Test that non-document links are preserved."""
        content = """[External](https://example.com)
[RFC](2025-10-13-rfc-001-test.md)
[Image](./image.png)"""
        fixed, count = fix_links_in_content(content)
        assert count == 1  # Only RFC link fixed
        assert "https://example.com" in fixed
        assert "./image.png" in fixed

    def test_different_date_formats(self):
        """Test various date formats."""
        content = """[Link1](2025-01-01-rfc-001-test.md)
[Link2](2025-12-31-adr-999-test.md)"""
        fixed, count = fix_links_in_content(content)
        assert count == 2
        assert "rfc-001-test.md" in fixed
        assert "adr-999-test.md" in fixed

    def test_complex_paths(self):
        """Test complex relative paths."""
        content = "[Link](../../rfcs/2025-10-13-rfc-001-test.md)"
        fixed, count = fix_links_in_content(content)
        assert count == 1
        assert "[Link](../../rfcs/rfc-001-test.md)" in fixed

    def test_unicode_in_link_text(self):
        """Test Unicode characters in link text."""
        content = "[RFC → ✓](2025-10-13-rfc-001-test.md)"
        fixed, count = fix_links_in_content(content)
        assert count == 1
        assert "→" in fixed
        assert "✓" in fixed

    def test_multiple_anchors(self):
        """Test links with different anchors."""
        content = """[Link1](2025-10-13-rfc-001-test.md#intro)
[Link2](2025-10-13-rfc-001-test.md#conclusion)"""
        fixed, count = fix_links_in_content(content)
        assert count == 2
        assert "rfc-001-test.md#intro" in fixed
        assert "rfc-001-test.md#conclusion" in fixed


class TestInternalLinksFile:
    """Test file-level link fixing."""

    def test_fix_links_in_file(self, tmp_path):
        """Test fixing links in a file."""
        test_file = tmp_path / "test.md"
        content = "[RFC](2025-10-13-rfc-001-test.md)"
        test_file.write_text(content, encoding="utf-8")

        fixes = fix_links_in_file(test_file, dry_run=False)
        assert fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "rfc-001-test.md" in result
        assert "2025-10-13" not in result

    def test_dry_run_mode(self, tmp_path, capsys):
        """Test dry-run mode doesn't modify files."""
        test_file = tmp_path / "test.md"
        content = "[RFC](2025-10-13-rfc-001-test.md)"
        test_file.write_text(content, encoding="utf-8")

        fixes = fix_links_in_file(test_file, dry_run=True)
        assert fixes == 1

        # File should not be modified
        result = test_file.read_text(encoding="utf-8")
        assert result == content
        assert "2025-10-13" in result

        # Should print dry-run message
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_no_changes_in_file(self, tmp_path):
        """Test file with no changes needed."""
        test_file = tmp_path / "test.md"
        content = "[RFC](rfc-001-test.md)"
        test_file.write_text(content, encoding="utf-8")

        fixes = fix_links_in_file(test_file, dry_run=False)
        assert fixes == 0

    def test_error_handling_nonexistent_file(self, tmp_path, capsys):
        """Test error handling for nonexistent file."""
        test_file = tmp_path / "nonexistent.md"

        fixes = fix_links_in_file(test_file, dry_run=False)
        assert fixes == 0

        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_unicode_content_preserved(self, tmp_path):
        """Test Unicode content is preserved."""
        test_file = tmp_path / "test.md"
        content = """# Title → ✓

[RFC](2025-10-13-rfc-001-test.md)

Content: 中文 ✗
"""
        test_file.write_text(content, encoding="utf-8")

        fix_links_in_file(test_file, dry_run=False)
        result = test_file.read_text(encoding="utf-8")

        assert "→" in result
        assert "✓" in result
        assert "中文" in result
        assert "✗" in result

    def test_empty_file(self, tmp_path):
        """Test empty file handling."""
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding="utf-8")

        fixes = fix_links_in_file(test_file, dry_run=False)
        assert fixes == 0


class TestInternalLinksDirectory:
    """Test directory-level processing."""

    def test_process_directory(self, tmp_path):
        """Test processing multiple files in directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create files with links to fix
        file1 = docs_dir / "file1.md"
        file1.write_text("[RFC](2025-10-13-rfc-001-test.md)", encoding="utf-8")

        file2 = docs_dir / "file2.md"
        file2.write_text("[ADR](2025-10-15-adr-003-decision.md)", encoding="utf-8")

        stats = process_directory(docs_dir, dry_run=False)

        assert stats["files_checked"] == 2
        assert stats["files_modified"] == 2
        assert stats["total_fixes"] == 2

    def test_process_directory_skips_readme(self, tmp_path):
        """Test that README.md is skipped."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        readme = docs_dir / "README.md"
        readme.write_text("[Link](2025-10-13-rfc-001-test.md)", encoding="utf-8")

        stats = process_directory(docs_dir, dry_run=False)

        assert stats["files_checked"] == 0
        # README should be skipped
        assert "2025-10-13" in readme.read_text(encoding="utf-8")

    def test_process_directory_skips_templates(self, tmp_path):
        """Test that template files are skipped."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        template = docs_dir / "template-doc.md"
        template.write_text("[Link](2025-10-13-rfc-001-test.md)", encoding="utf-8")

        stats = process_directory(docs_dir, dry_run=False)

        assert stats["files_checked"] == 0

    def test_process_directory_recursive(self, tmp_path):
        """Test recursive directory processing."""
        docs_dir = tmp_path / "docs"
        sub_dir = docs_dir / "subfolder"
        sub_dir.mkdir(parents=True)

        file1 = docs_dir / "file1.md"
        file1.write_text("[RFC](2025-10-13-rfc-001-test.md)", encoding="utf-8")

        file2 = sub_dir / "file2.md"
        file2.write_text("[ADR](2025-10-15-adr-003-decision.md)", encoding="utf-8")

        stats = process_directory(docs_dir, dry_run=False)

        assert stats["files_checked"] == 2
        assert stats["files_modified"] == 2

    def test_process_nonexistent_directory(self, tmp_path):
        """Test processing nonexistent directory."""
        docs_dir = tmp_path / "nonexistent"

        stats = process_directory(docs_dir, dry_run=False)

        assert stats["files_checked"] == 0
        assert stats["files_modified"] == 0
        assert stats["total_fixes"] == 0

    def test_process_directory_mixed_files(self, tmp_path):
        """Test directory with mix of files needing and not needing fixes."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Needs fix
        file1 = docs_dir / "file1.md"
        file1.write_text("[RFC](2025-10-13-rfc-001-test.md)", encoding="utf-8")

        # Already correct
        file2 = docs_dir / "file2.md"
        file2.write_text("[RFC](rfc-002-test.md)", encoding="utf-8")

        # No links
        file3 = docs_dir / "file3.md"
        file3.write_text("# Just text", encoding="utf-8")

        stats = process_directory(docs_dir, dry_run=False)

        assert stats["files_checked"] == 3
        assert stats["files_modified"] == 1
        assert stats["total_fixes"] == 1

    def test_process_directory_dry_run(self, tmp_path):
        """Test directory processing in dry-run mode."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        file1 = docs_dir / "file1.md"
        content = "[RFC](2025-10-13-rfc-001-test.md)"
        file1.write_text(content, encoding="utf-8")

        stats = process_directory(docs_dir, dry_run=True)

        assert stats["files_modified"] == 1
        # File should not be modified in dry-run
        assert file1.read_text(encoding="utf-8") == content
