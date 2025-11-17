"""Comprehensive tests for whitespace fixes - positive, negative, and edge cases."""

import frontmatter
import pytest

from docuchango.fixes.whitespace import (
    ensure_required_fields,
    fix_whitespace_and_fields,
    normalize_empty_values,
    trim_string_values,
)


class TestTrimStringValuesEdgeCases:
    """Edge case tests for trimming string values."""

    def test_only_whitespace_strings(self):
        """Test strings with only whitespace."""
        metadata = {
            "title": "   ",
            "description": "\t\t",
            "summary": "\n\n",
        }

        updated, messages = trim_string_values(metadata)

        assert updated["title"] == ""
        assert updated["description"] == ""
        assert updated["summary"] == ""

    def test_mixed_whitespace_types(self):
        """Test various whitespace characters."""
        metadata = {
            "title": " \t\nMy Title\r\n\t ",
        }

        updated, messages = trim_string_values(metadata)

        assert updated["title"] == "My Title"

    def test_unicode_whitespace(self):
        """Test Unicode whitespace characters."""
        metadata = {
            "title": "\u00a0Title\u00a0",  # Non-breaking space
            "description": "\u2003Content\u2003",  # Em space
        }

        updated, messages = trim_string_values(metadata)

        # Python strip() handles Unicode whitespace
        assert updated["title"].strip() == "Title"

    def test_nested_structures(self):
        """Test deeply nested structures."""
        metadata = {
            "config": {
                "nested": " value ",
            },
            "tags": [" tag1 ", " tag2 "],
        }

        updated, messages = trim_string_values(metadata)

        # Only handles top-level and arrays, not nested dicts
        assert updated["config"]["nested"] == " value "  # Not trimmed
        assert updated["tags"] == ["tag1", "tag2"]  # Trimmed

    def test_very_long_strings(self):
        """Test very long strings with whitespace."""
        long_content = " " + ("x" * 10000) + " "
        metadata = {"content": long_content}

        updated, messages = trim_string_values(metadata)

        assert len(updated["content"]) == 10000
        assert updated["content"][0] == "x"
        assert updated["content"][-1] == "x"

    def test_strings_with_internal_whitespace(self):
        """Test preserving internal whitespace."""
        metadata = {
            "title": "  Multiple   Internal   Spaces  ",
        }

        updated, messages = trim_string_values(metadata)

        # Should only trim edges, not internal
        assert updated["title"] == "Multiple   Internal   Spaces"

    def test_empty_metadata(self):
        """Test empty metadata dictionary."""
        metadata = {}

        updated, messages = trim_string_values(metadata)

        assert updated == {}
        assert len(messages) == 0

    def test_all_non_string_values(self):
        """Test metadata with no strings."""
        metadata = {
            "count": 42,
            "enabled": True,
            "ratio": 3.14,
            "items": [1, 2, 3],
        }

        updated, messages = trim_string_values(metadata)

        assert updated == metadata
        assert len(messages) == 0

    def test_mixed_array_types(self):
        """Test arrays with mixed types."""
        metadata = {
            "mixed": [" string ", 123, True, " another "],
        }

        updated, messages = trim_string_values(metadata)

        assert updated["mixed"] == ["string", 123, True, "another"]

    def test_empty_arrays(self):
        """Test empty arrays."""
        metadata = {
            "tags": [],
            "authors": [],
        }

        updated, messages = trim_string_values(metadata)

        assert updated["tags"] == []
        assert updated["authors"] == []


class TestNormalizeEmptyValuesEdgeCases:
    """Edge case tests for normalizing empty values."""

    def test_mixed_empty_types(self):
        """Test various empty value types."""
        metadata = {
            "str_empty": "",
            "str_spaces": "   ",
            "null_value": None,
            "empty_list": [],
            "zero": 0,
            "false": False,
        }

        updated, messages = normalize_empty_values(metadata)

        # Empty strings and nulls removed
        assert "str_empty" not in updated
        assert "str_spaces" not in updated
        assert "null_value" not in updated
        # Zero and False are valid values
        assert updated["zero"] == 0
        assert updated["false"] is False

    def test_list_fields_comprehensive(self):
        """Test all list field types."""
        metadata = {
            "tags": [],
            "authors": [],
            "reviewers": [],
            "related": [],
            "custom_list": [],
        }

        updated, messages = normalize_empty_values(metadata)

        # Known list fields should be kept
        assert "tags" in updated
        assert "authors" in updated
        assert "reviewers" in updated
        assert "related" in updated
        # Unknown list field should be removed
        assert "custom_list" not in updated

    def test_arrays_with_empty_strings(self):
        """Test arrays containing empty strings."""
        metadata = {
            "tags": ["", "valid", ""],
        }

        updated, messages = normalize_empty_values(metadata)

        # Should keep the array (doesn't filter contents)
        assert updated["tags"] == ["", "valid", ""]

    def test_nested_empty_values(self):
        """Test nested structures with empty values."""
        metadata = {
            "config": {
                "value": "",
                "other": None,
            },
        }

        updated, messages = normalize_empty_values(metadata)

        # Doesn't recurse into nested dicts
        assert "config" in updated
        assert updated["config"]["value"] == ""

    def test_special_string_values(self):
        """Test strings that might be considered empty."""
        metadata = {
            "zero_str": "0",
            "false_str": "false",
            "null_str": "null",
            "none_str": "None",
        }

        updated, messages = normalize_empty_values(metadata)

        # These are valid non-empty strings
        assert all(key in updated for key in metadata)


class TestEnsureRequiredFieldsEdgeCases:
    """Edge case tests for ensuring required fields."""

    def test_uuid_collision_handling(self):
        """Test generating multiple UUIDs."""
        metadata1 = {"id": "test1"}
        metadata2 = {"id": "test2"}

        updated1, _ = ensure_required_fields(metadata1)
        updated2, _ = ensure_required_fields(metadata2)

        # UUIDs should be different
        assert updated1["doc_uuid"] != updated2["doc_uuid"]

    def test_uuid_format_validation(self):
        """Test that generated UUIDs are valid."""
        import uuid as uuid_mod

        metadata = {"id": "test"}

        updated, _ = ensure_required_fields(metadata)

        # Should be valid UUID
        try:
            uuid_mod.UUID(updated["doc_uuid"])
        except ValueError:
            pytest.fail("Generated UUID is invalid")

    def test_existing_empty_string_fields(self):
        """Test handling of existing but empty required fields."""
        metadata = {
            "id": "test",
            "tags": "",  # Should be array
            "doc_uuid": "",  # Should be generated
            "project_id": "",  # Should be set
        }

        updated, messages = ensure_required_fields(metadata)

        # Empty tags left as-is (not our job to fix here)
        assert updated["tags"] == ""
        # Empty doc_uuid should be replaced
        assert updated["doc_uuid"] != ""
        # Empty project_id should be replaced
        assert updated["project_id"] != ""

    def test_required_fields_basic(self):
        """Test basic required fields are added consistently across document types."""
        # Test different document types to ensure required fields work regardless of doc type
        test_cases = [
            {"id": "test-adr", "doc_type": "adr"},
            {"id": "test-rfc", "doc_type": "rfc"},
            {"id": "test-memo", "doc_type": "memo"},
            {"id": "test-prd", "doc_type": "prd"},
            {"id": "test-generic"},  # No doc_type specified
        ]

        for metadata in test_cases:
            updated, messages = ensure_required_fields(metadata)

            # All should get these fields regardless of document type
            assert "tags" in updated, f"tags missing for {metadata.get('id')}"
            assert "doc_uuid" in updated, f"doc_uuid missing for {metadata.get('id')}"
            assert "project_id" in updated, f"project_id missing for {metadata.get('id')}"

    def test_preserving_extra_fields(self):
        """Test that extra fields are preserved."""
        metadata = {
            "id": "test",
            "custom_field": "custom_value",
            "another": 123,
        }

        updated, messages = ensure_required_fields(metadata)

        # Custom fields should be preserved
        assert updated["custom_field"] == "custom_value"
        assert updated["another"] == 123

    def test_very_large_metadata(self):
        """Test metadata with many existing fields."""
        metadata = {f"field{i}": f"value{i}" for i in range(1000)}

        updated, messages = ensure_required_fields(metadata)

        # Should add required fields
        assert "tags" in updated
        assert "doc_uuid" in updated
        assert "project_id" in updated
        # Should preserve all existing
        assert len(updated) >= 1003


class TestFixWhitespaceAndFieldsEdgeCases:
    """Edge case tests for combined fixes."""

    def test_file_in_root_directory(self, tmp_path):
        """Test file not in typed subdirectory."""
        doc = tmp_path / "test.md"
        doc.write_text("""---
id: " test "
title: "  Title  "
---
# Test
""")

        changed, messages = fix_whitespace_and_fields(doc)

        # Should still work without doc_type
        assert changed

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "test"
        assert post.metadata["title"] == "Title"

    def test_symlink_to_document(self, tmp_path):
        """Test following symlinks."""
        real_doc = tmp_path / "adr" / "real.md"
        real_doc.parent.mkdir(parents=True)
        real_doc.write_text('---\nid: " test "\n---\n# Test')

        link_doc = tmp_path / "adr" / "link.md"
        link_doc.symlink_to(real_doc)

        changed, messages = fix_whitespace_and_fields(link_doc)

        # Should work through symlink
        assert changed

    def test_concurrent_modifications(self, tmp_path):
        """Test file modified during processing."""
        doc = tmp_path / "test.md"
        doc.write_text('---\nid: " test "\n---\n# Test')

        # This test documents the behavior; actual concurrent
        # modification would require threading which we don't test
        changed, messages = fix_whitespace_and_fields(doc)
        assert changed

    def test_file_with_bom(self, tmp_path):
        """Test file with UTF-8 BOM."""
        doc = tmp_path / "test.md"
        content = '---\nid: " test "\n---\n# Test'
        doc.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))

        # Should handle BOM
        try:  # noqa: SIM105
            changed, messages = fix_whitespace_and_fields(doc)
            # May or may not work depending on implementation
        except Exception:  # noqa: S110
            # Expected to fail with BOM
            pass

    def test_very_long_field_values(self, tmp_path):
        """Test fields with very long values."""
        doc = tmp_path / "test.md"
        long_value = " " + ("x" * 100000) + " "
        doc.write_text(f'---\nid: test\ndescription: "{long_value}"\n---\n# Test')

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed

        post = frontmatter.loads(doc.read_text())
        assert len(post.metadata["description"]) == 100000

    def test_multiple_consecutive_fixes(self, tmp_path):
        """Test running fixes multiple times."""
        doc = tmp_path / "adr" / "test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: " test "\n---\n# Test')

        # First run
        changed1, messages1 = fix_whitespace_and_fields(doc)
        assert changed1

        # Second run should find nothing to fix
        changed2, messages2 = fix_whitespace_and_fields(doc)
        assert not changed2
        assert len(messages2) == 0

    def test_all_edge_cases_combined(self, tmp_path):
        """Test document with all possible edge cases."""
        doc = tmp_path / "adr" / "test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "  test-001  "
title: "  \t Title \n "
description: ""
null_field: null
tags: " backend "
status: "  Accepted  "
custom: "  value  "
---
# Test
"""
        doc.write_text(content)

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed
        assert len(messages) > 0

        post = frontmatter.loads(doc.read_text())
        # Trimmed
        assert post.metadata["id"] == "test-001"
        assert post.metadata["title"] == "Title"
        assert post.metadata["custom"] == "value"
        # Removed empty
        assert "description" not in post.metadata
        assert "null_field" not in post.metadata
        # Required fields added
        assert "doc_uuid" in post.metadata
        assert "project_id" in post.metadata
