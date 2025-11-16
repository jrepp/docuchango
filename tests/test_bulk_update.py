"""Tests for bulk update frontmatter functionality."""

from pathlib import Path

import frontmatter

from docuchango.fixes.bulk_update import (
    bulk_update_files,
    should_skip_file,
    update_frontmatter_bulk,
)


class TestShouldSkipFile:
    """Test file skipping logic."""

    def test_skip_template_files(self):
        """Test that template files are skipped."""
        assert should_skip_file(Path("adr-000-template.md"))
        assert should_skip_file(Path("my-TEMPLATE.md"))

    def test_skip_index_files(self):
        """Test that index files are skipped."""
        assert should_skip_file(Path("index.md"))

    def test_dont_skip_normal_files(self):
        """Test that normal files are not skipped."""
        assert not should_skip_file(Path("adr-001-test.md"))
        assert not should_skip_file(Path("rfc-042-proposal.md"))


class TestUpdateFrontmatterBulk:
    """Test frontmatter bulk update operations."""

    def test_set_new_field(self):
        """Test setting a field that doesn't exist."""
        content = """---
id: "test-001"
title: "Test"
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "priority", "high", "set")

        assert modified
        assert "Added priority=high" in message
        post = frontmatter.loads(new_content)
        assert post.metadata["priority"] == "high"

    def test_set_existing_field(self):
        """Test updating an existing field."""
        content = """---
id: "test-001"
title: "Test"
status: Draft
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "status", "Accepted", "set")

        assert modified
        assert "Updated status" in message
        post = frontmatter.loads(new_content)
        assert post.metadata["status"] == "Accepted"

    def test_add_new_field(self):
        """Test adding a field that doesn't exist."""
        content = """---
id: "test-001"
title: "Test"
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "reviewed", "yes", "add")

        assert modified
        assert "Added reviewed=yes" in message
        post = frontmatter.loads(new_content)
        assert post.metadata["reviewed"] == "yes"

    def test_add_existing_field(self):
        """Test that add doesn't modify existing fields."""
        content = """---
id: "test-001"
title: "Test"
status: Draft
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "status", "Accepted", "add")

        assert not modified
        assert "already exists" in message
        post = frontmatter.loads(new_content)
        assert post.metadata["status"] == "Draft"  # Unchanged

    def test_remove_existing_field(self):
        """Test removing an existing field."""
        content = """---
id: "test-001"
title: "Test"
deprecated: true
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "deprecated", None, "remove")

        assert modified
        assert "Removed deprecated" in message
        post = frontmatter.loads(new_content)
        assert "deprecated" not in post.metadata

    def test_remove_nonexistent_field(self):
        """Test removing a field that doesn't exist."""
        content = """---
id: "test-001"
title: "Test"
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "missing", None, "remove")

        assert not modified
        assert "not found" in message

    def test_rename_existing_field(self):
        """Test renaming an existing field."""
        content = """---
id: "test-001"
title: "Test"
old_name: "value"
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "old_name", "new_name", "rename")

        assert modified
        assert "Renamed old_name → new_name" in message
        post = frontmatter.loads(new_content)
        assert "old_name" not in post.metadata
        assert post.metadata["new_name"] == "value"

    def test_rename_nonexistent_field(self):
        """Test renaming a field that doesn't exist."""
        content = """---
id: "test-001"
title: "Test"
---

# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "missing", "new_name", "rename")

        assert not modified
        assert "not found" in message


class TestBulkUpdateFiles:
    """Test bulk file updates."""

    def test_bulk_set_field(self, tmp_path):
        """Test setting a field across multiple files."""
        # Create test files
        doc1 = tmp_path / "doc1.md"
        doc2 = tmp_path / "doc2.md"

        for doc in [doc1, doc2]:
            doc.write_text("---\nid: test\n---\n# Test")

        results = bulk_update_files([doc1, doc2], "priority", "high", "set")

        assert len(results) == 2
        assert all(changed for _, changed, _ in results)

        # Verify changes
        for doc in [doc1, doc2]:
            post = frontmatter.loads(doc.read_text())
            assert post.metadata["priority"] == "high"

    def test_bulk_update_dry_run(self, tmp_path):
        """Test that dry run doesn't modify files."""
        doc = tmp_path / "doc.md"
        doc.write_text("---\nid: test\n---\n# Test")
        original_content = doc.read_text()

        results = bulk_update_files([doc], "priority", "high", "set", dry_run=True)

        assert len(results) == 1
        assert results[0][1]  # Changed flag is True
        # But file should be unchanged
        assert doc.read_text() == original_content

    def test_bulk_update_skips_templates(self, tmp_path):
        """Test that template files are skipped."""
        template = tmp_path / "000-template.md"
        template.write_text("---\nid: template\n---\n# Template")

        results = bulk_update_files([template], "priority", "high", "set")

        assert len(results) == 0  # Skipped
