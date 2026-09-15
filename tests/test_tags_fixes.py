"""Tests for tags normalization fixes."""

import frontmatter
import pytest

from docuchango.fixes.tags import fix_tags, normalize_tag


class TestNormalizeTag:
    """Test single tag normalization."""

    def test_lowercase_conversion(self):
        """Test converting tags to lowercase."""
        assert normalize_tag("Backend") == "backend"
        assert normalize_tag("API") == "api"
        assert normalize_tag("FRONTEND") == "frontend"

    def test_space_to_dash(self):
        """Test converting spaces to dashes."""
        assert normalize_tag("API Design") == "api-design"
        assert normalize_tag("Machine Learning") == "machine-learning"

    def test_underscore_to_dash(self):
        """Test converting underscores to dashes."""
        assert normalize_tag("api_design") == "api-design"
        assert normalize_tag("machine_learning") == "machine-learning"

    def test_remove_special_characters(self):
        """Test removing special characters."""
        assert normalize_tag("api@design") == "apidesign"
        assert normalize_tag("frontend!") == "frontend"
        assert normalize_tag("back-end#") == "back-end"

    def test_multiple_dashes(self):
        """Test collapsing multiple dashes."""
        assert normalize_tag("api--design") == "api-design"
        assert normalize_tag("foo---bar") == "foo-bar"

    def test_leading_trailing_dashes(self):
        """Test removing leading/trailing dashes."""
        assert normalize_tag("-backend-") == "backend"
        assert normalize_tag("--api--") == "api"

    def test_whitespace_trimming(self):
        """Test trimming whitespace."""
        assert normalize_tag("  backend  ") == "backend"
        assert normalize_tag("\tapi\n") == "api"

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            pytest.param("", "", id="empty-string"),
            pytest.param("   ", "", id="whitespace-only"),
            pytest.param("!!!", "", id="only-bangs"),
            pytest.param("@#$%", "", id="only-symbols"),
            pytest.param("---", "", id="only-dashes"),
            pytest.param("café", "caf", id="unicode-accented"),
            pytest.param("日本語", "", id="unicode-japanese"),
            pytest.param("Москва", "", id="unicode-cyrillic"),
            pytest.param("api__design--system", "api-design-system", id="mixed-separators-underscores-dashes"),
            pytest.param("foo _ bar - baz", "foo-bar-baz", id="mixed-separators-spaced"),
            pytest.param("v2.0", "v20", id="numeric-version"),
            pytest.param("python3", "python3", id="numeric-trailing-digit"),
            pytest.param("2023-Q1", "2023-q1", id="numeric-quarter"),
            pytest.param("a" * 1000, "a" * 1000, id="very-long-tag"),
            pytest.param("https://example.com", "httpsexamplecom", id="url-like"),
            pytest.param("api.v1.endpoint", "apiv1endpoint", id="dotted-path"),
            pytest.param("API2Design", "api2design", id="mixed-case-with-number"),
            pytest.param("v1.2.3", "v123", id="dotted-version"),
            pytest.param("2023-update", "2023-update", id="leading-number-year"),
            pytest.param("1st-release", "1st-release", id="leading-number-ordinal"),
            pytest.param("backend🔥", "backend", id="emoji-trailing"),
            pytest.param("✨feature", "feature", id="emoji-leading"),
            pytest.param("api\tdesign", "api-design", id="tab-whitespace"),
            pytest.param("api\ndesign", "api-design", id="newline-whitespace"),
            pytest.param("api\r\ndesign", "api-design", id="crlf-whitespace"),
        ],
    )
    def test_normalize_tag_edge_cases(self, raw, expected):
        """Test normalize_tag across empty, unicode, numeric, emoji, and whitespace inputs."""
        assert normalize_tag(raw) == expected


class TestFixTags:
    """Test tags field fixes."""

    def test_add_missing_tags_field(self, tmp_path):
        """Test adding missing tags field."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\ntitle: Test\n---\n# Test")

        changed, messages = fix_tags(doc)

        assert changed
        assert any("Added missing tags field" in msg for msg in messages)

        post = frontmatter.loads(doc.read_text())
        assert "tags" in post.metadata
        assert post.metadata["tags"] == []

    def test_convert_string_to_array(self, tmp_path):
        """Test converting string tags to array."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\ntags: backend\n---\n# Test")

        changed, messages = fix_tags(doc)

        assert changed
        assert any("Converted string tags to array" in msg for msg in messages)

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["backend"]

    def test_normalize_tags_case(self, tmp_path):
        """Test normalizing tag case."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["Backend", "API", "Frontend"]\n---\n# Test')

        changed, messages = fix_tags(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["api", "backend", "frontend"]

    def test_normalize_tags_spaces(self, tmp_path):
        """Test normalizing tags with spaces."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["API Design", "Machine Learning"]\n---\n# Test')

        changed, messages = fix_tags(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["api-design", "machine-learning"]

    def test_remove_duplicates(self, tmp_path):
        """Test removing duplicate tags."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["backend", "Backend", "api", "backend"]\n---\n# Test')

        changed, messages = fix_tags(doc)

        assert changed
        assert any("duplicate" in msg.lower() for msg in messages)

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["api", "backend"]
        assert len(post.metadata["tags"]) == 2

    def test_sort_alphabetically(self, tmp_path):
        """Test sorting tags alphabetically."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["zebra", "alpha", "mike"]\n---\n# Test')

        changed, messages = fix_tags(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == ["alpha", "mike", "zebra"]

    def test_empty_string_tags(self, tmp_path):
        """Test handling empty string tags."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\ntags: ''\n---\n# Test")

        changed, messages = fix_tags(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == []

    def test_mixed_normalization(self, tmp_path):
        """Test comprehensive normalization."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["API Design", "backend", "api_design", "FRONTEND"]\n---\n# Test')

        changed, messages = fix_tags(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        # "API Design" and "api_design" both become "api-design" (duplicate removed)
        assert post.metadata["tags"] == ["api-design", "backend", "frontend"]

    def test_no_changes_needed(self, tmp_path):
        """Test when tags are already correct."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["api", "backend", "frontend"]\n---\n# Test')

        changed, messages = fix_tags(doc)

        assert not changed
        assert len(messages) == 0

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry run doesn't write changes."""
        doc = tmp_path / "test.md"
        content = '---\nid: test\ntags: ["Backend", "API"]\n---\n# Test'
        doc.write_text(content)

        changed, messages = fix_tags(doc, dry_run=True)

        assert changed
        assert len(messages) > 0
        # File should be unchanged
        assert doc.read_text() == content

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param("---\nid: test\ntags: null\n---\n# Test\n", id="null-tags"),
            pytest.param("---\nid: test\ntags:\n  backend: true\n---\n# Test", id="dict-tags"),
        ],
    )
    def test_invalid_tags_type_is_not_changed(self, tmp_path, content):
        """Test that non-list tags (null, dict) are reported but not modified."""
        doc = tmp_path / "test.md"
        doc.write_text(content)

        changed, messages = fix_tags(doc)

        assert not changed
        assert any("invalid type" in msg.lower() for msg in messages)

    def test_mixed_type_array_skips_non_string_tags(self, tmp_path):
        """Test that non-string entries in a tags array are dropped with a message."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: test\ntags: ["backend", 123, true]\n---\n# Test')

        changed, messages = fix_tags(doc)

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

        fix_tags(doc)

        post = frontmatter.loads(doc.read_text())
        assert len(post.metadata["tags"]) == 1000

    @pytest.mark.parametrize(
        ("content", "expected_tags"),
        [
            pytest.param(
                '---\nid: test\ntags: ["backend", "backend", "backend"]\n---\n# Test',
                ["backend"],
                id="duplicates-only",
            ),
            pytest.param(
                '---\nid: test\ntags: ["backend", "", "  ", "frontend"]\n---\n# Test',
                ["backend", "frontend"],
                id="empty-strings-filtered",
            ),
            pytest.param(
                '---\nid: test\ntags: ["!!!", "@@@", "###"]\n---\n# Test',
                [],
                id="all-invalid-chars",
            ),
            pytest.param(
                '---\nid: test\ntags: ["API", "Api", "api", "aPi"]\n---\n# Test',
                ["api"],
                id="case-variations-collapse",
            ),
            pytest.param(
                '---\nid: test\ntags: ["  API___DESIGN  ", "api-design", "api__design"]\n---\n# Test',
                ["api-design"],
                id="complex-normalization-collapse",
            ),
            pytest.param(
                '---\nid: test\ntags: ["yes", "no", "true", "false", "on", "off"]\n---\n# Test',
                ["false", "no", "off", "on", "true", "yes"],
                id="yaml-boolean-like-strings",
            ),
            pytest.param(
                '---\nid: test\ntags: ["Backend"]\n---\n# Test',
                ["backend"],
                id="single-tag-array",
            ),
            pytest.param(
                "---\nid: test\ntags:\n  - Backend\n  - API Design\n  - frontend\n---\n# Test\n",
                ["api-design", "backend", "frontend"],
                id="multiline-yaml-array",
            ),
        ],
    )
    def test_fix_tags_normalizes_various_inputs(self, tmp_path, content, expected_tags):
        """Test fix_tags collapses duplicates, drops blanks, and normalizes case/format."""
        doc = tmp_path / "test.md"
        doc.write_text(content)

        changed, messages = fix_tags(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["tags"] == expected_tags

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

    def test_tags_with_quotes(self, tmp_path):
        """Test tags with embedded quotes and mixed quoting styles."""
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
        tags = post.metadata["tags"]
        assert isinstance(tags, list)
        assert "api" in tags
        assert "backend" in tags
        assert "frontend" in tags
