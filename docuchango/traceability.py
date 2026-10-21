"""Requirement / acceptance-criterion traceability (TRC-001 .. TRC-005).

The PRD, FRD and RFC templates ask authors to give requirements and acceptance
criteria stable IDs (``FR-1``, ``NFR-1``, ``AC-1``, ``AC-1.1``) and to reference
them from the RFC. This module reads those IDs out of Markdown so
``docuchango validate`` can report a broken edge: a reference nobody defines, a
definition made twice, a coverage row with no disposition, a criterion no
design claims, or a requirement no criterion tests.

Only the shape of the references is checked. Whether a criterion is meaningful,
or a test passes, is for review and CI. The recognised syntax is documented in
``docs/ACCEPTANCE_CRITERIA.md``.

Definitions are recognised by form, in any document type, so an RFC with no
parent PRD can state its requirements locally as the template allows:

* a heading whose text starts with the ID (``### AC-1: Export a report``);
* a list item whose text starts with the ID in bold
  (``- [ ] **AC-1** (Requirement: FR-1): ...``, ``1. **FR-1**: ...``);
* a row of a table whose header's first column is ``ID`` or ``Requirement``
  and that has no ``Disposition`` or ``Source`` column (``| FR-1 | ... |``).

A table with a ``Disposition`` column is a coverage table: its rows cite IDs
and must say covered, deferred or unresolved. A defining row whose Scope, Status
or Priority cell explicitly marks deferral is a deferred requirement, which is
accounted for without a criterion or design.

Parsing works on text already masked by :func:`docuchango.markdown.mask_code`,
so IDs inside code fences and inline code are never definitions or references.
HTML comments are masked here for the same reason.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_ID = r"(?:AC|FR|NFR)-\d+(?:\.\d+)*"
#: A bare ID. The lookbehind keeps ``NFR-1`` from also yielding ``FR-1`` and
#: ``UAC-1`` from yielding ``AC-1``; the lookahead keeps ``AC-1a`` out. A dotted
#: ID (``AC-1.1``) is one ID, distinct from ``AC-1``; a trailing full stop is
#: punctuation (``see AC-1.``).
ID_RE = re.compile(rf"(?<![A-Za-z0-9_-])({_ID})(?![A-Za-z0-9_])")
_REFERENCE = rf"(?:[a-z][a-z0-9_-]*::)?{_ID}"
REFERENCE_RE = re.compile(rf"(?<![A-Za-z0-9_:-])({_REFERENCE})(?![A-Za-z0-9_])")
#: ``AC-1 through AC-3``. A bare hyphen is not a range operator: ``AC-1-AC-3``
#: cannot be told from hyphenated prose.
RANGE_RE = re.compile(rf"({_REFERENCE})\s*(?i:through|thru|to|\.\.+|–|—)\s*({_REFERENCE})")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_DEF_HEADING_RE = re.compile(rf"^(#{{1,6}})\s+\W*({_ID})(?![A-Za-z0-9_])")
_DEF_BULLET_RE = re.compile(rf"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?\*\*({_ID})\*\*")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
_DEFINING_HEADER_RE = re.compile(r"^(ids?|requirements?|criteri(?:a|on)|acceptance criteri(?:a|on))\b")
_CITING_HEADER_RE = re.compile(r"disposition|source|coverage")
_DISPOSITION_HEADER_RE = re.compile(r"disposition")
_DEFERRED_RE = re.compile(r"^(?:deferred|descoped|out of scope|not in scope)(?:$|\s*[:(—–-]|\s+to\b)", re.IGNORECASE)
#: ``Requirement: FR-1, FR-2`` up to the end of the clause. The clause ends at
#: a closing bracket, colon or semicolon so the Given/When/Then text that
#: follows on the same line is not read as more requirements.
_REQUIREMENT_RE = re.compile(r"Requirements?\s*:\s*((?:(?:::)|[^():;])*)")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_DISPOSITIONS = ("covered", "deferred", "unresolved")


@dataclass
class Definition:
    """One place an ID is defined."""

    id: str
    line: int
    #: FR/NFR IDs named by a ``Requirement:`` clause in this definition's span.
    #: Only meaningful for ``AC-*`` definitions.
    requirements: list[str] = field(default_factory=list)
    #: Explicit deferral in a defining table row's Scope, Status or Priority cell.
    #: It is accounted for without a criterion or design.
    deferred: bool = False


@dataclass
class Reference:
    """One mention of an ID that is not its own definition."""

    id: str
    line: int


@dataclass
class Range:
    """``lo through hi``: a claim over every defined ID between the endpoints."""

    prefix: str
    lo: int
    hi: int
    line: int
    source: str | None = None


@dataclass
class DocTrace:
    """Everything traceability reads from one document."""

    definitions: dict[str, list[Definition]] = field(default_factory=dict)
    references: list[Reference] = field(default_factory=list)
    ranges: list[Range] = field(default_factory=list)
    #: (line, IDs on the row) for coverage-table rows with no disposition.
    rows_without_disposition: list[tuple[int, list[str]]] = field(default_factory=list)

    def defined_ids(self, prefix: str | None = None) -> list[str]:
        return [i for i in self.definitions if prefix is None or i.startswith(prefix)]

    def is_deferred(self, def_id: str) -> bool:
        return any(d.deferred for d in self.definitions.get(def_id, []))


def split_id(def_id: str) -> tuple[str, int | None]:
    """``("AC", 3)`` for ``AC-3``; number is None for a dotted ID."""
    prefix, _, number = def_id.partition("-")
    return prefix, int(number) if number.isdigit() else None


def _cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def _plain(cell: str) -> str:
    return cell.strip().strip("*_`[] ").lower()


def has_disposition(cell: str) -> bool:
    """True when a coverage-table cell says covered, deferred or unresolved."""
    text = _plain(cell)
    return text.startswith(_DISPOSITIONS) and "/" not in text  # "[Covered / deferred / unresolved]" is the placeholder


def mask_html_comments(lines: list[str]) -> list[str]:
    """Blank HTML comments, line count preserved."""
    text = "\n".join(lines)
    masked = _HTML_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    return masked.split("\n")


def _requirement_ids(line: str) -> list[str]:
    ids: list[str] = []
    for clause in _REQUIREMENT_RE.finditer(line):
        ids.extend(
            m.group(1)
            for m in REFERENCE_RE.finditer(clause.group(1))
            if not m.group(1).split("::")[-1].startswith("AC-")
        )
    return ids


@dataclass
class _Table:
    header: list[str]
    defines: bool
    disposition_column: int | None
    deferral_columns: list[int]


def _table_at(lines: list[str], index: int) -> _Table | None:
    """The table whose header row is ``lines[index]``, if it is one."""
    if (
        index + 1 >= len(lines)
        or not _TABLE_ROW_RE.match(lines[index])
        or not _TABLE_SEPARATOR_RE.match(lines[index + 1])
    ):
        return None
    header = [_plain(cell) for cell in _cells(lines[index])]
    if not header:
        return None
    disposition = next((i for i, cell in enumerate(header) if _DISPOSITION_HEADER_RE.search(cell)), None)
    defines = bool(_DEFINING_HEADER_RE.match(header[0])) and not any(_CITING_HEADER_RE.search(c) for c in header)
    return _Table(
        header=header,
        defines=defines,
        disposition_column=disposition,
        deferral_columns=[i for i, cell in enumerate(header) if cell in {"scope", "status", "priority"}],
    )


def parse_traceability(lines: list[str]) -> DocTrace:
    """Read definitions, references, ranges and coverage rows from masked lines.

    ``lines`` is the document with frontmatter and code already masked, one
    string per line, so list index plus one is the real line number.
    """
    lines = mask_html_comments(lines)
    trace = DocTrace()

    # First pass: definitions and coverage rows, walking tables as units.
    # (index, id, heading level or None, deferred)
    starts: list[tuple[int, str, int | None, bool]] = []
    table: _Table | None = None
    for index, line in enumerate(lines):
        if table is not None:
            if not _TABLE_ROW_RE.match(line):
                table = None
            elif _TABLE_SEPARATOR_RE.match(line):
                continue
            else:
                cells = _cells(line)
                if table.defines and cells:
                    match = ID_RE.match(cells[0].strip("*_` "))
                    if match and match.group(1) == cells[0].strip("*_` "):
                        deferred = any(
                            _DEFERRED_RE.match(_plain(cells[i])) for i in table.deferral_columns if i < len(cells)
                        )
                        starts.append((index, match.group(1), None, deferred))
                if table.disposition_column is not None:
                    ids = [m.group(1) for m in ID_RE.finditer(line)]
                    cell = cells[table.disposition_column] if table.disposition_column < len(cells) else ""
                    if ids and not has_disposition(cell):
                        trace.rows_without_disposition.append((index + 1, ids))
                continue
        table = _table_at(lines, index)
        if table is not None:
            continue
        match = _DEF_HEADING_RE.match(line)
        if match:
            starts.append((index, match.group(2), len(match.group(1)), False))
            continue
        match = _DEF_BULLET_RE.match(line)
        if match:
            starts.append((index, match.group(1), None, False))

    # A definition's span runs to the next definition, a heading at or above
    # its own level, or (for a list item) the next unindented line.
    definition_lines: dict[int, str] = {}
    for position, (index, def_id, level, deferred) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        for probe in range(index + 1, end):
            probe_level = _heading_level(lines[probe])
            if probe_level is not None and (level is None or probe_level <= level):
                end = probe
                break
            if level is None and lines[probe].strip() and not lines[probe][0].isspace():
                end = probe
                break
        definition = Definition(id=def_id, line=index + 1, deferred=deferred)
        if def_id.startswith("AC-"):
            for span_line in lines[index:end]:
                definition.requirements.extend(_requirement_ids(span_line))
        trace.definitions.setdefault(def_id, []).append(definition)
        definition_lines[index] = def_id

    # Second pass: every other mention of an ID is a reference. The mention
    # inside an AC's own ``Requirement:`` clause counts: it must resolve too.
    for index, line in enumerate(lines):
        own_id = definition_lines.get(index)
        skipped_own = False
        for match in REFERENCE_RE.finditer(line):
            ref_id = match.group(1)
            if own_id == ref_id and not skipped_own:
                skipped_own = True
                continue
            trace.references.append(Reference(id=ref_id, line=index + 1))
        for match in RANGE_RE.finditer(line):
            lo_source, _, lo_id = match.group(1).rpartition("::")
            hi_source, _, hi_id = match.group(2).rpartition("::")
            (lo_prefix, lo), (hi_prefix, hi) = split_id(lo_id), split_id(hi_id)
            if lo_source == hi_source and lo_prefix == hi_prefix and lo is not None and hi is not None and lo <= hi:
                trace.ranges.append(Range(prefix=lo_prefix, lo=lo, hi=hi, line=index + 1, source=lo_source or None))

    return trace


def _heading_level(line: str) -> int | None:
    match = _HEADING_RE.match(line)
    return len(match.group(1)) if match else None
