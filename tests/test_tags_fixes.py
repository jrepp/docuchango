"""Tests for tags normalization fixes."""

import frontmatter

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
