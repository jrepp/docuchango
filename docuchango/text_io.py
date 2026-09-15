"""Shared text IO helpers for reading documents and configuration files.

Every document and config read goes through :func:`read_text` (or
:func:`read_document`, when the caller needs to know what it dropped) so that a
UTF-8 byte-order mark cannot hide the opening ``---`` from
``python-frontmatter``. Without this, a BOM makes a perfectly good document look
like it has no frontmatter at all: the fixers skip it and the validator reports
FM-001.

Writes stay plain UTF-8 everywhere, so the BOM disappears the first time a fixer
rewrites the file. The whitespace/fields and frontmatter fixers report that
removal as FMT-012; see the finding registry in
``docs-cms/rfcs/rfc-003-validator-roadmap.md``.

Line endings are the mirror image of the same problem. Text-mode reads use
universal newlines, so a ``\\r\\n`` document is indistinguishable from an
``\\n`` one by the time :func:`read_text` returns, and a text-mode write
translates ``\\n`` back to ``os.linesep``. :func:`carriage_return_lines` looks
at the bytes on disk the way :func:`has_bom` does, and :func:`write_text` pins
the newline translation off, which together are FMT-010.
"""

from __future__ import annotations

import codecs
from collections.abc import Iterable
from pathlib import Path

#: A UTF-8 BOM as it decodes when the file is read as plain ``utf-8``.
UTF8_BOM = "﻿"

#: Message the fixers report when they drop a BOM (registry row FMT-012).
FMT_012_FIX_MESSAGE = "FMT-012: Removed UTF-8 byte-order mark"

#: Message the validator reports for a file that still carries a BOM.
FMT_012_FINDING_MESSAGE = "FMT-012: UTF-8 byte-order mark at start of file"


def strip_bom(content: str) -> str:
    """Return ``content`` without a leading UTF-8 BOM."""
    return content[len(UTF8_BOM) :] if content.startswith(UTF8_BOM) else content


def read_document(file_path: Path) -> tuple[str, bool]:
    """Read a text file, returning its content and whether a BOM was dropped.

    Args:
        file_path: Path to the file to read.

    Returns:
        Tuple of (content without a leading BOM, whether a BOM was present).
    """
    content = file_path.read_text(encoding="utf-8")
    if content.startswith(UTF8_BOM):
        return content[len(UTF8_BOM) :], True
    return content, False


def read_text(file_path: Path) -> str:
    """Read a text file as UTF-8, dropping a leading BOM (like ``utf-8-sig``)."""
    return read_document(file_path)[0]


def has_bom(file_path: Path) -> bool:
    """Whether ``file_path`` starts with a UTF-8 byte-order mark."""
    try:
        with file_path.open("rb") as handle:
            return handle.read(len(codecs.BOM_UTF8)) == codecs.BOM_UTF8
    except OSError:
        return False


#: Kinds of non-LF line ending :func:`find_carriage_returns` reports.
CRLF = "CRLF"
CR = "CR"


def find_carriage_returns(data: bytes) -> list[tuple[int, str]]:
    """Locate every non-LF line ending in ``data`` (registry row FMT-010).

    Python reads text with universal newlines, so ``\\r\\n`` is translated to
    ``\\n`` before any check can see it: a CRLF document looks byte-for-byte
    like an LF one to :func:`read_text`. Detection therefore has to work on the
    bytes on disk, the same way :func:`has_bom` does.

    Args:
        data: Raw file bytes. A leading BOM is harmless; it carries no newline
            and so does not shift the line numbers.

    Returns:
        A list of ``(line_number, kind)`` pairs, in file order, where
        ``line_number`` is 1-based and ``kind`` is :data:`CRLF` for ``\\r\\n``
        or :data:`CR` for a lone carriage return. Lines are counted the way
        Python's universal-newline reader counts them -- ``\\n``, ``\\r\\n``
        and a bare ``\\r`` each end a line -- so the numbers line up with the
        ones the other formatting checks report.
    """
    findings: list[tuple[int, str]] = []
    line = 1
    index = 0
    length = len(data)
    while index < length:
        byte = data[index]
        if byte == 0x0D:  # \r
            if index + 1 < length and data[index + 1] == 0x0A:
                findings.append((line, CRLF))
                index += 2
            else:
                findings.append((line, CR))
                index += 1
            line += 1
        elif byte == 0x0A:  # \n
            index += 1
            line += 1
        else:
            index += 1
    return findings


def carriage_return_lines(file_path: Path) -> list[tuple[int, str]]:
    """The FMT-010 findings for ``file_path``, read from the bytes on disk."""
    try:
        return find_carriage_returns(file_path.read_bytes())
    except OSError:
        return []


def line_ending_finding_message(line_number: int, kind: str) -> str:
    """The FMT-010 message the validator reports for one offending line."""
    return f"FMT-010: Line {line_number}: {kind} line ending"


def line_ending_fix_message(findings: Iterable[tuple[int, str]]) -> str:
    """The FMT-010 message a fixer reports after normalizing line endings."""
    kinds = sorted({kind for _, kind in findings})
    return f"FMT-010: Converted {' and '.join(kinds)} line endings to LF"


def write_text(file_path: Path, content: str) -> None:
    """Write ``content`` as plain UTF-8 with LF line endings.

    ``Path.write_text`` opens the file with ``newline=None``, which translates
    every ``\\n`` to ``os.linesep`` -- on Windows that would put back the very
    carriage returns FMT-010 just removed. Pinning ``newline=""`` makes the
    bytes written exactly the bytes in ``content``.
    """
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
