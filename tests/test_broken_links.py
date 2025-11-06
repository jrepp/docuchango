"""Tests for broken_links.py fix module."""

from docuchango.fixes.broken_links import fix_links_in_file


class TestBrokenLinksFixes:
    """Test broken links fixing functionality."""

    def test_fix_rfc_full_filename_to_short_id(self, tmp_path):
        """Test converting RFC full filename to short ID."""
        test_file = tmp_path / "test.md"
        content = """[RFC](/rfc/rfc-001-test-decision)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/rfc/rfc-001" in result
        assert "test-decision" not in result

    def test_fix_adr_full_filename_to_short_id(self, tmp_path):
        """Test converting ADR full filename to short ID."""
        test_file = tmp_path / "test.md"
        content = """[ADR](/adr/adr-042-database-migration)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-042" in result
        assert "database-migration" not in result

    def test_fix_memo_full_filename_to_short_id(self, tmp_path):
        """Test converting memo full filename to short ID."""
        test_file = tmp_path / "test.md"
        content = """[Memo](/memos/memo-123-important-note)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/memos/memo-123" in result
        assert "important-note" not in result

    def test_remove_prism_data_layer_prefix(self, tmp_path):
        """Test removing /prism-data-layer prefix."""
        test_file = tmp_path / "test.md"
        content = """[Link](/prism-data-layer/adr/adr-001)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-001" in result
        assert "prism-data-layer" not in result

    def test_fix_netflix_abstractions_link(self, tmp_path):
        """Test fixing Netflix abstractions link."""
        test_file = tmp_path / "test.md"
        content = """[Netflix](/netflix/abstractions)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/netflix/netflix-abstractions" in result

    def test_fix_multiple_links_in_file(self, tmp_path):
        """Test fixing multiple links in one file."""
        test_file = tmp_path / "test.md"
        content = """# Document

[RFC 1](/rfc/rfc-001-test)
[RFC 2](/rfc/rfc-002-another)
[ADR](/adr/adr-010-decision)
"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 3

        result = test_file.read_text(encoding="utf-8")
        assert "/rfc/rfc-001" in result
        assert "/rfc/rfc-002" in result
        assert "/adr/adr-010" in result

    def test_no_changes_needed(self, tmp_path):
        """Test file with no broken links."""
        test_file = tmp_path / "test.md"
        content = """[Already correct](/rfc/rfc-001)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 0

    def test_dry_run_mode(self, tmp_path, capsys):
        """Test dry-run mode doesn't modify files."""
        test_file = tmp_path / "test.md"
        content = """[RFC](/rfc/rfc-001-test)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=True)
        assert changes == 1

        # File should not be modified
        result = test_file.read_text(encoding="utf-8")
        assert result == content
        assert "test" in result

        # Should print message
        captured = capsys.readouterr()
        assert "Would fix" in captured.out

    def test_error_handling_nonexistent_file(self, tmp_path, capsys):
        """Test error handling for nonexistent files."""
        test_file = tmp_path / "nonexistent.md"

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 0

        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_fix_rfc_211_to_021(self, tmp_path):
        """Test fixing incorrectly converted RFC number."""
        test_file = tmp_path / "test.md"
        content = """[RFC 211](/rfc/rfc-211) is wrong"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/rfc/rfc-021" in result
        assert "rfc-211" not in result

    def test_fix_relative_rfc_link(self, tmp_path):
        """Test fixing relative RFC links."""
        test_file = tmp_path / "test.md"
        content = """[RFC](./RFC-001-test)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/rfc/rfc-001" in result

    def test_fix_prism_data_layer_rfc(self, tmp_path):
        """Test fixing prism-data-layer RFC paths."""
        test_file = tmp_path / "test.md"
        content = """[RFC](/prism-data-layer/rfc/rfc-005-example)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        # May apply multiple overlapping patterns
        assert changes >= 1

        result = test_file.read_text(encoding="utf-8")
        assert "/rfc/rfc-005" in result
        assert "prism-data-layer" not in result

    def test_fix_prism_data_layer_adr(self, tmp_path):
        """Test fixing prism-data-layer ADR paths."""
        test_file = tmp_path / "test.md"
        content = """[ADR](/prism-data-layer/adr/adr-999-test)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        # May apply multiple overlapping patterns
        assert changes >= 1

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-999" in result

    def test_fix_netflix_write_ahead_log(self, tmp_path):
        """Test fixing Netflix write-ahead-log link."""
        test_file = tmp_path / "test.md"
        content = """[WAL](/netflix/write-ahead-log)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/netflix/netflix-write-ahead-log" in result

    def test_fix_netflix_scale(self, tmp_path):
        """Test fixing Netflix scale link."""
        test_file = tmp_path / "test.md"
        content = """[Scale](/netflix/scale)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/netflix/netflix-scale" in result

    def test_unicode_content_preserved(self, tmp_path):
        """Test that Unicode content is preserved."""
        test_file = tmp_path / "test.md"
        content = """# Title → ✓

[RFC](/rfc/rfc-001-test)

Special: 中文 ✗
"""
        test_file.write_text(content, encoding="utf-8")

        fix_links_in_file(test_file, dry_run=False)
        result = test_file.read_text(encoding="utf-8")

        # Unicode should be preserved
        assert "→" in result
        assert "✓" in result
        assert "中文" in result
        assert "✗" in result

    def test_multiple_same_pattern_fixes(self, tmp_path):
        """Test fixing multiple occurrences of same pattern."""
        test_file = tmp_path / "test.md"
        content = """[RFC 1](/rfc/rfc-001-alpha)
[RFC 2](/rfc/rfc-001-beta)
[RFC 3](/rfc/rfc-001-gamma)
"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 3

        result = test_file.read_text(encoding="utf-8")
        # All should be fixed to same short form
        assert result.count("/rfc/rfc-001") == 3

    def test_fix_key_documents_path(self, tmp_path):
        """Test fixing prism-data-layer key-documents path."""
        test_file = tmp_path / "test.md"
        content = """[Docs](/prism-data-layer/key-documents)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/key-documents" in result
        assert "prism-data-layer" not in result

    def test_fix_prd_path(self, tmp_path):
        """Test fixing prism-data-layer PRD path."""
        test_file = tmp_path / "test.md"
        content = """[PRD](/prism-data-layer/prd)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/prd" in result
        assert "prism-data-layer" not in result

    def test_preserves_link_text(self, tmp_path):
        """Test that link text is preserved."""
        test_file = tmp_path / "test.md"
        content = """[My Important RFC Document](/rfc/rfc-123-long-title)"""
        test_file.write_text(content, encoding="utf-8")

        fix_links_in_file(test_file, dry_run=False)
        result = test_file.read_text(encoding="utf-8")

        # Link text should be unchanged
        assert "[My Important RFC Document]" in result
        # But URL should be fixed
        assert "/rfc/rfc-123)" in result

    def test_case_insensitive_rfc_fix(self, tmp_path):
        """Test fixing RFC links with uppercase."""
        test_file = tmp_path / "test.md"
        content = """[RFC](/prism-data-layer/rfc/RFC-042-test)"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 1

        result = test_file.read_text(encoding="utf-8")
        # Should be lowercased
        assert "/rfc/rfc-042" in result.lower()

    def test_empty_file(self, tmp_path):
        """Test handling of empty file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 0

    def test_file_without_links(self, tmp_path):
        """Test file without any links."""
        test_file = tmp_path / "test.md"
        content = """# Title

Just plain text, no links here.
"""
        test_file.write_text(content, encoding="utf-8")

        changes = fix_links_in_file(test_file, dry_run=False)
        assert changes == 0
