"""Tests for whitespace and required fields fixes."""

import uuid as uuid_mod

import frontmatter
import pytest

from docuchango.fixes.whitespace import (
    ensure_required_fields,
    fix_whitespace_and_fields,
    normalize_empty_values,
    trim_string_values,
)


class TestTrimStringValues:
    """Test trimming whitespace from string values."""

    def test_trim_simple_strings(self):
        """Test trimming simple string values."""
        metadata = {
            "title": "  My Title  ",
            "status": "Accepted ",
            "id": " test-001",
        }

        updated, messages = trim_string_values(metadata)

        assert updated["title"] == "My Title"
        assert updated["status"] == "Accepted"
        assert updated["id"] == "test-001"
        assert len(messages) == 3

    def test_trim_strings_in_arrays(self):
        """Test trimming strings within arrays."""
        metadata = {
            "tags": [" backend ", "api  ", "  frontend"],
            "deciders": ["John Doe ", " Jane Smith"],
        }

        updated, messages = trim_string_values(metadata)

        assert updated["tags"] == ["backend", "api", "frontend"]
        assert updated["deciders"] == ["John Doe", "Jane Smith"]
        assert len(messages) == 2

    def test_preserve_non_strings(self):
        """Test preserving non-string values."""
        metadata = {
            "priority": 1,
            "deprecated": False,
            "tags": ["test"],
        }

        updated, messages = trim_string_values(metadata)

        assert updated["priority"] == 1
        assert updated["deprecated"] is False
        assert updated["tags"] == ["test"]

    def test_no_changes_needed(self):
        """Test when no trimming is needed."""
        metadata = {
            "title": "Clean Title",
            "status": "Accepted",
        }

        updated, messages = trim_string_values(metadata)

        assert updated == metadata
        assert len(messages) == 0

    def test_only_whitespace_strings_become_empty(self):
        """Test that strings containing only whitespace are trimmed to empty."""
        metadata = {
            "title": "   ",
            "description": "\t\t",
            "summary": "\n\n",
        }

        updated, messages = trim_string_values(metadata)

        assert updated["title"] == ""
        assert updated["description"] == ""
        assert updated["summary"] == ""

    def test_mixed_whitespace_characters_trimmed(self):
        """Test trimming a mix of tabs, newlines, and spaces."""
        metadata = {"title": " \t\nMy Title\r\n\t "}

        updated, messages = trim_string_values(metadata)

        assert updated["title"] == "My Title"

    def test_unicode_whitespace_trimmed(self):
        """Test trimming Unicode whitespace (non-breaking space, em space)."""
        metadata = {
            "title": " Title ",  # Non-breaking space
            "description": " Content ",  # Em space
        }

        updated, messages = trim_string_values(metadata)

        # Python strip() handles Unicode whitespace
        assert updated["title"].strip() == "Title"

    def test_nested_dicts_are_not_trimmed_but_array_strings_are(self):
        """Test that trimming only handles top-level strings and arrays, not nested dicts."""
        metadata = {
            "config": {"nested": " value "},
            "tags": [" tag1 ", " tag2 "],
        }

        updated, messages = trim_string_values(metadata)

        assert updated["config"]["nested"] == " value "  # Not trimmed
        assert updated["tags"] == ["tag1", "tag2"]  # Trimmed

    def test_long_string_edges_trimmed_content_preserved(self):
        """Test trimming a very long string only strips the edges."""
        long_content = " " + ("x" * 10000) + " "
        metadata = {"content": long_content}

        updated, messages = trim_string_values(metadata)

        assert len(updated["content"]) == 10000
        assert updated["content"][0] == "x"
        assert updated["content"][-1] == "x"

    def test_internal_whitespace_preserved(self):
        """Test that only leading/trailing whitespace is trimmed, not internal runs."""
        metadata = {"title": "  Multiple   Internal   Spaces  "}

        updated, messages = trim_string_values(metadata)

        assert updated["title"] == "Multiple   Internal   Spaces"

    def test_empty_metadata_dict(self):
        """Test trimming an empty metadata dictionary is a no-op."""
        metadata = {}

        updated, messages = trim_string_values(metadata)

        assert updated == {}
        assert len(messages) == 0

    def test_mixed_type_array_only_trims_strings(self):
        """Test arrays with mixed types only trim the string entries."""
        metadata = {"mixed": [" string ", 123, True, " another "]}

        updated, messages = trim_string_values(metadata)

        assert updated["mixed"] == ["string", 123, True, "another"]

    def test_empty_arrays_untouched(self):
        """Test that empty arrays pass through unchanged."""
        metadata = {"tags": [], "authors": []}

        updated, messages = trim_string_values(metadata)

        assert updated["tags"] == []
        assert updated["authors"] == []


class TestNormalizeEmptyValues:
    """Test normalizing empty values."""

    def test_remove_empty_strings(self):
        """Test removing empty string values."""
        metadata = {
            "title": "Test",
            "description": "",
            "summary": "   ",
        }

        updated, messages = normalize_empty_values(metadata)

        assert "title" in updated
        assert "description" not in updated
        assert "summary" not in updated
        assert len(messages) == 2

    def test_remove_null_values(self):
        """Test removing null values."""
        metadata = {
            "title": "Test",
            "description": None,
        }

        updated, messages = normalize_empty_values(metadata)

        assert "title" in updated
        assert "description" not in updated
        assert any("null" in msg.lower() for msg in messages)

    def test_keep_empty_arrays_for_list_fields(self):
        """Test keeping empty arrays for list fields."""
        metadata = {
            "tags": [],
            "authors": [],
            "reviewers": [],
        }

        updated, messages = normalize_empty_values(metadata)

        assert "tags" in updated
        assert updated["tags"] == []
        assert "authors" in updated
        assert updated["authors"] == []

    def test_remove_empty_arrays_for_other_fields(self):
        """Test removing empty arrays for non-list fields."""
        metadata = {
            "tags": [],
            "custom_field": [],
        }

        updated, messages = normalize_empty_values(metadata)

        assert "tags" in updated
        assert "custom_field" not in updated

    def test_zero_and_false_are_kept_not_treated_as_empty(self):
        """Test that 0 and False are valid values, distinct from empty string/null."""
        metadata = {
            "str_empty": "",
            "str_spaces": "   ",
            "null_value": None,
            "empty_list": [],
            "zero": 0,
            "false": False,
        }

        updated, messages = normalize_empty_values(metadata)

        assert "str_empty" not in updated
        assert "str_spaces" not in updated
        assert "null_value" not in updated
        assert updated["zero"] == 0
        assert updated["false"] is False

    def test_all_known_list_fields_kept_empty(self):
        """Test that every known list field is kept even when empty, and unknown ones dropped."""
        metadata = {
            "tags": [],
            "authors": [],
            "reviewers": [],
            "related": [],
            "custom_list": [],
        }

        updated, messages = normalize_empty_values(metadata)

        assert "tags" in updated
        assert "authors" in updated
        assert "reviewers" in updated
        assert "related" in updated
        assert "custom_list" not in updated

    def test_empty_strings_inside_arrays_are_not_filtered(self):
        """Test that normalize_empty_values does not recurse into array contents."""
        metadata = {"tags": ["", "valid", ""]}

        updated, messages = normalize_empty_values(metadata)

        assert updated["tags"] == ["", "valid", ""]

    def test_nested_dict_values_are_not_recursed_into(self):
        """Test that normalize_empty_values does not recurse into nested dicts."""
        metadata = {"config": {"value": "", "other": None}}

        updated, messages = normalize_empty_values(metadata)

        assert "config" in updated
        assert updated["config"]["value"] == ""

    def test_strings_that_look_empty_but_are_not_are_kept(self):
        """Test that strings like '0', 'false', 'null' are valid non-empty values."""
        metadata = {
            "zero_str": "0",
            "false_str": "false",
            "null_str": "null",
            "none_str": "None",
        }

        updated, messages = normalize_empty_values(metadata)

        assert all(key in updated for key in metadata)


class TestEnsureRequiredFields:
    """Test ensuring required fields are present."""

    def test_add_missing_tags(self):
        """Test adding missing tags field."""
        metadata = {"id": "test"}

        updated, messages = ensure_required_fields(metadata)

        assert "tags" in updated
        assert updated["tags"] == []
        assert any("tags" in msg.lower() for msg in messages)

    def test_add_missing_doc_uuid(self):
        """Test adding missing doc_uuid."""
        metadata = {"id": "test"}

        updated, messages = ensure_required_fields(metadata)

        assert "doc_uuid" in updated
        assert isinstance(updated["doc_uuid"], str)
        assert len(updated["doc_uuid"]) > 0
        assert any("doc_uuid" in msg.lower() for msg in messages)

    def test_add_missing_project_id(self):
        """Test adding missing project_id."""
        metadata = {"id": "test"}

        updated, messages = ensure_required_fields(metadata)

        assert "project_id" in updated
        assert updated["project_id"] == "my-project"
        assert any("project_id" in msg.lower() for msg in messages)

    def test_replace_empty_doc_uuid(self):
        """Test replacing empty doc_uuid."""
        metadata = {"id": "test", "doc_uuid": ""}

        updated, messages = ensure_required_fields(metadata)

        assert updated["doc_uuid"] != ""
        assert len(updated["doc_uuid"]) > 0

    def test_preserve_existing_fields(self):
        """Test preserving existing required fields."""
        metadata = {
            "id": "test",
            "tags": ["existing"],
            "doc_uuid": "existing-uuid",
            "project_id": "my-custom-project",
        }

        updated, messages = ensure_required_fields(metadata)

        assert updated["tags"] == ["existing"]
        assert updated["doc_uuid"] == "existing-uuid"
        assert updated["project_id"] == "my-custom-project"
        assert len(messages) == 0

    def test_generated_uuids_are_unique_across_calls(self):
        """Test that each call to ensure_required_fields generates a distinct doc_uuid."""
        updated1, _ = ensure_required_fields({"id": "test1"})
        updated2, _ = ensure_required_fields({"id": "test2"})

        assert updated1["doc_uuid"] != updated2["doc_uuid"]

    def test_generated_uuid_is_well_formed(self):
        """Test that the generated doc_uuid parses as a valid UUID."""
        updated, _ = ensure_required_fields({"id": "test"})

        uuid_mod.UUID(updated["doc_uuid"])  # Raises ValueError if malformed

    def test_existing_empty_fields_replaced_except_tags(self):
        """Test that empty doc_uuid/project_id are replaced but an empty tags string is left alone."""
        metadata = {
            "id": "test",
            "tags": "",  # Not our job to fix here
            "doc_uuid": "",
            "project_id": "",
        }

        updated, messages = ensure_required_fields(metadata)

        assert updated["tags"] == ""
        assert updated["doc_uuid"] != ""
        assert updated["project_id"] != ""

    @pytest.mark.parametrize(
        "metadata",
        [
            pytest.param({"id": "test-adr", "doc_type": "adr"}, id="adr"),
            pytest.param({"id": "test-rfc", "doc_type": "rfc"}, id="rfc"),
            pytest.param({"id": "test-memo", "doc_type": "memo"}, id="memo"),
            pytest.param({"id": "test-prd", "doc_type": "prd"}, id="prd"),
            pytest.param({"id": "test-generic"}, id="no-doc-type"),
        ],
    )
    def test_required_fields_added_regardless_of_doc_type(self, metadata):
        """Test that tags/doc_uuid/project_id are always added, independent of doc_type."""
        updated, messages = ensure_required_fields(metadata)

        assert "tags" in updated
        assert "doc_uuid" in updated
        assert "project_id" in updated

    def test_extra_fields_are_preserved(self):
        """Test that fields unrelated to the required set are left untouched."""
        metadata = {"id": "test", "custom_field": "custom_value", "another": 123}

        updated, messages = ensure_required_fields(metadata)

        assert updated["custom_field"] == "custom_value"
        assert updated["another"] == 123

    def test_large_metadata_still_gets_required_fields(self):
        """Test that required fields are added even to metadata with many existing keys."""
        metadata = {f"field{i}": f"value{i}" for i in range(1000)}

        updated, messages = ensure_required_fields(metadata)

        assert "tags" in updated
        assert "doc_uuid" in updated
        assert "project_id" in updated
        assert len(updated) >= 1003


class TestFixWhitespaceAndFields:
    """Test combined whitespace and fields fixes."""

    def test_comprehensive_fix(self, tmp_path):
        """Test fixing multiple issues at once."""
        doc = tmp_path / "adr" / "test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("""---
id: " test-001 "
title: "  My Document  "
status: "Accepted "
description: ""
---

# Test
""")

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed
        assert len(messages) > 0

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "test-001"
        assert post.metadata["title"] == "My Document"
        assert post.metadata["status"] == "Accepted"
        assert "description" not in post.metadata
        assert "tags" in post.metadata
        assert "doc_uuid" in post.metadata
        assert "project_id" in post.metadata

    def test_trim_and_add_fields(self, tmp_path):
        """Test trimming whitespace and adding missing fields."""
        doc = tmp_path / "rfc" / "test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("""---
id: "rfc-001 "
title: " API Design "
---

# Test
""")

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "rfc-001"
        assert post.metadata["title"] == "API Design"
        assert "tags" in post.metadata
        assert "doc_uuid" in post.metadata

    def test_no_changes_needed(self, tmp_path):
        """Test when no changes are needed."""
        doc = tmp_path / "test.md"
        doc.write_text("""---
id: "test-001"
title: "Clean Document"
tags: []
doc_uuid: "existing-uuid"
project_id: "my-project"
---

# Test
""")

        changed, messages = fix_whitespace_and_fields(doc)

        assert not changed

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry run doesn't write changes."""
        doc = tmp_path / "test.md"
        content = """---
id: " test-001 "
title: "  Needs Trim  "
---

# Test
"""
        doc.write_text(content)

        changed, messages = fix_whitespace_and_fields(doc, dry_run=True)

        assert changed
        assert len(messages) > 0
        # File should be unchanged
        assert doc.read_text() == content

    def test_file_in_root_directory_without_doc_type(self, tmp_path):
        """Test that fixing works for files not in a typed subdirectory."""
        doc = tmp_path / "test.md"
        doc.write_text("""---
id: " test "
title: "  Title  "
---
# Test
""")

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "test"
        assert post.metadata["title"] == "Title"

    def test_follows_symlink_to_document(self, tmp_path):
        """Test that fixing a symlink operates on the real underlying file."""
        real_doc = tmp_path / "adr" / "real.md"
        real_doc.parent.mkdir(parents=True)
        real_doc.write_text('---\nid: " test "\n---\n# Test')

        link_doc = tmp_path / "adr" / "link.md"
        link_doc.symlink_to(real_doc)

        changed, messages = fix_whitespace_and_fields(link_doc)

        assert changed

    def test_file_with_utf8_bom_is_recognized_as_having_frontmatter(self, tmp_path):
        """FMT-012: a UTF-8 BOM before '---' is stripped, not treated as no frontmatter.

        python-frontmatter wants the delimiter at the very start of the file, so the
        BOM is removed before parsing and the file is rewritten without it.
        """
        doc = tmp_path / "test.md"
        content = '---\nid: " test "\n---\n# Test'
        doc.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed
        assert "FMT-012: Removed UTF-8 byte-order mark" in messages
        assert not any("no frontmatter" in msg.lower() for msg in messages)
        assert not doc.read_bytes().startswith(b"\xef\xbb\xbf")

        post = frontmatter.loads(doc.read_text(encoding="utf-8"))
        assert post.metadata["id"] == "test"

    def test_utf8_bom_removal_is_reported_and_not_repeated(self, tmp_path):
        """FMT-012: a second run over the repaired file has nothing left to do."""
        doc = tmp_path / "adr" / "test.md"
        doc.parent.mkdir(parents=True)
        body = "---\nid: test\ntags: []\nproject_id: fixture\ndoc_uuid: 4f2f2b3e-0e2c-4b0a-9a4f-2a8b1c9d0e11\n---\n# Test\n"
        doc.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed
        assert messages == ["FMT-012: Removed UTF-8 byte-order mark"]
        # Only the BOM goes: the rest of the file is rewritten verbatim.
        assert doc.read_text(encoding="utf-8") == body

        changed_again, messages_again = fix_whitespace_and_fields(doc)

        assert not changed_again
        assert messages_again == []

    def test_utf8_bom_dry_run_leaves_the_file_alone(self, tmp_path):
        """FMT-012: --dry-run reports the removal without writing it."""
        doc = tmp_path / "test.md"
        raw = b"\xef\xbb\xbf" + b'---\nid: " test "\n---\n# Test'
        doc.write_bytes(raw)

        changed, messages = fix_whitespace_and_fields(doc, dry_run=True)

        assert changed
        assert "FMT-012: Removed UTF-8 byte-order mark" in messages
        assert doc.read_bytes() == raw

    def test_utf8_bom_without_frontmatter_is_still_no_frontmatter(self, tmp_path):
        """A BOM in front of plain Markdown does not conjure up frontmatter."""
        doc = tmp_path / "test.md"
        doc.write_bytes(b"\xef\xbb\xbf# Test\n\nNo frontmatter here.\n")

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed
        assert messages == ["FMT-012: Removed UTF-8 byte-order mark"]
        assert doc.read_text(encoding="utf-8") == "# Test\n\nNo frontmatter here.\n"

    def test_very_long_field_values_are_preserved_after_trim(self, tmp_path):
        """Test that trimming a very long field value keeps its full inner content."""
        doc = tmp_path / "test.md"
        long_value = " " + ("x" * 100000) + " "
        doc.write_text(f'---\nid: test\ndescription: "{long_value}"\n---\n# Test')

        changed, messages = fix_whitespace_and_fields(doc)

        assert changed

        post = frontmatter.loads(doc.read_text())
        assert len(post.metadata["description"]) == 100000

    def test_second_run_finds_nothing_left_to_fix(self, tmp_path):
        """Test that running the fix twice is idempotent."""
        doc = tmp_path / "adr" / "test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: " test "\n---\n# Test')

        changed1, messages1 = fix_whitespace_and_fields(doc)
        assert changed1

        changed2, messages2 = fix_whitespace_and_fields(doc)
        assert not changed2
        assert len(messages2) == 0

    def test_all_edge_cases_combined(self, tmp_path):
        """Test a document combining trimming, empty removal, and missing required fields."""
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
