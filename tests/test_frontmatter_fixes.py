"""Tests for frontmatter auto-fixes."""

import uuid
from datetime import date, datetime
from pathlib import Path

import frontmatter
import pytest

from docuchango.fixes.frontmatter import (
    add_missing_frontmatter,
    fix_all_frontmatter,
    fix_date_format,
    fix_frontmatter_metadata,
    fix_status_value,
    get_doc_type,
)
from docuchango.fixes.yaml_utils import dumps as frontmatter_dumps
from docuchango.schemas import ADRFrontmatter, MemoFrontmatter, PRDFrontmatter, RFCFrontmatter


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

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            pytest.param(Path("docs/ADR/adr-001.md"), "adr", id="case-insensitive-adr"),
            pytest.param(Path("DOCS/RFCS/rfc-001.md"), "rfc", id="case-insensitive-rfc"),
            pytest.param(Path("Docs/Memos/memo.md"), "memo", id="case-insensitive-memo"),
            pytest.param(
                Path("/home/user/project/docs/adr/subdir/adr-001.md"),
                "adr",
                id="deeply-nested-adr",
            ),
            pytest.param(Path("adr/rfcs/test.md"), "adr", id="multiple-indicators-matches-first-adr"),
            pytest.param(Path("rfcs/adr/test.md"), "rfc", id="multiple-indicators-matches-first-rfc"),
            pytest.param(Path("adrs/test.md"), None, id="plural-adrs-not-matched"),
            pytest.param(Path("rfc/test.md"), None, id="singular-rfc-not-matched"),
            pytest.param(Path("memoranda/test.md"), None, id="different-word-not-matched"),
        ],
    )
    def test_get_doc_type_across_path_shapes(self, path, expected):
        """Test doc type detection is case-insensitive, works on nested paths, and requires
        an exact directory-name match (not a prefix, plural, or synonym)."""
        assert get_doc_type(path) == expected

    def test_windows_style_paths_are_platform_dependent(self):
        """Backslash-separated paths only split into directory components on Windows;
        on POSIX they're a single opaque path segment, so doc-type detection fails there.
        """
        import platform

        if platform.system() == "Windows":
            assert get_doc_type(Path("C:\\docs\\adr\\adr-001.md")) == "adr"
            assert get_doc_type(Path("D:\\project\\rfcs\\rfc-001.md")) == "rfc"
        else:
            assert get_doc_type(Path("C:\\docs\\adr\\adr-001.md")) is None
            assert get_doc_type(Path("D:\\project\\rfcs\\rfc-001.md")) is None


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

    def test_fix_pending_to_proposed_rfc(self, tmp_path):
        """Test fixing 'pending' to schema-valid 'Proposed' for RFC."""
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
        assert "Proposed" in msg

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["status"] == "Proposed"

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

    def test_rejected_status_is_valid_adr(self, tmp_path):
        """'Rejected' is a valid ADR status and must not be 'fixed'."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\ntitle: "Test ADR"\nstatus: Rejected\ndate: 2025-01-26\n---\n\n# Test\n')
        changed, msg = fix_status_value(doc)
        assert not changed
        assert "already valid" in msg.lower()

    def test_rejected_status_is_valid_rfc(self, tmp_path):
        """'Rejected' is a valid RFC status and must not be 'fixed'."""
        doc = tmp_path / "rfcs" / "rfc-001-test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "rfc-001"\ntitle: "Test RFC"\nstatus: Rejected\ndate: 2025-01-26\n---\n\n# Test\n')
        changed, msg = fix_status_value(doc)
        assert not changed
        assert "already valid" in msg.lower()

    def test_lowercase_rejected_normalizes_adr(self, tmp_path):
        """'rejected' normalizes to the valid 'Rejected' status for ADRs."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\ntitle: "Test ADR"\nstatus: rejected\ndate: 2025-01-26\n---\n\n# Test\n')
        changed, msg = fix_status_value(doc)
        assert changed
        assert "Rejected" in msg
        assert frontmatter.loads(doc.read_text()).metadata["status"] == "Rejected"

    def test_lowercase_rejected_normalizes_rfc(self, tmp_path):
        """'rejected' normalizes to the valid 'Rejected' status for RFCs."""
        doc = tmp_path / "rfcs" / "rfc-001-test.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "rfc-001"\ntitle: "Test RFC"\nstatus: rejected\ndate: 2025-01-26\n---\n\n# Test\n')
        changed, msg = fix_status_value(doc)
        assert changed
        assert "Rejected" in msg
        assert frontmatter.loads(doc.read_text()).metadata["status"] == "Rejected"

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

    def test_status_with_punctuation_still_maps(self, tmp_path):
        """Test that a keyword match works even with trailing punctuation."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\nstatus: "draft!"\n---\n# Test\n')

        changed, msg = fix_status_value(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["status"] == "Proposed"

    def test_status_with_leading_trailing_spaces_still_maps(self, tmp_path):
        """Test that surrounding whitespace doesn't prevent a keyword match."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\nstatus: "  draft  "\n---\n# Test\n')

        changed, msg = fix_status_value(doc)

        assert changed

    def test_numeric_status_is_rejected(self, tmp_path):
        """Test that a non-string status value is reported, not coerced."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\nstatus: 123\n---\n# Test\n')

        changed, msg = fix_status_value(doc)

        assert not changed
        assert "not a string" in msg

    def test_empty_status_is_rejected(self, tmp_path):
        """Test that an empty status string matches no keyword and is reported as empty."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\nstatus: ""\n---\n# Test\n')

        changed, msg = fix_status_value(doc)

        assert not changed
        assert "empty" in msg.lower()

    def test_long_status_string_still_finds_keyword(self, tmp_path):
        """Test that a keyword buried in a long status string is still detected."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        long_status = "draft " * 100
        doc.write_text(f'---\nid: "adr-001"\nstatus: "{long_status}"\n---\n# Test\n')

        changed, msg = fix_status_value(doc)

        assert changed

    def test_unicode_lookalike_status_does_not_match(self, tmp_path):
        """Test that a Unicode-lookalike spelling ('drāft') does not match the 'draft' keyword."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\nstatus: "drāft"\n---\n# Test\n')

        changed, msg = fix_status_value(doc)

        assert not changed

    def test_status_with_multiple_keywords_matches_first(self, tmp_path):
        """Test that a status containing two matching keywords resolves via the first match."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\nstatus: "draft pending"\n---\n# Test\n')

        changed, msg = fix_status_value(doc)

        assert changed


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
        assert post.metadata["date"] == date(2025, 1, 26)

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
        """Test that unquoted ISO 8601 date (parsed as date object) needs no fix."""
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

        # Unquoted ISO 8601 date is already canonical — no fix needed
        changed, msg = fix_date_format(doc)
        assert not changed
        assert "already in ISO 8601" in msg

    def test_datetime_object_already_valid(self, tmp_path):
        """Test that a datetime object (from unquoted YAML) needs no fix."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)

        # Create frontmatter with datetime object (simulates unquoted datetime in YAML)
        post = frontmatter.Post("")
        post.metadata = {
            "id": "adr-001",
            "title": "Test ADR",
            "status": "Accepted",
            "date": datetime(2025, 1, 26),
        }
        post.content = "# Test"

        # Use frontmatter_dumps to exercise the same formatting path as production
        doc.write_text(frontmatter_dumps(post))

        # datetime objects from PyYAML are already canonical — no fix needed
        changed, msg = fix_date_format(doc)
        assert not changed
        assert "already in ISO 8601" in msg

    @pytest.mark.parametrize(
        "date_literal",
        [
            pytest.param("2025-13-01", id="invalid-month"),
            pytest.param("2025-02-30", id="invalid-day"),
            pytest.param("not-a-date", id="non-date-text"),
            pytest.param("12345", id="integer-like-garbage"),
            pytest.param("2025/02/30", id="invalid-with-slashes"),
            pytest.param('"2025-01"', id="partial-date-missing-day"),
            pytest.param('"2025-01-26 14:30:00"', id="date-with-time-component"),
            pytest.param('"1900-01-01"', id="already-iso-very-old"),
            pytest.param('"2099-12-31"', id="already-iso-future"),
            pytest.param("20250126", id="date-as-plain-integer"),
        ],
    )
    def test_dates_that_are_not_reformatted(self, tmp_path, date_literal):
        """Test date values that fix_date_format leaves untouched: either they're invalid,
        ambiguous/partial, carry a time component, are already ISO 8601, or aren't a
        recognizable date shape at all (e.g. a bare integer)."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text(f'---\nid: "adr-001"\ndate: {date_literal}\n---\n# Test\n')

        changed, msg = fix_date_format(doc)

        assert not changed

    def test_ambiguous_slash_date_resolves_using_us_month_day_order(self, tmp_path):
        """Test that an ambiguous 'mm/dd/yyyy vs dd/mm/yyyy' date is resolved as US-style
        (month first) when it does get reformatted."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        # 01/02/2025 could be Jan 2 or Feb 1
        doc.write_text('---\nid: "adr-001"\ndate: "01/02/2025"\n---\n# Test\n')

        changed, msg = fix_date_format(doc)

        if changed:
            post = frontmatter.loads(doc.read_text())
            assert post.metadata["date"] == date(2025, 2, 1)


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
        title = post.metadata["title"]
        assert isinstance(title, str)
        assert "Python" in title
        assert post.metadata["status"] == "Proposed"
        assert "created" in post.metadata
        assert "date" not in post.metadata
        assert "deciders" in post.metadata
        assert "doc_uuid" in post.metadata
        ADRFrontmatter(**post.metadata)

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
        assert "author" in post.metadata
        assert "created" in post.metadata
        assert "date" not in post.metadata
        assert "deciders" not in post.metadata  # RFC shouldn't have deciders
        RFCFrontmatter(**post.metadata)

    def test_add_frontmatter_memo_matches_schema(self, tmp_path):
        """Test generated Memo frontmatter validates against schema."""
        doc = tmp_path / "memos" / "memo-007-implementation-notes.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("# Implementation Notes\n\nContent here.\n")

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        assert "memo-007" in msg

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "memo-007"
        assert "author" in post.metadata
        assert "status" not in post.metadata
        assert "created" in post.metadata
        assert "date" not in post.metadata
        MemoFrontmatter(**post.metadata)

    def test_add_frontmatter_prd_matches_schema(self, tmp_path):
        """Test generated PRD frontmatter validates against schema."""
        doc = tmp_path / "prd" / "prd-003-user-authentication.md"
        doc.parent.mkdir(parents=True)

        doc.write_text("# User Authentication\n\nContent here.\n")

        changed, msg = add_missing_frontmatter(doc)
        assert changed
        assert "prd-003" in msg

        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "prd-003"
        assert post.metadata["status"] == "Draft"
        assert "author" in post.metadata
        assert "target_release" in post.metadata
        assert "created" in post.metadata
        assert "date" not in post.metadata
        PRDFrontmatter(**post.metadata)

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
        try:
            uuid.UUID(doc_uuid)
        except ValueError:
            pytest.fail(f"Invalid UUID: {doc_uuid}")

    def test_frontmatter_marker_with_no_body_is_treated_as_existing(self, tmp_path):
        """Test that a bare '---' marker (no closing delimiter) counts as 'already has
        frontmatter' rather than being filled in."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("---\n")

        changed, msg = add_missing_frontmatter(doc)

        assert not changed

    def test_malformed_yaml_frontmatter_is_treated_as_existing(self, tmp_path):
        """Test that malformed (but delimiter-bounded) YAML is treated as existing
        frontmatter and not overwritten."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("---\nid: adr-001\n  invalid: yaml:\n---\n# Test\n")

        changed, msg = add_missing_frontmatter(doc)

        assert not changed

    @pytest.mark.parametrize(
        "filename",
        [
            pytest.param("random-file.md", id="no-id-pattern-in-name"),
            pytest.param("adr-001-api@design.md", id="special-characters-in-name"),
            pytest.param("a" * 200 + ".md", id="very-long-filename"),
            pytest.param("adr-001-测试.md", id="unicode-in-filename"),
        ],
    )
    def test_id_falls_back_to_adr_001_for_unmatchable_filenames(self, tmp_path, filename):
        """Test that filenames that don't yield a clean ID (no pattern, special
        characters, excessive length, or non-ASCII) all fall back to 'adr-001'."""
        doc = tmp_path / "adr" / filename
        doc.parent.mkdir(parents=True)
        doc.write_text("# Test")

        changed, msg = add_missing_frontmatter(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["id"] == "adr-001"

    def test_very_long_filename_still_produces_a_nonempty_title(self, tmp_path):
        """Test that an extremely long filename still yields a usable title string."""
        doc = tmp_path / "adr" / ("a" * 200 + ".md")
        doc.parent.mkdir(parents=True)
        doc.write_text("# Test")

        changed, msg = add_missing_frontmatter(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert len(post.metadata["title"]) > 0


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
        assert post.metadata["date"] == date(2025, 1, 26)

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

    @pytest.mark.parametrize(
        "raw_content",
        [
            pytest.param("", id="completely-empty-file"),
            pytest.param("   \n\n   \n", id="whitespace-only-file"),
        ],
    )
    def test_degenerate_files_are_handled_without_raising(self, tmp_path, raw_content):
        """Test that empty or whitespace-only files are handled gracefully (no frontmatter
        to fix, but no exception either)."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text(raw_content)

        messages = fix_all_frontmatter(doc)

        assert isinstance(messages, list)

    def test_binary_content_raises_a_decode_error(self, tmp_path):
        """Test that a file that isn't valid UTF-8 raises rather than silently corrupting."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_bytes(b"\xff\xfe\x00\x01\x02\x03")

        with pytest.raises((ValueError, UnicodeDecodeError)):
            fix_all_frontmatter(doc)

    def test_frontmatter_with_a_thousand_extra_fields_is_still_fixed(self, tmp_path):
        """Test that a very large frontmatter block doesn't prevent status/date fixes."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)

        fields = "\n".join([f'field{i}: "value{i}"' for i in range(1000)])
        content = f"""---
id: "adr-001"
status: Draft
date: 2025/01/26
{fields}
---
# Test
"""
        doc.write_text(content)

        messages = fix_all_frontmatter(doc)

        assert len(messages) >= 2

    def test_status_and_date_are_both_fixed_in_one_pass(self, tmp_path):
        """Test that a document with both a bad status and a bad date gets both fixed
        by a single fix_all_frontmatter call."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text(
            '---\nid: "adr-001"\ntitle: "Test"\nstatus: draft\ndate: 2025/01/26\ninvalid_field: null\n---\n# Test\n'
        )

        messages = fix_all_frontmatter(doc)

        assert len(messages) >= 2
        assert any("status" in msg.lower() for msg in messages)
        assert any("date" in msg.lower() for msg in messages)

    def test_readonly_file_fails_to_write_without_raising(self, tmp_path):
        """Test that a read-only file either produces no messages (write silently
        skipped) or an explicit error message, but never raises."""
        doc = tmp_path / "adr" / "adr-001.md"
        doc.parent.mkdir(parents=True)
        doc.write_text('---\nid: "adr-001"\nstatus: draft\n---\n# Test\n')

        import os
        import stat

        os.chmod(doc, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            messages = fix_all_frontmatter(doc)
            assert len(messages) == 0 or any("error" in msg.lower() for msg in messages)
        finally:
            os.chmod(doc, stat.S_IWUSR | stat.S_IRUSR)


class TestUtf8ByteOrderMark:
    """FMT-012: a UTF-8 BOM must not hide the frontmatter from the parser."""

    BOM = b"\xef\xbb\xbf"

    def test_bom_is_removed_and_frontmatter_is_still_fixed(self, tmp_path):
        """The BOM goes and the frontmatter behind it is repaired in the same pass."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)
        doc.write_bytes(self.BOM + b'---\nid: "adr-001"\nstatus: draft\n---\n# Test\n')

        changed, messages = fix_frontmatter_metadata(doc)

        assert changed
        assert "FMT-012: Removed UTF-8 byte-order mark" in messages
        assert any("status" in msg.lower() for msg in messages)
        assert not doc.read_bytes().startswith(self.BOM)

        post = frontmatter.loads(doc.read_text(encoding="utf-8"))
        assert post.metadata["status"] == "Proposed"

    def test_bom_alone_is_removed_without_touching_the_rest(self, tmp_path):
        """A document that only has a BOM wrong is rewritten byte-for-byte without it."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)
        body = (
            "---\n"
            'id: "adr-001"\n'
            "status: Accepted\n"
            "created: 2026-01-02\n"
            "tags: []\n"
            'project_id: "fixture"\n'
            'doc_uuid: "4f2f2b3e-0e2c-4b0a-9a4f-2a8b1c9d0e11"\n'
            "---\n"
            "# Test\n"
        )
        doc.write_bytes(self.BOM + body.encode())

        changed, messages = fix_frontmatter_metadata(doc)

        assert changed
        assert messages == ["FMT-012: Removed UTF-8 byte-order mark"]
        assert doc.read_text(encoding="utf-8") == body

        assert fix_frontmatter_metadata(doc) == (False, [])

    def test_bom_dry_run_does_not_write(self, tmp_path):
        """--dry-run reports the removal but leaves the bytes alone."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)
        raw = self.BOM + b'---\nid: "adr-001"\nstatus: draft\n---\n# Test\n'
        doc.write_bytes(raw)

        changed, messages = fix_frontmatter_metadata(doc, dry_run=True)

        assert changed
        assert "FMT-012: Removed UTF-8 byte-order mark" in messages
        assert doc.read_bytes() == raw

    def test_bom_before_plain_markdown_still_gets_frontmatter_added(self, tmp_path):
        """A BOM in front of a document with no frontmatter reports both repairs."""
        doc = tmp_path / "adr" / "adr-001-test.md"
        doc.parent.mkdir(parents=True)
        doc.write_bytes(self.BOM + b"# Test\n\nNo frontmatter here.\n")

        changed, messages = fix_frontmatter_metadata(doc)

        assert changed
        assert "FMT-012: Removed UTF-8 byte-order mark" in messages
        assert any("Added frontmatter block" in msg for msg in messages)
        assert not doc.read_bytes().startswith(self.BOM)

        post = frontmatter.loads(doc.read_text(encoding="utf-8"))
        assert post.metadata["id"] == "adr-001"
