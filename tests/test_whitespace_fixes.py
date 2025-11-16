"""Tests for whitespace and required fields fixes."""

from pathlib import Path

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


class TestEnsureRequiredFields:
    """Test ensuring required fields are present."""

    def test_add_missing_tags(self):
        """Test adding missing tags field."""
        metadata = {"id": "test"}

        updated, messages = ensure_required_fields(metadata, "adr")

        assert "tags" in updated
        assert updated["tags"] == []
        assert any("tags" in msg.lower() for msg in messages)

    def test_add_missing_doc_uuid(self):
        """Test adding missing doc_uuid."""
        metadata = {"id": "test"}

        updated, messages = ensure_required_fields(metadata, "adr")

        assert "doc_uuid" in updated
        assert isinstance(updated["doc_uuid"], str)
        assert len(updated["doc_uuid"]) > 0
        assert any("doc_uuid" in msg.lower() for msg in messages)

    def test_add_missing_project_id(self):
        """Test adding missing project_id."""
        metadata = {"id": "test"}

        updated, messages = ensure_required_fields(metadata, "adr")

        assert "project_id" in updated
        assert updated["project_id"] == "my-project"
        assert any("project_id" in msg.lower() for msg in messages)

    def test_replace_empty_doc_uuid(self):
        """Test replacing empty doc_uuid."""
        metadata = {"id": "test", "doc_uuid": ""}

        updated, messages = ensure_required_fields(metadata, "adr")

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

        updated, messages = ensure_required_fields(metadata, "adr")

        assert updated["tags"] == ["existing"]
        assert updated["doc_uuid"] == "existing-uuid"
        assert updated["project_id"] == "my-custom-project"
        assert len(messages) == 0


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
