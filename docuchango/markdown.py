"""Markdown structure helpers shared by the validator and the fixers.

Two regions of a Markdown document are content rather than prose, and every
check and fix that walks lines has to agree on where they are: the leading YAML
frontmatter block, and fenced code blocks. :func:`frontmatter_span` and
:func:`fence_mask` are the single implementation of both, used by
``DocValidator._mask_code`` (which masks code before the prose checks) and by
the blank-line helpers below.

Blank lines are the reason this module exists. ``FMT-002`` reports a run of
more than two blank lines and ``FMT-011`` collapses it back to two; see the
finding registry in ``docs-cms/rfcs/rfc-003-validator-roadmap.md``. A blank
line inside a code fence is content -- a deliberately empty line in a shell
transcript or a Python file -- and a blank line inside frontmatter may be part
of a YAML block scalar, so neither is reported and neither is collapsed. The
report and the fix share :func:`blank_line_runs` so they can never disagree
about which run is a finding: under the default atomic run, a fix the check
still reports would roll the whole run back.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: The maximum number of consecutive blank lines FMT-002 accepts, and the
#: number FMT-011 collapses a longer run down to.
MAX_BLANK_LINES = 2

#: An opening or closing code fence: three or more backticks or tildes,
#: optionally indented, optionally followed by an info string.
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def frontmatter_span(lines: list[str]) -> int:
    """Number of leading lines taken up by a YAML frontmatter block.

    Args:
        lines: The document's lines, as produced by ``content.split("\\n")``.

    Returns:
        The index of the first line after the closing ``---``, or ``0`` when
        the document does not open with a frontmatter block. An unterminated
        block spans the whole document, which is what the parser sees too.
    """
    if not lines or lines[0].strip() != "---":
        return 0
    index = 1
    while index < len(lines) and lines[index].strip() != "---":
        index += 1
    if index < len(lines):  # the closing '---'
        index += 1
    return index


def fence_mask(lines: list[str]) -> list[bool]:
    """Mark every line that belongs to a fenced code block.

    A fence opens with three or more backticks or tildes and is only closed by
    a fence of the same character that is at least as long and carries no info
    string, so an outer ```` ```` block may contain an inner ``` example. A
    backtick fence whose info string contains a backtick is not a valid opening
    fence and stays prose.

    Args:
        lines: The lines to scan. Pass the lines *after* any frontmatter block
            (see :func:`frontmatter_span`); a ``---`` inside YAML is not a
            fence, but an indented ``~~~`` in a block scalar would be.

    Returns:
        One flag per input line: ``True`` for an opening fence, a closing
        fence and everything between them, ``False`` for prose.
    """
    mask = [False] * len(lines)
    fence_char: str | None = None
    fence_len = 0

    for index, line in enumerate(lines):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(2)
            rest = match.group(3)
            char = marker[0]
            length = len(marker)
            if fence_char is None:
                # Opening fence. Backtick fences may not carry a backtick in
                # the info string; if they do, this is not a fence at all.
                if char == "`" and "`" in rest:
                    continue
                fence_char = char
                fence_len = length
                mask[index] = True
                continue
            # A closing fence uses the same character, is at least as long,
            # and (per CommonMark) carries no info string.
            if char == fence_char and length >= fence_len and rest.strip() == "":
                fence_char = None
                fence_len = 0
            mask[index] = True
            continue
        if fence_char is not None:
            mask[index] = True

    return mask


@dataclass(frozen=True)
class BlankLineRun:
    """A run of consecutive blank lines outside frontmatter and code fences."""

    #: 1-based line number of the first blank line in the run.
    start_line: int
    #: How many blank lines the run contains.
    length: int

    @property
    def excess_lines(self) -> list[int]:
        """The 1-based line numbers past the second blank line of the run."""
        return list(range(self.start_line + MAX_BLANK_LINES, self.start_line + self.length))


def blank_line_runs(content: str) -> list[BlankLineRun]:
    """Every run of more than two blank lines that FMT-002 reports.

    Blank lines inside a code fence or inside the frontmatter block are
    content and are not counted; because a fence delimiter and the ``---``
    markers are themselves non-blank, they also break a run that would
    otherwise straddle them.

    Args:
        content: The whole document, frontmatter included, read with LF line
            endings (see :mod:`docuchango.text_io`).

    Returns:
        The runs of at least ``MAX_BLANK_LINES + 1`` blank lines, in file
        order.
    """
    return _scan_blank_lines(content)[1]


def collapse_blank_lines(content: str) -> tuple[str, list[BlankLineRun]]:
    """Collapse runs of more than two blank lines to two (FMT-011).

    Args:
        content: The whole document, frontmatter included.

    Returns:
        Tuple of (rewritten content, the runs that were collapsed). The
        content is returned unchanged, and the list is empty, when there is
        nothing to collapse, so the caller can use the list as the "did this
        change anything" flag. The line numbers in the runs are the ones the
        *input* had, matching what FMT-002 reported for the same file.
    """
    collapsed, runs = _scan_blank_lines(content)
    if not runs:
        return content, []
    return collapsed, runs


def blank_line_finding_message(line_number: int) -> str:
    """The FMT-002 message the validator reports for one excess blank line."""
    return f"FMT-002: Line {line_number}: More than {MAX_BLANK_LINES} consecutive blank lines"


def blank_line_fix_message(run: BlankLineRun) -> str:
    """The FMT-011 message a fixer reports after collapsing one run."""
    return f"FMT-011: Collapsed {run.length} blank lines to {MAX_BLANK_LINES} at line {run.start_line}"


def _scan_blank_lines(content: str) -> tuple[str, list[BlankLineRun]]:
    """Find the blank-line runs in ``content`` and build the collapsed text."""
    lines = content.split("\n")
    body_start = frontmatter_span(lines)
    mask = fence_mask(lines[body_start:])

    out: list[str] = lines[:body_start]
    runs: list[BlankLineRun] = []
    pending: list[str] = []
    index = body_start

    def flush(run_start: int) -> None:
        if len(pending) > MAX_BLANK_LINES:
            runs.append(BlankLineRun(start_line=run_start, length=len(pending)))
            out.extend(pending[:MAX_BLANK_LINES])
        else:
            out.extend(pending)
        pending.clear()

    run_start = index + 1
    while index < len(lines):
        if not lines[index].strip() and not mask[index - body_start]:
            if not pending:
                run_start = index + 1
            pending.append(lines[index])
        else:
            flush(run_start)
            out.append(lines[index])
        index += 1
    flush(run_start)

    return "\n".join(out), runs
