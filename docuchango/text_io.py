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
"""

from __future__ import annotations

import codecs
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
