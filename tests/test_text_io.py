"""Tests for the byte-level text IO helpers in ``docuchango.text_io``.

The point of this module is everything Python's universal newlines hide.
``Path.read_text`` translates ``\\r\\n`` and a bare ``\\r`` to ``\\n`` before any
caller sees the string, and ``Path.write_text`` translates ``\\n`` back to
``os.linesep`` on the way out, so both FMT-010 detection and the FMT-010 repair
have to work on the bytes. FMT-012 (the BOM) is the same problem from the other
end, and the two have to coexist on one file.
"""

from __future__ import annotations

import codecs
from pathlib import Path

import pytest

from docuchango.text_io import (
    CR,
    CRLF,
    carriage_return_lines,
    find_carriage_returns,
    has_bom,
    line_ending_finding_message,
    line_ending_fix_message,
    read_document,
    write_text,
)
from docuchango.validator import DocValidator

ADR = """---
id: adr-001
title: "ADR-001: Line Endings"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: test-project
doc_uuid: 8b063564-82a5-4a21-943f-e868388d36b9
---

# ADR-001: Line Endings

A single paragraph of ordinary prose with nothing else wrong with it.
"""


class TestFindCarriageReturns:
    """The pure byte-level scanner."""

    def test_lf_only_is_clean(self):
        assert find_carriage_returns(b"alpha\nbeta\ngamma\n") == []

    def test_empty_input_is_clean(self):
        assert find_carriage_returns(b"") == []

    def test_every_crlf_line_is_reported(self):
        assert find_carriage_returns(b"alpha\r\nbeta\r\ngamma\r\n") == [
            (1, CRLF),
            (2, CRLF),
            (3, CRLF),
        ]

    def test_mixed_reports_only_the_offending_lines(self):
        # 1: LF, 2: CRLF, 3: LF, 4: CRLF, 5: LF
        data = b"alpha\nbeta\r\ngamma\ndelta\r\nepsilon\n"
        assert find_carriage_returns(data) == [(2, CRLF), (4, CRLF)]

    def test_lone_cr_is_reported_as_cr(self):
        # A bare \r ends a line for Python's universal-newline reader too, so
        # the line numbering stays in step with the other formatting checks.
        assert find_carriage_returns(b"alpha\rbeta\ngamma\n") == [(1, CR)]

    def test_cr_at_end_of_file_is_reported(self):
        assert find_carriage_returns(b"alpha\n beta\r") == [(2, CR)]

    def test_cr_and_crlf_together(self):
        assert find_carriage_returns(b"alpha\r\nbeta\rgamma\n") == [(1, CRLF), (2, CR)]

    def test_line_numbers_match_a_universal_newline_read(self, tmp_path: Path):
        data = b"alpha\r\nbeta\rgamma\ndelta\r\n"
        path = tmp_path / "doc.md"
        path.write_bytes(data)
        lines = path.read_text(encoding="utf-8").split("\n")
        for line_number, _ in find_carriage_returns(data):
            # 1-based line numbers index into the decoded lines.
            assert lines[line_number - 1] in {"alpha", "beta", "gamma", "delta"}

    def test_bom_does_not_shift_line_numbers(self):
        assert find_carriage_returns(codecs.BOM_UTF8 + b"alpha\r\nbeta\r\n") == [
            (1, CRLF),
            (2, CRLF),
        ]


class TestCarriageReturnLines:
    """The path-taking wrapper the validator and the fixers call."""

    def test_reads_the_bytes_and_not_the_decoded_text(self, tmp_path: Path):
        path = tmp_path / "doc.md"
        path.write_bytes(b"alpha\r\nbeta\r\n")
        # The decoded text has no carriage return left in it at all...
        assert "\r" not in path.read_text(encoding="utf-8")
        # ...which is exactly why detection has to go through the bytes.
        assert carriage_return_lines(path) == [(1, CRLF), (2, CRLF)]

    def test_missing_file_is_not_a_finding(self, tmp_path: Path):
        assert carriage_return_lines(tmp_path / "nope.md") == []

    def test_crlf_and_bom_together(self, tmp_path: Path):
        path = tmp_path / "doc.md"
        path.write_bytes(codecs.BOM_UTF8 + ADR.replace("\n", "\r\n").encode("utf-8"))
        assert has_bom(path)
        assert [kind for _, kind in carriage_return_lines(path)] == [CRLF] * 14
        content, bom_removed = read_document(path)
        assert bom_removed
        assert content.startswith("---\nid: adr-001\n")


class TestMessages:
    def test_finding_message_matches_the_rfc_example(self):
        assert line_ending_finding_message(12, CRLF) == "FMT-010: Line 12: CRLF line ending"

    def test_finding_message_names_a_lone_cr(self):
        assert line_ending_finding_message(3, CR) == "FMT-010: Line 3: CR line ending"

    @pytest.mark.parametrize(
        ("findings", "expected"),
        [
            ([(1, CRLF)], "FMT-010: Converted CRLF line endings to LF"),
            ([(1, CR)], "FMT-010: Converted CR line endings to LF"),
            ([(1, CRLF), (2, CR)], "FMT-010: Converted CR and CRLF line endings to LF"),
        ],
    )
    def test_fix_message_names_what_was_found(self, findings, expected):
        assert line_ending_fix_message(findings) == expected


class TestWriteText:
    def test_writes_lf_verbatim(self, tmp_path: Path):
        path = tmp_path / "doc.md"
        write_text(path, "alpha\nbeta\n")
        assert path.read_bytes() == b"alpha\nbeta\n"

    def test_does_not_translate_newlines(self, tmp_path: Path):
        """``Path.write_text`` would emit ``os.linesep``; this must not."""
        path = tmp_path / "doc.md"
        write_text(path, "alpha\nbeta\n")
        assert b"\r" not in path.read_bytes()

    def test_round_trips_a_crlf_file_to_lf(self, tmp_path: Path):
        path = tmp_path / "doc.md"
        path.write_bytes(ADR.replace("\n", "\r\n").encode("utf-8"))
        write_text(path, read_document(path)[0])
        assert path.read_bytes() == ADR.encode("utf-8")
        assert carriage_return_lines(path) == []


class TestValidatorReportsOnlyFmt010:
    """A CRLF document is an FMT-010 finding and nothing else.

    The carriage returns must not be mistaken for trailing whitespace (FMT-001)
    on every single line, and the frontmatter behind them must parse normally
    rather than being reported as missing (FM-001).
    """

    def _errors(self, tmp_path: Path, data: bytes) -> list[str]:
        adr = tmp_path / "docs-cms" / "adr" / "adr-001-line-endings.md"
        adr.parent.mkdir(parents=True, exist_ok=True)
        adr.write_bytes(data)
        validator = DocValidator(repo_root=tmp_path, verbose=False)
        validator.scan_documents()
        validator.check_formatting()
        errors: list[str] = []
        for doc in validator.documents:
            errors.extend(doc.errors)
        return errors

    def test_crlf_document_reports_one_finding_per_line(self, tmp_path: Path):
        errors = self._errors(tmp_path, ADR.replace("\n", "\r\n").encode("utf-8"))

        assert errors == [line_ending_finding_message(n, CRLF) for n in range(1, 15)]
        assert not [e for e in errors if "Trailing whitespace" in e]
        assert not [e for e in errors if "frontmatter" in e.lower()]

    def test_lf_document_reports_nothing(self, tmp_path: Path):
        assert self._errors(tmp_path, ADR.encode("utf-8")) == []
