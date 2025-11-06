"""Tests for doc_links.py fix module."""

from docuchango.fixes.doc_links import fix_links_in_file


class TestDocLinksRelative:
    """Test relative link conversions."""

    def test_fix_adr_relative_current_dir(self, tmp_path):
        """Test converting ./ADR-XXX.md to absolute path."""
        test_file = tmp_path / "test.md"
        content = "[ADR](./ADR-001-decision.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1
        assert case_fixes == 0

        result = test_file.read_text(encoding="utf-8")
        assert "[ADR](/adr/adr-001)" in result
        assert "./ADR-001" not in result

    def test_fix_adr_relative_parent_dir(self, tmp_path):
        """Test converting ../adr/ADR-XXX.md to absolute path."""
        test_file = tmp_path / "test.md"
        content = "[ADR](../adr/ADR-002-decision.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1
        assert case_fixes == 0

        result = test_file.read_text(encoding="utf-8")
        assert "[ADR](/adr/adr-002)" in result

    def test_fix_rfc_relative_current_dir(self, tmp_path):
        """Test converting ./RFC-XXX.md to absolute path."""
        test_file = tmp_path / "test.md"
        content = "[RFC](./RFC-001-proposal.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[RFC](/rfc/rfc-001)" in result

    def test_fix_rfc_relative_with_rfcs_dir(self, tmp_path):
        """Test converting ../rfcs/RFC-XXX.md to absolute path."""
        test_file = tmp_path / "test.md"
        content = "[RFC](../rfcs/RFC-002-proposal.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[RFC](/rfc/rfc-002)" in result

    def test_fix_rfc_relative_with_rfc_dir(self, tmp_path):
        """Test converting ../rfc/RFC-XXX.md to absolute path."""
        test_file = tmp_path / "test.md"
        content = "[RFC](../rfc/RFC-003-proposal.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[RFC](/rfc/rfc-003)" in result

    def test_fix_memo_relative_current_dir(self, tmp_path):
        """Test converting ./MEMO-XXX.md to absolute path."""
        test_file = tmp_path / "test.md"
        content = "[Memo](./MEMO-001-note.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[Memo](/memos/memo-001)" in result

    def test_fix_memo_relative_with_memos_dir(self, tmp_path):
        """Test converting ../memos/MEMO-XXX.md to absolute path."""
        test_file = tmp_path / "test.md"
        content = "[Memo](../memos/MEMO-002-note.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[Memo](/memos/memo-002)" in result


class TestDocLinksCase:
    """Test case fixing in absolute links."""

    def test_fix_adr_case(self, tmp_path):
        """Test fixing uppercase ADR in absolute path."""
        test_file = tmp_path / "test.md"
        content = "[ADR](/adr/ADR-001)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 0
        assert case_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[ADR](/adr/adr-001)" in result
        assert "ADR-001" not in result

    def test_fix_rfc_case(self, tmp_path):
        """Test fixing uppercase RFC in absolute path."""
        test_file = tmp_path / "test.md"
        content = "[RFC](/rfc/RFC-001)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 0
        assert case_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[RFC](/rfc/rfc-001)" in result

    def test_fix_memo_case(self, tmp_path):
        """Test fixing uppercase MEMO in absolute path."""
        test_file = tmp_path / "test.md"
        content = "[Memo](/memos/MEMO-001)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 0
        assert case_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "[Memo](/memos/memo-001)" in result


class TestDocLinksCombined:
    """Test combined and edge case scenarios."""

    def test_multiple_relative_links(self, tmp_path):
        """Test multiple relative links in one file."""
        test_file = tmp_path / "test.md"
        content = """[ADR 1](./ADR-001-decision.md)
[RFC 1](./RFC-001-proposal.md)
[Memo 1](./MEMO-001-note.md)"""
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 3
        assert case_fixes == 0

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-001" in result
        assert "/rfc/rfc-001" in result
        assert "/memos/memo-001" in result

    def test_multiple_case_fixes(self, tmp_path):
        """Test multiple case fixes in one file."""
        test_file = tmp_path / "test.md"
        content = """[ADR](/adr/ADR-001)
[RFC](/rfc/RFC-001)
[Memo](/memos/MEMO-001)"""
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 0
        assert case_fixes == 3

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-001" in result
        assert "/rfc/rfc-001" in result
        assert "/memos/memo-001" in result

    def test_both_relative_and_case_fixes(self, tmp_path):
        """Test both relative and case fixes in same file."""
        test_file = tmp_path / "test.md"
        content = """[ADR 1](./ADR-001-decision.md)
[ADR 2](/adr/ADR-002)"""
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1
        assert case_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-001" in result
        assert "/adr/adr-002" in result

    def test_no_changes_needed(self, tmp_path):
        """Test file with already correct links."""
        test_file = tmp_path / "test.md"
        content = "[ADR](/adr/adr-001)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 0
        assert case_fixes == 0

        # File should not be modified
        result = test_file.read_text(encoding="utf-8")
        assert result == content

    def test_preserve_link_text(self, tmp_path):
        """Test that link text is preserved."""
        test_file = tmp_path / "test.md"
        content = "[My Important ADR Document](./ADR-001-decision.md)"
        test_file.write_text(content, encoding="utf-8")

        fix_links_in_file(test_file)

        result = test_file.read_text(encoding="utf-8")
        assert "[My Important ADR Document](/adr/adr-001)" in result

    def test_preserve_other_links(self, tmp_path):
        """Test that non-ADR/RFC/MEMO links are preserved."""
        test_file = tmp_path / "test.md"
        content = """[External](https://example.com)
[ADR](./ADR-001-decision.md)
[Image](./image.png)"""
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "https://example.com" in result
        assert "./image.png" in result

    def test_unicode_content_preserved(self, tmp_path):
        """Test Unicode content is preserved."""
        test_file = tmp_path / "test.md"
        content = """# Title → ✓

[ADR](./ADR-001-decision.md)

Content: 中文 ✗
"""
        test_file.write_text(content, encoding="utf-8")

        fix_links_in_file(test_file)
        result = test_file.read_text(encoding="utf-8")

        assert "→" in result
        assert "✓" in result
        assert "中文" in result
        assert "✗" in result

    def test_empty_file(self, tmp_path):
        """Test empty file handling."""
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 0
        assert case_fixes == 0

    def test_three_digit_numbers(self, tmp_path):
        """Test ADR/RFC/MEMO with three-digit numbers."""
        test_file = tmp_path / "test.md"
        content = """[ADR](./ADR-123-decision.md)
[RFC](/rfc/RFC-999)
[Memo](../memos/MEMO-500-note.md)"""
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 2
        assert case_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-123" in result
        assert "/rfc/rfc-999" in result
        assert "/memos/memo-500" in result

    def test_file_with_long_names(self, tmp_path):
        """Test files with long descriptive names."""
        test_file = tmp_path / "test.md"
        content = "[ADR](./ADR-001-very-long-decision-name-with-many-words.md)"
        test_file.write_text(content, encoding="utf-8")

        relative_fixes, case_fixes = fix_links_in_file(test_file)
        assert relative_fixes == 1

        result = test_file.read_text(encoding="utf-8")
        assert "/adr/adr-001" in result
        # Long name should be stripped
        assert "very-long-decision" not in result
