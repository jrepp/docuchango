"""Requirement / acceptance-criterion traceability (TRC-001 .. TRC-005).

The PRD, FRD and RFC templates ask authors to give requirements and acceptance
criteria stable IDs (``FR-1``, ``NFR-1``, ``AC-1``) and to reference them from
the RFC. This module reads those IDs out of Markdown so ``docuchango validate``
can report a broken edge: a reference nobody defines, a definition made twice,
a coverage row with no disposition, a criterion no design claims, or a
requirement no criterion tests.

Only the shape of the references is checked. Whether a criterion is meaningful,
or a test passes, is for review and CI. The recognised syntax is documented in
``docs/ACCEPTANCE_CRITERIA.md``.

Parsing works on text already masked by :func:`docuchango.markdown.mask_code`,
so IDs inside code fences and inline code are never definitions or references.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Schemas whose documents may define IDs. RFCs, ADRs and memos only reference
#: them: an RFC coverage table that starts a row with ``FR-1`` is citing the
#: requirement, not restating it.
DEFINING_SCHEMAS = frozenset({"prd", "generic"})

_ID = r"(?:AC|FR|NFR)-\d+"
#: A bare ID. The lookbehind keeps ``NFR-1`` from also yielding ``FR-1`` and
#: ``UAC-1`` from yielding ``AC-1``; the lookahead keeps ``AC-1a`` out.
ID_RE = re.compile(rf"(?<![A-Za-z0-9_-])({_ID})(?![A-Za-z0-9_])")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_DEF_HEADING_RE = re.compile(rf"^(#{{2,6}})\s+\W*({_ID})(?![A-Za-z0-9_])")
_DEF_BULLET_RE = re.compile(rf"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?\*\*({_ID})\*\*")
_DEF_TABLE_RE = re.compile(r"^\s*\|\s*\**\s*((?:FR|NFR)-\d+)\s*\**\s*\|")
_REQUIREMENT_RE = re.compile(r"Requirements?\s*:\s*([^)]*)")
_TABLE_ROW_RE = re.compile(r"^\s*\|")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
_COVERAGE_HEADING_RE = re.compile(r"requirements?\s+coverage", re.IGNORECASE)
_DISPOSITIONS = ("covered", "deferred", "unresolved")


@dataclass
class Definition:
    """One place an ID is defined."""

    id: str
    line: int
    #: Requirement IDs named by a ``Requirement:`` clause in this definition's
    #: span. Only meaningful for ``AC-*`` definitions.
    requirements: list[str] = field(default_factory=list)


@dataclass
class Reference:
    """One mention of an ID that is not its own definition."""

    id: str
    line: int


@dataclass
class DocTrace:
    """Everything traceability reads from one document."""

    definitions: dict[str, list[Definition]] = field(default_factory=dict)
    references: list[Reference] = field(default_factory=list)
    #: (line, IDs on the row) for coverage-table rows with no disposition.
    rows_without_disposition: list[tuple[int, list[str]]] = field(default_factory=list)

    def defined_ids(self, prefix: str | None = None) -> list[str]:
        ids = self.definitions.keys()
        return [i for i in ids if prefix is None or i.startswith(prefix)]


def _heading_level(line: str) -> int | None:
    match = _HEADING_RE.match(line)
    return len(match.group(1)) if match else None


def _definition_at(line: str, can_define: bool) -> tuple[str, int | None] | None:
    """Return ``(id, heading level or None)`` when ``line`` defines an ID."""
    if not can_define:
        return None
    match = _DEF_HEADING_RE.match(line)
    if match:
        return match.group(2), len(match.group(1))
    match = _DEF_BULLET_RE.match(line)
    if match:
        return match.group(1), None
    match = _DEF_TABLE_RE.match(line)
    if match:
        return match.group(1), None
    return None


def _requirement_ids(text: str) -> list[str]:
    ids: list[str] = []
    for clause in _REQUIREMENT_RE.finditer(text):
        ids.extend(m.group(1) for m in ID_RE.finditer(clause.group(1)))
    return ids


def has_disposition(row: str) -> bool:
    """True when a coverage-table row has a covered/deferred/unresolved cell."""
    cells = [cell.strip().strip("*_` ").lower() for cell in row.strip().strip("|").split("|")]
    return any(cell.startswith(_DISPOSITIONS) for cell in cells)


def parse_traceability(lines: list[str], can_define: bool) -> DocTrace:
    """Read definitions, references and coverage rows from masked lines.

    ``lines`` is the document with frontmatter and code already masked, one
    string per line, so list index plus one is the real line number.
    """
    trace = DocTrace()

    # First pass: where is each ID defined, and how far does its span run?
    starts: list[tuple[int, str, int | None]] = []  # (index, id, heading level)
    for index, line in enumerate(lines):
        found = _definition_at(line, can_define)
        if found:
            starts.append((index, found[0], found[1]))

    definition_lines: dict[int, str] = {}
    for position, (index, def_id, level) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        for probe in range(index + 1, end):
            probe_level = _heading_level(lines[probe])
            if probe_level is not None and (level is None or probe_level <= level):
                end = probe
                break
            # A bullet's span is its own line plus indented continuation lines.
            if level is None and lines[probe].strip() and not lines[probe][0].isspace():
                end = probe
                break
        definition = Definition(id=def_id, line=index + 1)
        if def_id.startswith("AC-"):
            definition.requirements = _requirement_ids("\n".join(lines[index:end]))
        trace.definitions.setdefault(def_id, []).append(definition)
        definition_lines[index] = def_id

    # Second pass: every other mention of an ID is a reference. The mention
    # inside an AC's own ``Requirement:`` clause counts: it must resolve too.
    for index, line in enumerate(lines):
        own_id = definition_lines.get(index)
        skipped_own = False
        for match in ID_RE.finditer(line):
            ref_id = match.group(1)
            if own_id == ref_id and not skipped_own:
                skipped_own = True
                continue
            trace.references.append(Reference(id=ref_id, line=index + 1))

    # Third pass: coverage-table rows need a disposition.
    coverage_level: int | None = None
    for index, line in enumerate(lines):
        level = _heading_level(line)
        if level is not None:
            if coverage_level is not None and level <= coverage_level:
                coverage_level = None
            if _COVERAGE_HEADING_RE.search(line):
                coverage_level = level
            continue
        if coverage_level is None or not _TABLE_ROW_RE.match(line) or _TABLE_SEPARATOR_RE.match(line):
            continue
        ids = [m.group(1) for m in ID_RE.finditer(line)]
        if ids and not has_disposition(line):
            trace.rows_without_disposition.append((index + 1, ids))

    return trace
