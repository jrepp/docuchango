"""Comprehensive tests for tags fixes - positive, negative, and edge cases."""

from pathlib import Path

import frontmatter
import pytest

from docuchango.fixes.tags import fix_tags, normalize_tag


class TestNormalizeTagEdgeCases:
    """Edge case tests for single tag normalization."""

    def test_empty_string(self):
        """Test empty string tag."""
        assert normalize_tag("") == ""
        assert normalize_tag("   ") == ""

    def test_only_special_characters(self):
        """Test tags with only special characters."""
        assert normalize_tag("!!!") == ""
        assert normalize_tag("@#$%") == ""
        assert normalize_tag("---") == ""

    def test_unicode_characters(self):
        """Test Unicode characters in tags."""
        assert normalize_tag("café") == "caf"  # Special chars removed
        assert normalize_tag("日本語") == ""  # Non-Latin removed
        assert normalize_tag("Москва") == ""  # Cyrillic removed

    def test_mixed_separators(self):
        """Test tags with mixed separators."""
        assert normalize_tag("api__design--system") == "api-design-system"
        assert normalize_tag("foo _ bar - baz") == "foo-bar-baz"

    def test_numeric_tags(self):
        """Test tags with numbers."""
        assert normalize_tag("v2.0") == "v20"
        assert normalize_tag("python3") == "python3"
        assert normalize_tag("2023-Q1") == "2023-q1"

    def test_very_long_tags(self):
        """Test very long tag strings."""
        long_tag = "a" * 1000
        result = normalize_tag(long_tag)
        assert result == long_tag
        assert len(result) == 1000

    def test_tags_with_urls(self):
        """Test tags that look like URLs."""
        assert normalize_tag("https://example.com") == "httpsexamplecom"
        assert normalize_tag("api.v1.endpoint") == "apiv1endpoint"

    def test_mixed_case_with_numbers(self):
        """Test mixed case with numbers."""
        assert normalize_tag("API2Design") == "api2design"
        assert normalize_tag("v1.2.3") == "v123"

    def test_leading_numbers(self):
        """Test tags starting with numbers."""
        assert normalize_tag("2023-update") == "2023-update"
        assert normalize_tag("1st-release") == "1st-release"

    def test_emoji_in_tags(self):
        """Test tags with emoji."""
        assert normalize_tag("backend🔥") == "backend"
        assert normalize_tag("✨feature") == "feature"

    def test_whitespace_variations(self):
        """Test various whitespace characters."""
        assert normalize_tag("api\tdesign") == "api-design"
        assert normalize_tag("api\ndesign") == "api-design"
        assert normalize_tag("api\r\ndesign") == "api-design"


class TestFixTagsEdgeCases:
    """Edge case tests for fix_tags function."""

    def test_null_tags_field(self, tmp_path):
        """Test tags field set to null."""
        doc = tmp_path / "test.md"
        content = """---
id: test
tags: null
---
# Test
"""
        doc.write_text(content)

        changed, messages = fix_tags(doc)
        # Null is not a list
        assert not changed
        assert any("invalid type" in msg.lower() for msg in messages)

    def test_tags_as_dict(self, tmp_path):
        """Test tags field as dictionary."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\ntags:\n  backend: true\n---\n# Test")

        changed, messages = fix_tags(doc)
        assert not changed
        assert any("invalid type" in msg.lower() for msg in messages)

    def test_tags_with_mixed_types(self, tmp_path):
        """Test tags array with mixed types."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["backend", 123, true]\n---\n# Test')

        changed, messages = fix_tags(doc)
        # Should skip non-string tags
        assert changed
        assert any("Skipped non-string tag" in msg for msg in messages)

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["backend"]

    def test_very_large_tag_array(self, tmp_path):
        """Test array with many tags."""
        doc = tmp_path / "test.md"
        tags = [f"tag{i}" for i in range(1000)]
        tags_str = str(tags).replace("'", '"')
        doc.write_text(f"---\nid: test\ntags: {tags_str}\n---\n# Test")

        changed, messages = fix_tags(doc)
        # Should handle large arrays
        post = frontmatter.loads(doc.read_text())
        assert len(post.metadata["tags"]) == 1000

    def test_duplicate_tags_only(self, tmp_path):
        """Test array with only duplicates."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["backend", "backend", "backend"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["backend"]
        assert len(post.metadata["tags"]) == 1

    def test_empty_strings_in_array(self, tmp_path):
        """Test tags with empty strings."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["backend", "", "  ", "frontend"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        # Empty strings should be filtered out
        assert post.metadata["tags"] == ["backend", "frontend"]

    def test_tags_with_only_invalid_chars(self, tmp_path):
        """Test tags that become empty after normalization."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["!!!", "@@@", "###"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        # All tags become empty, should result in empty array
        assert post.metadata["tags"] == []

    def test_case_variations_of_same_tag(self, tmp_path):
        """Test multiple case variations of same tag."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["API", "Api", "api", "aPi"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        # Should normalize to one
        assert post.metadata["tags"] == ["api"]

    def test_tags_with_complex_normalization(self, tmp_path):
        """Test tags requiring multiple normalization steps."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["  API___DESIGN  ", "api-design", "api__design"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        # All normalize to same tag
        assert post.metadata["tags"] == ["api-design"]

    def test_file_without_frontmatter(self, tmp_path):
        """Test file with no frontmatter at all."""
        doc = tmp_path / "test.md"
        doc.write_text("# Just a heading\n\nSome content.")

        changed, messages = fix_tags(doc)
        assert not changed
        assert any("No frontmatter" in msg for msg in messages)

    def test_file_with_incomplete_frontmatter(self, tmp_path):
        """Test file with incomplete frontmatter."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\n# Missing closing")

        # Should fail to parse
        changed, messages = fix_tags(doc)
        assert not changed

    def test_special_yaml_values(self, tmp_path):
        """Test tags with special YAML values."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["yes", "no", "true", "false", "on", "off"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        # Should treat as strings, not booleans
        expected = sorted(["false", "no", "off", "on", "true", "yes"])
        assert post.metadata["tags"] == expected

    def test_tags_already_perfect(self, tmp_path):
        """Test tags that need no changes."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["api", "backend", "frontend"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert not changed
        assert len(messages) == 0

    def test_single_tag_array(self, tmp_path):
        """Test array with single tag."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["Backend"]\n---\n# Test')

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["backend"]

    def test_multiline_tags_array(self, tmp_path):
        """Test tags in multiline YAML format."""
        doc = tmp_path / "test.md"
        content = """---
id: test
tags:
  - Backend
  - API Design
  - frontend
---
# Test
"""
        doc.write_text(content)

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["api-design", "backend", "frontend"]

    def test_tags_with_quotes(self, tmp_path):
        """Test tags with embedded quotes."""
        doc = tmp_path / "test.md"
        doc.write_text("""---
id: test
tags: ['backend', "frontend", api]
---
# Test
""")

        changed, messages = fix_tags(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        assert "api" in post.metadata["tags"]
        assert "backend" in post.metadata["tags"]
        assert "frontend" in post.metadata["tags"]
