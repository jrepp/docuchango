"""Tests for frontmatter auto-fixes."""

import tempfile
from datetime import datetime
from pathlib import Path

import frontmatter
import pytest

from docuchango.fixes.frontmatter import (
    add_missing_frontmatter,
    fix_all_frontmatter,
    fix_date_format,
    fix_status_value,
    get_doc_type,
)


class TestGetDocType:
    """Test document type detection."""

    def test_adr_detection(self):
        """Test ADR document type detection."""
        assert get_doc_type(Path("docs/adr/adr-001-test.md")) == "adr"
        assert get_doc_type(Path("/path/to/adr/document.md")) == "adr"

    def test_rfc_detection(self):
        """Test RFC document type detection."""
        assert get_doc_type(Path("docs/rfcs/rfc-001-test.md")) == "rfc"
        assert get_doc_type(Path("/path/to/rfcs/document.md")) == "rfc"

    def test_memo_detection(self):
        """Test memo document type detection."""
        assert get_doc_type(Path("docs/memos/memo-001-test.md")) == "memo"
        assert get_doc_type(Path("/path/to/memos/document.md")) == "memo"

    def test_prd_detection(self):
        """Test PRD document type detection."""
        assert get_doc_type(Path("docs/prd/prd-001-test.md")) == "prd"
        assert get_doc_type(Path("/path/to/prd/document.md")) == "prd"

    def test_no_doc_type(self):
        """Test when document type cannot be determined."""
        assert get_doc_type(Path("docs/random/file.md")) is None
        assert get_doc_type(Path("file.md")) is None


class TestFixStatusValue:
    """Test status value fixing."""

    def test_fix_draft_to_proposed_adr(self, tmp_path):
        """Test fixing 'Draft' to 'Proposed' for ADR."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Draft
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        assert changed
        assert "Proposed" in msg

        # Verify the change
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["status"] == "Proposed"

    def test_fix_pending_to_in_review_rfc(self, tmp_path):
        """Test fixing 'pending' to 'In Review' for RFC."""
        doc = tmp_path / "rfcs" / "rfc-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "rfc-001"
title: "Test RFC"
status: pending
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        assert changed
        assert "In Review" in msg

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["status"] == "In Review"

    def test_already_valid_status(self, tmp_path):
        """Test that valid status is not changed."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Accepted
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        assert not changed
        assert "already valid" in msg.lower()

    def test_no_status_field(self, tmp_path):
        """Test when status field is missing."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)

        changed, msg = fix_status_value(doc)
        assert not changed
        assert "No status field" in msg

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry run doesn't write changes."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Draft
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)
        original_content = content

        changed, msg = fix_status_value(doc, dry_run=True)
        assert changed
        assert doc.read_text() == original_content


class TestFixDateFormat:
    """Test date format fixing."""

    def test_fix_slash_format(self, tmp_path):
        """Test fixing date with slashes."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Accepted
date: 2025/01/26
---

# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        assert changed
        assert "2025-01-26" in msg

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["date"] == "2025-01-26"

    def test_fix_dot_format(self, tmp_path):
        """Test fixing date with dots."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Accepted
date: 26.01.2025
---

# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        assert changed
        assert "2025-01-26" in msg

    def test_fix_long_month_format(self, tmp_path):
        """Test fixing date with long month name."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Accepted
date: January 26, 2025
---

# Test
"""
        doc.write_text(content)

        changed, msg = fix_date_format(doc)
        assert changed
        assert "2025-01-26" in msg

    def test_already_iso_format(self, tmp_path):
        """Test that ISO 8601 format date object is converted to string."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Accepted
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)

        # YAML parser will convert the date string to a date object
        # so our fix should convert it back to a string
        changed, msg = fix_date_format(doc)
        assert changed
        assert "2025-01-26" in msg

        # Verify it's now a string in the file
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["date"] == "2025-01-26"
        assert isinstance(post.metadata["date"], str)

    def test_convert_datetime_object(self, tmp_path):
        """Test converting datetime object to string."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        # Create frontmatter with datetime object
        post = frontmatter.Post("")
        post.metadata = {
            "id": "adr-001",
            "title": "Test ADR",
            "status": "Accepted",
            "date": datetime(2025, 1, 26),
        }
        post.content = "# Test"

        doc.write_text(frontmatter.dumps(post))

        changed, msg = fix_date_format(doc)
        assert changed
        assert "2025-01-26" in msg

        # Verify it's now a string
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["date"] == "2025-01-26"
        assert isinstance(post.metadata["date"], str)


class TestAddMissingFrontmatter:
    """Test adding missing frontmatter."""

    def test_add_frontmatter_adr(self, tmp_path):
        """Test adding frontmatter to ADR without any."""
        doc = tmp_path / "adr" / "adr-001-use-python.md"
        doc.parent.mkdir(parents=True)

        content = """# Use Python for Implementation

This is the content.
"""
        doc.write_text(content)

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        assert "adr-001" in msg

        # Verify frontmatter was added
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "adr-001"
        assert "Python" in post.metadata["title"]
        assert post.metadata["status"] == "Proposed"
        assert "deciders" in post.metadata
        assert "doc_uuid" in post.metadata

    def test_add_frontmatter_rfc(self, tmp_path):
        """Test adding frontmatter to RFC."""
        doc = tmp_path / "rfcs" / "rfc-042-api-design.md"
        doc.parent.mkdir(parents=True)

        content = """# API Design Proposal

Content here.
"""
        doc.write_text(content)

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        assert "rfc-042" in msg

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "rfc-042"
        assert post.metadata["status"] == "Draft"
        assert "deciders" not in post.metadata  # RFC shouldn't have deciders

    def test_frontmatter_already_exists(self, tmp_path):
        """Test that existing frontmatter is not overwritten."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Existing"
---

# Test
"""
        doc.write_text(content)

        changed, msg = add_missing_frontmatter(doc)
        assert not changed
        assert "already exists" in msg.lower()

    def test_uuid_is_valid(self, tmp_path):
        """Test that generated UUID is valid."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("# Test")

        changed, msg = add_missing_frontmatter(doc)
        assert changed

        post = frontmatter.loads(doc.read_text())
        doc_uuid = post.metadata["doc_uuid"]

        # Verify it's a valid UUID format
        import uuid as uuid_mod

        try:
            uuid_mod.UUID(doc_uuid)
        except ValueError:
            pytest.fail(f"Invalid UUID: {doc_uuid}")


class TestFixAllFrontmatter:
    """Test applying all fixes together."""

    def test_fix_all_on_document(self, tmp_path):
        """Test fixing multiple issues in one document."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Draft
date: 2025/01/26
---

# Test
"""
        doc.write_text(content)

        messages = fix_all_frontmatter(doc)

        # Should fix both status and date
        assert len(messages) >= 2
        assert any("status" in msg.lower() for msg in messages)
        assert any("date" in msg.lower() for msg in messages)

        # Verify fixes
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["status"] == "Proposed"
        assert post.metadata["date"] == "2025-01-26"

    def test_fix_all_dry_run(self, tmp_path):
        """Test that dry run doesn't persist changes."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        content = """---
id: "adr-001"
title: "Test ADR"
status: Draft
date: 2025/01/26
---

# Test
"""
        doc.write_text(content)
        original = content

        messages = fix_all_frontmatter(doc, dry_run=True)

        # Should identify fixes but not apply them
        assert len(messages) >= 2
        assert doc.read_text() == original
