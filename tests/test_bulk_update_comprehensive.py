"""Comprehensive tests for bulk update - positive, negative, and edge cases."""

from pathlib import Path

import frontmatter
import pytest

from docuchango.fixes.bulk_update import (
    bulk_update_files,
    should_skip_file,
    update_frontmatter_bulk,
)


class TestShouldSkipFileEdgeCases:
    """Edge case tests for file skipping logic."""

    def test_case_variations(self):
        """Test case-insensitive template detection."""
        assert should_skip_file(Path("TEMPLATE.md"))
        assert should_skip_file(Path("Template.md"))
        assert should_skip_file(Path("TeMpLaTe.md"))

    def test_template_in_path(self):
        """Test template in directory name."""
        assert not should_skip_file(Path("templates/my-doc.md"))
        assert should_skip_file(Path("templates/template.md"))

    def test_numbers_in_filename(self):
        """Test files with numbers."""
        assert should_skip_file(Path("000-template.md"))
        assert should_skip_file(Path("000-anything.md"))
        assert not should_skip_file(Path("001-document.md"))
        assert not should_skip_file(Path("adr-001.md"))

    def test_index_variations(self):
        """Test index file variations."""
        assert should_skip_file(Path("index.md"))
        assert not should_skip_file(Path("INDEX.md"))  # Case sensitive
        assert not should_skip_file(Path("my-index.md"))

    def test_valid_document_names(self):
        """Test that valid documents are not skipped."""
        valid_names = [
            "adr-001-decision.md",
            "rfc-042-proposal.md",
            "memo-2023-q1.md",
            "document.md",
            "my-file.md",
        ]
        for name in valid_names:
            assert not should_skip_file(Path(name))


class TestUpdateFrontmatterBulkEdgeCases:
    """Edge case tests for bulk frontmatter updates."""

    def test_set_with_same_value(self):
        """Test setting field to same value it already has."""
        content = """---
id: test
status: Accepted
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "status", "Accepted", "set")

        assert not modified
        assert "status" in message.lower()
        assert "already" in message.lower()

    def test_set_on_empty_frontmatter(self):
        """Test set operation on empty frontmatter."""
        content = """---
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "status", "Accepted", "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["status"] == "Accepted"

    def test_add_already_existing_field(self):
        """Test add operation when field exists."""
        content = """---
id: test
status: Draft
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "status", "Accepted", "add")

        assert not modified
        assert "already exists" in message
        # Original value should be preserved
        post = frontmatter.loads(new_content)
        assert post.metadata["status"] == "Draft"

    def test_remove_nonexistent_field(self):
        """Test remove operation on missing field."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "status", None, "remove")

        assert not modified
        assert "not found" in message

    def test_rename_nonexistent_field(self):
        """Test rename operation on missing field."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "old_name", "new_name", "rename")

        assert not modified
        assert "not found" in message

    def test_rename_to_existing_field(self):
        """Test rename to name that already exists."""
        content = """---
id: test
old_name: value1
new_name: value2
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "old_name", "new_name", "rename")

        assert modified
        post = frontmatter.loads(new_content)
        # old_name should be removed, new_name should have old_name's value
        assert "old_name" not in post.metadata
        assert post.metadata["new_name"] == "value1"

    def test_set_with_special_characters(self):
        """Test setting values with special characters."""
        content = """---
id: test
---
# Test
"""
        special_values = [
            "value: with: colons",
            "value with spaces",
            "value\nwith\nnewlines",
            "value\twith\ttabs",
        ]

        for value in special_values:
            new_content, modified, message = update_frontmatter_bulk(content, "field", value, "set")
            assert modified

    def test_set_with_empty_string(self):
        """Test setting field to empty string."""
        content = """---
id: test
field: value
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "field", "", "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["field"] == ""

    def test_set_with_numeric_value(self):
        """Test setting field to numeric value."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "priority", "123", "set")

        assert modified
        post = frontmatter.loads(new_content)
        # Should be stored as string
        assert post.metadata["priority"] == "123"

    def test_invalid_operation(self):
        """Test with invalid operation."""
        content = """---
id: test
---
# Test
"""
        # Should raise ValueError for invalid operations
        with pytest.raises(ValueError, match="Invalid operation"):
            update_frontmatter_bulk(content, "field", "value", "invalid_op")

    def test_very_long_field_name(self):
        """Test with very long field name."""
        content = """---
id: test
---
# Test
"""
        long_name = "a" * 1000
        new_content, modified, message = update_frontmatter_bulk(content, long_name, "value", "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata[long_name] == "value"

    def test_very_long_field_value(self):
        """Test with very long field value."""
        content = """---
id: test
---
# Test
"""
        long_value = "x" * 100000
        new_content, modified, message = update_frontmatter_bulk(content, "field", long_value, "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert len(post.metadata["field"]) == 100000

    def test_unicode_field_names(self):
        """Test with Unicode field names."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "фield", "value", "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["фield"] == "value"

    def test_unicode_field_values(self):
        """Test with Unicode field values."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "field", "значение", "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["field"] == "значение"


class TestBulkUpdateFilesEdgeCases:
    """Edge case tests for bulk file operations."""

    def test_empty_file_list(self):
        """Test with empty file list."""
        results = bulk_update_files([], "field", "value", "set")

        assert len(results) == 0

    def test_nonexistent_files(self, tmp_path):
        """Test with files that don't exist."""
        files = [tmp_path / "nonexistent1.md", tmp_path / "nonexistent2.md"]

        results = bulk_update_files(files, "field", "value", "set")

        # Should have errors for each file
        assert len(results) == 2
        assert all(not changed for _, changed, _ in results)

    def test_mixed_valid_invalid_files(self, tmp_path):
        """Test with mix of valid and invalid files."""
        valid = tmp_path / "valid.md"
        valid.write_text("---\nid: test\n---\n# Test")

        invalid = tmp_path / "invalid.md"
        # Don't create invalid file

        results = bulk_update_files([valid, invalid], "field", "value", "set")

        assert len(results) == 2
        # One should succeed, one should fail
        success_count = sum(1 for _, changed, _ in results if changed)
        assert success_count == 1

    def test_files_in_different_directories(self, tmp_path):
        """Test files across multiple directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        file1 = dir1 / "doc1.md"
        file2 = dir2 / "doc2.md"

        for f in [file1, file2]:
            f.write_text("---\nid: test\n---\n# Test")

        results = bulk_update_files([file1, file2], "field", "value", "set")

        assert len(results) == 2
        assert all(changed for _, changed, _ in results)

    def test_duplicate_files_in_list(self, tmp_path):
        """Test same file listed multiple times.

        Note: Each file path in the list is processed independently.
        The first occurrence will add the field, subsequent ones will
        update it (but since it's the same value, no change).
        """
        doc = tmp_path / "doc.md"
        doc.write_text("---\nid: test\n---\n# Test")

        results = bulk_update_files([doc, doc, doc], "field", "value", "set")

        # Should process each occurrence
        # First one modifies, next two don't (already has same value)
        assert len(results) == 3
        assert results[0][1] is True  # First one is modified
        assert results[1][1] is False  # Second one is not modified
        assert results[2][1] is False  # Third one is not modified

    def test_dry_run_with_multiple_files(self, tmp_path):
        """Test dry run mode with multiple files."""
        files = []
        for i in range(5):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text("---\nid: test\n---\n# Test")
            files.append(doc)

        # Get original contents
        originals = [f.read_text() for f in files]

        results = bulk_update_files(files, "field", "value", "set", dry_run=True)

        # All should report changes
        assert all(changed for _, changed, _ in results)

        # But no files should be modified
        for f, original in zip(files, originals):
            assert f.read_text() == original

    def test_bulk_remove_all_fields(self, tmp_path):
        """Test removing same field from all files."""
        files = []
        for i in range(3):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text("---\nid: test\ndeprecated: true\n---\n# Test")
            files.append(doc)

        results = bulk_update_files(files, "deprecated", None, "remove")

        assert all(changed for _, changed, _ in results)

        # Verify all removed
        for f in files:
            post = frontmatter.loads(f.read_text())
            assert "deprecated" not in post.metadata

    def test_bulk_rename_preserves_values(self, tmp_path):
        """Test rename preserves different values."""
        values = ["value1", "value2", "value3"]
        files = []

        for i, value in enumerate(values):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text(f"---\nid: test\nold_name: {value}\n---\n# Test")
            files.append(doc)

        results = bulk_update_files(files, "old_name", "new_name", "rename")

        assert all(changed for _, changed, _ in results)

        # Verify values preserved
        for f, expected_value in zip(files, values):
            post = frontmatter.loads(f.read_text())
            assert post.metadata["new_name"] == expected_value

    def test_large_number_of_files(self, tmp_path):
        """Test with large number of files."""
        files = []
        for i in range(100):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text("---\nid: test\n---\n# Test")
            files.append(doc)

        results = bulk_update_files(files, "field", "value", "set")

        assert len(results) == 100
        assert all(changed for _, changed, _ in results)

    def test_concurrent_operations_different_fields(self, tmp_path):
        """Test multiple operations on same files."""
        doc = tmp_path / "doc.md"
        doc.write_text("---\nid: test\n---\n# Test")

        # First operation
        bulk_update_files([doc], "field1", "value1", "set")

        # Second operation
        bulk_update_files([doc], "field2", "value2", "set")

        # Both should exist
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["field1"] == "value1"
        assert post.metadata["field2"] == "value2"
