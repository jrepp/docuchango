"""Tests for document ID compression."""

from click.testing import CliRunner

from docuchango.cli import main
from docuchango.fixes.id_compression import audit_missing_document_references, compress_document_ids


def _write_memo(path, memo_id: str, title: str, body: str = ""):
    path.write_text(
        f"""---
id: {memo_id}
title: {title}
status: Draft
created: 2026-01-01T00:00:00Z
author: Test User
tags: []
---

# {title}

{body}
""",
        encoding="utf-8",
    )


def test_compress_document_ids_renames_files_and_updates_references(tmp_path):
    memos_dir = tmp_path / "memos"
    memos_dir.mkdir()

    memo_001 = memos_dir / "memo-001-first.md"
    memo_010 = memos_dir / "memo-010-second.md"
    memo_011 = memos_dir / "memo-011-third.md"
    _write_memo(memo_001, "memo-001", "First Memo")
    _write_memo(memo_010, "memo-010", "Second Memo", "References MEMO-011 and /memos/memo-001.")
    _write_memo(memo_011, "memo-011", "Third Memo")

    readme = tmp_path / "README.md"
    readme.write_text(
        "See [second](memos/memo-010-second.md), [third](/memos/MEMO-011), and memo-010.",
        encoding="utf-8",
    )

    result = compress_document_ids(tmp_path, [memo_001, memo_010, memo_011], doc_type="memo")

    assert [(change.old_id, change.new_id) for change in result.changes] == [
        ("memo-010", "memo-002"),
        ("memo-011", "memo-003"),
    ]
    assert not memo_010.exists()
    assert not memo_011.exists()
    assert (memos_dir / "memo-002-second.md").exists()
    assert (memos_dir / "memo-003-third.md").exists()

    second_content = (memos_dir / "memo-002-second.md").read_text(encoding="utf-8")
    assert "id: memo-002" in second_content
    assert "MEMO-003" in second_content
    assert "memo-010" not in second_content

    readme_content = readme.read_text(encoding="utf-8")
    assert "memos/memo-002-second.md" in readme_content
    assert "/memos/MEMO-003" in readme_content
    assert "memo-002" in readme_content
    assert "memo-010" not in readme_content
    assert result.stale_references == []


def test_compress_document_ids_preserves_new_id_when_it_was_an_old_id(tmp_path):
    adr_dir = tmp_path / "adr"
    adr_dir.mkdir()

    adr_001 = adr_dir / "adr-001-first.md"
    adr_003 = adr_dir / "adr-003-second.md"
    adr_032 = adr_dir / "adr-032-third.md"
    _write_memo(adr_001, "adr-001", "First ADR")
    _write_memo(adr_003, "adr-003", "Second ADR")
    _write_memo(adr_032, "adr-032", "Third ADR", "References ADR-003 and ADR-032.")

    result = compress_document_ids(tmp_path, [adr_001, adr_003, adr_032], doc_type="adr")

    assert [(change.old_id, change.new_id) for change in result.changes] == [
        ("adr-003", "adr-002"),
        ("adr-032", "adr-003"),
    ]
    new_third = adr_dir / "adr-003-third.md"
    assert new_third.exists()
    new_third_content = new_third.read_text(encoding="utf-8")
    assert "id: adr-003" in new_third_content
    assert "ADR-002 and ADR-003" in new_third_content


def test_compress_document_ids_syncs_frontmatter_to_filename(tmp_path):
    memos_dir = tmp_path / "memos"
    memos_dir.mkdir()

    memo_001 = memos_dir / "memo-001-first.md"
    _write_memo(memo_001, "memo-999", "First Memo")

    result = compress_document_ids(tmp_path, [memo_001], doc_type="memo")

    assert result.changes == []
    assert result.synced_files == [memo_001]
    assert "id: memo-001" in memo_001.read_text(encoding="utf-8")


def test_compress_document_ids_dry_run_does_not_modify_files(tmp_path):
    memos_dir = tmp_path / "memos"
    memos_dir.mkdir()

    memo_001 = memos_dir / "memo-001-first.md"
    memo_010 = memos_dir / "memo-010-second.md"
    _write_memo(memo_001, "memo-001", "First Memo")
    _write_memo(memo_010, "memo-010", "Second Memo")
    original = memo_010.read_text(encoding="utf-8")

    result = compress_document_ids(tmp_path, [memo_001, memo_010], doc_type="memo", dry_run=True)

    assert [(change.old_id, change.new_id) for change in result.changes] == [("memo-010", "memo-002")]
    assert memo_010.exists()
    assert not (memos_dir / "memo-002-second.md").exists()
    assert memo_010.read_text(encoding="utf-8") == original
    assert result.stale_references == []


def test_audit_missing_document_references_reports_stale_refs(tmp_path):
    memos_dir = tmp_path / "memos"
    memos_dir.mkdir()

    memo_001 = memos_dir / "memo-001-first.md"
    _write_memo(memo_001, "memo-001", "First Memo")
    (tmp_path / "notes.md").write_text("memo-999 is stale\n", encoding="utf-8")

    hits = audit_missing_document_references(tmp_path, [memo_001])

    assert len(hits) == 1
    assert hits[0].file_path == tmp_path / "notes.md"
    assert hits[0].line_number == 1
    assert hits[0].reference == "memo-999"


def test_bulk_compress_ids_cli(tmp_path):
    memos_dir = tmp_path / "memos"
    memos_dir.mkdir()

    _write_memo(memos_dir / "memo-001-first.md", "memo-001", "First Memo")
    _write_memo(memos_dir / "memo-010-second.md", "memo-010", "Second Memo")

    result = CliRunner().invoke(main, ["bulk", "compress-ids", "--path", str(tmp_path), "--type", "memo"])

    assert result.exit_code == 0
    assert "Renumbered 1 document" in result.output
    assert (memos_dir / "memo-002-second.md").exists()
