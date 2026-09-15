"""Tests for bulk update frontmatter functionality."""

from pathlib import Path

import frontmatter
import pytest

from docuchango.fixes.bulk_update import (
    bulk_update_files,
    should_skip_file,
    update_frontmatter_bulk,
)


class TestShouldSkipFile:
    """Test file skipping logic."""

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("adr-000-template.md", id="numeric-prefix-plus-template-word"),
            pytest.param("my-TEMPLATE.md", id="uppercase-template-word"),
            pytest.param("Template.md", id="titlecase-template-word"),
            pytest.param("TeMpLaTe.md", id="mixed-case-template-word"),
            pytest.param("000-template.md", id="leading-000-and-template-word"),
            pytest.param("000-anything.md", id="leading-000-only"),
            pytest.param("templates/template.md", id="template-word-in-filename-under-templates-dir"),
            pytest.param("index.md", id="index-file"),
        ],
    )
    def test_skip_template_and_index_files(self, path):
        """Test that template-like and index filenames are skipped."""
        assert should_skip_file(Path(path))

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("adr-001-test.md", id="normal-adr"),
            pytest.param("rfc-042-proposal.md", id="normal-rfc"),
            pytest.param("memo-2023-q1.md", id="normal-memo"),
            pytest.param("document.md", id="generic-document"),
            pytest.param("my-file.md", id="generic-file"),
            pytest.param("001-document.md", id="leading-nonzero-number"),
            pytest.param("adr-001.md", id="short-adr-id"),
            pytest.param("INDEX.md", id="index-uppercase-is-case-sensitive"),
            pytest.param("my-index.md", id="index-as-suffix-not-whole-name"),
            pytest.param("templates/my-doc.md", id="templates-directory-but-plain-filename"),
        ],
    )
    def test_dont_skip_normal_files(self, path):
        """Test that ordinary document filenames are never skipped."""
        assert not should_skip_file(Path(path))


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

    def test_set_to_same_value_reports_no_change(self):
        """Test that setting a field to the value it already has is a no-op."""
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
        """Test set operation when the frontmatter block has no fields yet."""
        content = """---
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "status", "Accepted", "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["status"] == "Accepted"

    def test_rename_to_a_name_that_already_exists_overwrites_it(self):
        """Test that renaming onto an existing field name overwrites the target with
        the source's value and removes the source."""
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
        assert "old_name" not in post.metadata
        assert post.metadata["new_name"] == "value1"

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param("value: with: colons", id="colons"),
            pytest.param("value with spaces", id="spaces"),
            pytest.param("value\nwith\nnewlines", id="newlines"),
            pytest.param("value\twith\ttabs", id="tabs"),
        ],
    )
    def test_set_with_special_character_values(self, value):
        """Test that field values containing YAML-sensitive characters are still applied."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "field", value, "set")

        assert modified

    def test_set_field_to_empty_string(self):
        """Test setting a field's value to an empty string."""
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

    def test_set_numeric_looking_value_is_stored_as_string(self):
        """Test that a numeric-looking value is quoted/stored as a string, not a YAML number."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "priority", "123", "set")

        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["priority"] == "123"

    def test_invalid_operation_raises_value_error(self):
        """Test that an unrecognized operation name raises ValueError."""
        content = """---
id: test
---
# Test
"""
        with pytest.raises(ValueError, match="Invalid operation"):
            update_frontmatter_bulk(content, "field", "value", "invalid_op")

    def test_rename_requires_non_empty_new_field_name(self):
        """Test that rename rejects an empty or missing target field name."""
        content = """---
id: test
old_name: value
---
# Test
"""
        with pytest.raises(ValueError, match="non-empty new field name"):
            update_frontmatter_bulk(content, "old_name", "", "rename")

        with pytest.raises(ValueError, match="non-empty new field name"):
            update_frontmatter_bulk(content, "old_name", None, "rename")

    def test_very_long_field_name_and_value_round_trip(self):
        """Test that very long field names and values survive a set + reparse."""
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

        long_value = "x" * 100000
        new_content, modified, message = update_frontmatter_bulk(content, "field", long_value, "set")
        assert modified
        post = frontmatter.loads(new_content)
        assert len(post.metadata["field"]) == 100000

    def test_unicode_field_name_and_value_round_trip(self):
        """Test that non-Latin field names and values are preserved."""
        content = """---
id: test
---
# Test
"""
        new_content, modified, message = update_frontmatter_bulk(content, "фield", "value", "set")
        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["фield"] == "value"

        new_content, modified, message = update_frontmatter_bulk(content, "field", "значение", "set")
        assert modified
        post = frontmatter.loads(new_content)
        assert post.metadata["field"] == "значение"


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

    def test_empty_file_list_returns_no_results(self):
        """Test that an empty file list produces no results."""
        results = bulk_update_files([], "field", "value", "set")

        assert len(results) == 0

    def test_nonexistent_files_report_as_unchanged(self, tmp_path):
        """Test that files that don't exist on disk are reported without being changed."""
        files = [tmp_path / "nonexistent1.md", tmp_path / "nonexistent2.md"]

        results = bulk_update_files(files, "field", "value", "set")

        assert len(results) == 2
        assert all(not changed for _, changed, _ in results)

    def test_mix_of_existing_and_missing_files(self, tmp_path):
        """Test that a missing file in the list doesn't stop the valid file from updating."""
        valid = tmp_path / "valid.md"
        valid.write_text("---\nid: test\n---\n# Test")

        missing = tmp_path / "missing.md"  # Not created

        results = bulk_update_files([valid, missing], "field", "value", "set")

        assert len(results) == 2
        success_count = sum(1 for _, changed, _ in results if changed)
        assert success_count == 1

    def test_files_across_multiple_directories_all_update(self, tmp_path):
        """Test that files in different directories are each updated independently."""
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

    def test_same_file_listed_multiple_times_is_processed_each_time(self, tmp_path):
        """Test that repeating a path in the list processes it repeatedly: the first
        occurrence sets the field, and later occurrences find it already set."""
        doc = tmp_path / "doc.md"
        doc.write_text("---\nid: test\n---\n# Test")

        results = bulk_update_files([doc, doc, doc], "field", "value", "set")

        assert len(results) == 3
        assert results[0][1] is True
        assert results[1][1] is False
        assert results[2][1] is False

    def test_dry_run_with_multiple_files_leaves_all_unmodified(self, tmp_path):
        """Test that dry run reports changes for every file without writing any of them."""
        files = []
        for i in range(5):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text("---\nid: test\n---\n# Test")
            files.append(doc)

        originals = [f.read_text() for f in files]

        results = bulk_update_files(files, "field", "value", "set", dry_run=True)

        assert all(changed for _, changed, _ in results)
        for f, original in zip(files, originals, strict=True):
            assert f.read_text() == original

    def test_bulk_remove_same_field_from_every_file(self, tmp_path):
        """Test removing the same field from a batch of files."""
        files = []
        for i in range(3):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text("---\nid: test\ndeprecated: true\n---\n# Test")
            files.append(doc)

        results = bulk_update_files(files, "deprecated", None, "remove")

        assert all(changed for _, changed, _ in results)
        for f in files:
            post = frontmatter.loads(f.read_text())
            assert "deprecated" not in post.metadata

    def test_bulk_rename_preserves_each_files_distinct_value(self, tmp_path):
        """Test that a bulk rename preserves each file's own value rather than
        overwriting them with a single shared value."""
        values = ["value1", "value2", "value3"]
        files = []

        for i, value in enumerate(values):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text(f"---\nid: test\nold_name: {value}\n---\n# Test")
            files.append(doc)

        results = bulk_update_files(files, "old_name", "new_name", "rename")

        assert all(changed for _, changed, _ in results)
        for f, expected_value in zip(files, values, strict=True):
            post = frontmatter.loads(f.read_text())
            assert post.metadata["new_name"] == expected_value

    def test_large_number_of_files(self, tmp_path):
        """Test that bulk_update_files scales to a large batch without dropping any."""
        files = []
        for i in range(100):
            doc = tmp_path / f"doc{i}.md"
            doc.write_text("---\nid: test\n---\n# Test")
            files.append(doc)

        results = bulk_update_files(files, "field", "value", "set")

        assert len(results) == 100
        assert all(changed for _, changed, _ in results)

    def test_successive_calls_on_the_same_file_accumulate_fields(self, tmp_path):
        """Test that separate bulk_update_files calls on the same file both take effect."""
        doc = tmp_path / "doc.md"
        doc.write_text("---\nid: test\n---\n# Test")

        bulk_update_files([doc], "field1", "value1", "set")
        bulk_update_files([doc], "field2", "value2", "set")

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["field1"] == "value1"
        assert post.metadata["field2"] == "value2"
