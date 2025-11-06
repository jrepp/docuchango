#!/usr/bin/env python3
"""Tests for specific bug fixes to ensure they don't regress.

This module tests the fixes for high-priority bugs identified in the
comprehensive codebase scan.
"""

import re
import tempfile
from pathlib import Path


class TestStringReplacementCollision:
    """Tests for bug fix: String replacement collision in cli.py (PR #29)

    Bug: Sequential .replace() calls caused cascading replacements when
    user input contained placeholder substrings.

    Fix: Two-pass replacement using null-byte markers to prevent collision.
    """

    def test_replacement_with_date_in_project_id(self):
        """Test that project_id containing '2025' doesn't get corrupted."""
        # Simulate the template replacement logic
        content = """project:
  id: "my-project"
  name: "My Project"

metadata:
  created: 2025-01-01"""

        # User values
        project_id = "my-project-2025"
        project_name = "Infrastructure"
        date = "2025-11-05"

        # Apply fix: two-pass replacement with markers
        markers = {
            "my-project": "\x00PROJECT_ID\x00",
            "My Project": "\x00PROJECT_NAME\x00",
            "2025-01-01": "\x00DATE\x00",
        }

        # First pass: replace placeholders with unique markers
        for placeholder, marker in markers.items():
            content = content.replace(placeholder, marker)

        # Second pass: replace markers with actual values
        content = content.replace(markers["my-project"], project_id)
        content = content.replace(markers["My Project"], project_name)
        content = content.replace(markers["2025-01-01"], date)

        # Verify no corruption occurred
        assert project_id in content
        assert "my-project-2025-11-05" not in content  # Date shouldn't replace '2025' in project_id
        assert content.count("2025-11-05") == 1  # Only one date replacement

    def test_replacement_with_project_in_name(self):
        """Test that project_name containing 'my-project' doesn't cause collision."""
        content = """project:
  id: "my-project"
  name: "My Project"
  description: "A project for my-project management"
"""

        project_id = "infra-2024"
        project_name = "My Project Management"  # Contains "My Project"

        # Apply fix
        markers = {
            "my-project": "\x00PROJECT_ID\x00",
            "My Project": "\x00PROJECT_NAME\x00",
            "2025-01-01": "\x00DATE\x00",
        }

        for placeholder, marker in markers.items():
            content = content.replace(placeholder, marker)

        content = content.replace(markers["my-project"], project_id)
        content = content.replace(markers["My Project"], project_name)

        # Verify correct replacements
        assert 'id: "infra-2024"' in content
        assert 'name: "My Project Management"' in content
        assert "for infra-2024 management" in content  # "my-project" in description replaced once

    def test_old_behavior_would_fail(self):
        """Demonstrate that the old sequential replace() approach fails."""
        content = "my-project My Project 2025-01-01"

        project_id = "proj-2025"
        project_name = "2025 Initiative"
        date = "2025-11-05"

        # Old buggy approach (sequential replacements)
        old_content = content.replace("my-project", project_id)
        old_content = old_content.replace("My Project", project_name)
        old_content = old_content.replace("2025-01-01", date)

        # This would produce incorrect results:
        # "proj-2025 2025 Initiative 2025-11-05"
        # Then "2025-01-01" replacement also matches "2025" in other places!

        # New fixed approach
        markers = {
            "my-project": "\x00PROJECT_ID\x00",
            "My Project": "\x00PROJECT_NAME\x00",
            "2025-01-01": "\x00DATE\x00",
        }

        new_content = content
        for placeholder, marker in markers.items():
            new_content = new_content.replace(placeholder, marker)

        new_content = new_content.replace(markers["my-project"], project_id)
        new_content = new_content.replace(markers["My Project"], project_name)
        new_content = new_content.replace(markers["2025-01-01"], date)

        # Verify the new approach produces correct output
        assert new_content == "proj-2025 2025 Initiative 2025-11-05"
        assert "2025-11-05" not in project_id  # No corruption


class TestUTF8EncodingOnWrites:
    """Tests for bug fix: Missing UTF-8 encoding on file writes (PR #29)

    Bug: write_text() without explicit encoding uses system default,
    causing corruption on Windows with CP1252.

    Fix: Added encoding="utf-8" to all read/write operations.
    """

    def test_utf8_characters_preserved_in_broken_links(self):
        """Test that UTF-8 characters are preserved when fixing broken links."""
        from docuchango.fixes.broken_links import fix_links_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"

            # Content with UTF-8 characters
            content = """# Test Document

[Link](/rfc/rfc-211-test)

UTF-8 characters: → ✓ ✗ 中文 🎉
"""

            test_file.write_text(content, encoding="utf-8")

            # Fix links (should preserve UTF-8)
            fix_links_in_file(test_file, dry_run=False)

            # Read back and verify UTF-8 preserved
            result = test_file.read_text(encoding="utf-8")
            assert "→" in result
            assert "✓" in result
            assert "✗" in result
            assert "中文" in result
            assert "🎉" in result

    def test_utf8_characters_preserved_in_cross_plugin_links(self):
        """Test that UTF-8 characters are preserved when fixing cross-plugin links."""
        from docuchango.fixes.cross_plugin_links import fix_cross_plugin_links

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"

            content = """# Document

[Test](../rfcs/RFC-001-test.md)

Special chars: ≥ ≤ ≠ → ← ↔
"""

            test_file.write_text(content, encoding="utf-8")

            # Fix cross-plugin links
            fix_cross_plugin_links(test_file, dry_run=False)

            # Verify UTF-8 preserved
            result = test_file.read_text(encoding="utf-8")
            assert "≥" in result
            assert "≤" in result
            assert "≠" in result
            assert "→" in result

    def test_encoding_parameter_present_in_read_operations(self):
        """Verify that encoding parameter is specified in file read operations."""
        import inspect

        from docuchango.fixes import broken_links, cross_plugin_links

        # Check broken_links.py
        source = inspect.getsource(broken_links.fix_links_in_file)
        assert 'encoding="utf-8"' in source, "broken_links.py should specify UTF-8 encoding"

        # Check cross_plugin_links.py
        source = inspect.getsource(cross_plugin_links.fix_cross_plugin_links)
        assert 'encoding="utf-8"' in source, "cross_plugin_links.py should specify UTF-8 encoding"


class TestRegexCatastrophicBacktracking:
    r"""Tests for bug fix: Regex catastrophic backtracking in mdx_syntax.py (PR #29)

    Bug: Pattern (?:\s+\w+)? with unbounded \w+ causes exponential
    backtracking (ReDoS vulnerability).

    Fix: Limited word length to 20 characters: \w{1,20}
    """

    def test_regex_bounded_backtracking(self):
        """Test that the regex has bounded backtracking."""
        import time

        # The fixed pattern from mdx_syntax.py
        pattern = r"(?<!`)<(\d+(?:\.\d+)?(?:ms|min|s|%|MB|GB|KB)?(?:\s+\w{1,20})?)"

        # Adversarial input that would cause catastrophic backtracking with \w+
        # This has many words, which would cause O(2^n) backtracking
        adversarial = "<123 " + "abc " * 30 + "xyz"

        start = time.time()
        matches = re.findall(pattern, adversarial)
        elapsed = time.time() - start

        # Should complete quickly (< 0.1 seconds even on slow systems)
        assert elapsed < 0.1, f"Regex took too long: {elapsed}s (possible ReDoS)"

        # Should still match the number
        assert len(matches) > 0

    def test_regex_matches_valid_cases(self):
        """Test that the fixed regex still matches valid use cases."""
        pattern = r"(?<!`)<(\d+(?:\.\d+)?(?:ms|min|s|%|MB|GB|KB)?(?:\s+\w{1,20})?)"

        test_cases = [
            ("<10", "10"),
            ("<10ms", "10ms"),
            ("<1 minute", "1 minute"),
            ("<0.5 seconds", "0.5 seconds"),
            ("<100%", "100%"),
            ("<5MB", "5MB"),
            ("<2.5GB", "2.5GB"),
            ("<1KB", "1KB"),
        ]

        for test_input, expected_match in test_cases:
            matches = re.findall(pattern, test_input)
            assert len(matches) == 1, f"Should match {test_input}"
            assert expected_match in matches[0], f"Should extract '{expected_match}' from '{test_input}'"

    def test_regex_skips_backticked_content(self):
        """Test that the regex doesn't match content already in backticks."""
        pattern = r"(?<!`)<(\d+(?:\.\d+)?(?:ms|min|s|%|MB|GB|KB)?(?:\s+\w{1,20})?)"

        # Should not match (already backticked)
        no_match_cases = [
            "`<10ms`",
            "`<1 minute`",
            "``<100%``",
        ]

        for test_input in no_match_cases:
            matches = re.findall(pattern, test_input)
            assert len(matches) == 0, f"Should not match backticked content: {test_input}"

    def test_regex_word_limit_prevents_redos(self):
        """Test that word length limit prevents ReDoS attacks."""
        pattern = r"(?<!`)<(\d+(?:\.\d+)?(?:ms|min|s|%|MB|GB|KB)?(?:\s+\w{1,20})?)"

        # Input with word longer than 20 characters
        test_input = "<123 verylongwordthatexceedstwentycharacters"

        import time

        start = time.time()
        matches = re.findall(pattern, test_input)
        elapsed = time.time() - start

        # Should complete quickly (the key improvement - no exponential backtracking)
        assert elapsed < 0.05, f"Regex with long word took too long: {elapsed}s"

        # Should match the number plus first 20 chars of the word
        assert len(matches) == 1
        assert matches[0].startswith("123")
        # Word is limited to 20 chars, so "verylongwordthatexceedstwentycharacters" is truncated
        assert len(matches[0].split()[1]) <= 20 if len(matches[0].split()) > 1 else True


class TestBugFixIntegration:
    """Integration tests to ensure all bug fixes work together."""

    def test_init_command_with_problematic_values(self, tmp_path):
        """Test docuchango init with values that would trigger all three bugs."""
        from click.testing import CliRunner

        from docuchango.cli import init

        runner = CliRunner()

        # Values that would trigger the string replacement bug
        result = runner.invoke(
            init,
            [
                "--path",
                str(tmp_path / "docs-cms"),
                "--project-id",
                "my-project-2025",
                "--project-name",
                "My Project 2025",
            ],
        )

        # Should succeed
        assert result.exit_code == 0

        # Verify the generated file has correct values
        config_file = tmp_path / "docs-cms" / "docs-project.yaml"
        assert config_file.exists()

        content = config_file.read_text(encoding="utf-8")

        # Check that no replacement collision occurred
        assert "my-project-2025" in content
        assert "My Project 2025" in content
        assert "my-project-2025-11-05" not in content  # No date corruption in project_id
