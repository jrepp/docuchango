"""Markdown structure helpers shared by the validator and the fixers.

Two regions of a Markdown document are content rather than prose, and every
check and fix that walks lines has to agree on where they are: the leading YAML
frontmatter block, and fenced code blocks. :func:`frontmatter_span` and
:func:`fence_mask` are the single implementation of both, used by
:func:`mask_code` (which blanks code before the prose checks and before the
LNK-010 link rewrite) and by the blank-line helpers below.

Blank lines are the reason this module exists. ``FMT-002`` reports a run of
more than two blank lines and ``FMT-011`` collapses it back to two; see the
finding registry in ``docs-cms/rfcs/rfc-003-validator-roadmap.md``. A blank
line inside a code fence is content -- a deliberately empty line in a shell
transcript or a Python file -- and a blank line inside frontmatter may be part
of a YAML block scalar, so neither is reported and neither is collapsed. The
report and the fix share :func:`blank_line_runs` so they can never disagree
about which run is a finding: under the default atomic run, a fix the check
still reports would roll the whole run back.

``MDX-001`` and ``MDX-010`` are the same story one level up. :func:`mdx_tags`
is the single scan for a JSX-shaped ``<...>`` in prose that MDX cannot
compile: ``DocValidator.check_mdx_compatibility`` turns each hit into an
``MDX-001`` report, and :func:`escape_mdx_tags` -- which
``docuchango.fixes.mdx_syntax`` wraps for Phase 1 -- escapes exactly those
hits and nothing else. Sharing the scan is what makes the fix idempotent and
keeps the atomic run from withholding every fix in the tree over a
one-candidate disagreement.
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


def mask_code(content: str, strip_frontmatter: bool = False) -> list[str]:
    """Return the document's lines with code masked out, line numbers kept.

    Masks fenced code blocks (``` / ~~~) and inline code spans (backticks),
    including inline spans that wrap across multiple lines. Masked regions are
    replaced with spaces so column positions are preserved but the content is
    not matched by prose checks (MDX tags, links, ...); a line inside a fence
    is emptied outright, so a check that walks the masked lines finds nothing
    on it at all.

    Fenced blocks track the opening delimiter's character and length via
    :func:`fence_mask`: a block is only closed by a fence of the same character
    that is at least as long, so an outer ```` ```` block may contain an inner
    ``` example without prematurely closing.

    Every prose check and every fixer that walks links or tags masks with this
    one function, so none of them can disagree about where code begins: a link
    LNK-001 ignored because it sits in a code fence must be a link LNK-010
    leaves alone too.

    Args:
        content: The whole document, frontmatter included.
        strip_frontmatter: Also mask a leading YAML frontmatter block, since
            frontmatter is not compiled as MDX and its values must not be
            treated as prose.

    Returns:
        One string per input line, in order.
    """
    lines = content.split("\n")

    # Optionally mask a leading YAML frontmatter block.
    start = frontmatter_span(lines) if strip_frontmatter else 0
    out: list[str] = [""] * start

    # Fence tracking is shared with the blank-line helpers, so FMT-002 and
    # FMT-011 agree with the prose checks about where code begins and ends.
    for line, masked in zip(lines[start:], fence_mask(lines[start:]), strict=True):
        out.append("" if masked else line)

    # Now mask inline code spans across the (non-fenced) joined text so that
    # spans spanning multiple lines are handled. We rebuild line by line.
    joined = "\n".join(out)

    def _blank(match: re.Match[str]) -> str:
        # Preserve newlines so line numbering is unaffected.
        return "".join("\n" if ch == "\n" else " " for ch in match.group(0))

    # Backtick spans: two-backtick then single-backtick delimiters, matched
    # non-greedily, allowing newlines (multi-line inline spans).
    # A code span may wrap across lines but, per CommonMark, never across a
    # blank line. Bounding the span that way stops a single stray backtick in
    # prose from masking (and silencing the checks on) the rest of the
    # document.
    joined = re.sub(r"``(?:[^\n]|\n(?!\s*\n))+?``", _blank, joined)
    joined = re.sub(r"`(?:[^`\n]|\n(?!\s*\n))+?`", _blank, joined)

    return joined.split("\n")


# Known HTML elements that are valid raw markup in MDX and must not be
# flagged (e.g. '<a href=...>', '<br/>', '<sup>', '<div>').
KNOWN_HTML_TAGS = frozenset(
    {
        # Content / text
        "a",
        "abbr",
        "address",
        "article",
        "aside",
        "b",
        "bdi",
        "bdo",
        "blockquote",
        "br",
        "button",
        "canvas",
        "caption",
        "cite",
        "code",
        "col",
        "colgroup",
        "data",
        "datalist",
        "dd",
        "del",
        "details",
        "dfn",
        "dialog",
        "div",
        "dl",
        "dt",
        "em",
        "embed",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "head",
        "header",
        "hgroup",
        "hr",
        "i",
        "iframe",
        "img",
        "input",
        "ins",
        "kbd",
        "label",
        "legend",
        "li",
        "link",
        "main",
        "map",
        "mark",
        "menu",
        "meta",
        "meter",
        "nav",
        "noscript",
        "object",
        "ol",
        "optgroup",
        "option",
        "output",
        "p",
        "param",
        "picture",
        "pre",
        "progress",
        "q",
        "rp",
        "rt",
        "ruby",
        "s",
        "samp",
        "script",
        "section",
        "select",
        "slot",
        "small",
        "source",
        "span",
        "strong",
        "style",
        "sub",
        "summary",
        "sup",
        "table",
        "tbody",
        "td",
        "template",
        "textarea",
        "tfoot",
        "th",
        "thead",
        "time",
        "title",
        "tr",
        "track",
        "u",
        "ul",
        "var",
        "video",
        "wbr",
        # Media / SVG / MathML (commonly embedded raw)
        "audio",
        "svg",
        "path",
        "g",
        "circle",
        "rect",
        "line",
        "polyline",
        "polygon",
        "ellipse",
        "text",
        "defs",
        "use",
        "symbol",
        "math",
    }
)

# CommonMark autolinks: '<scheme:rest>' (absolute URI) and '<local@domain>'
# (email). Both are valid Markdown and must never be reported as JSX.
AUTOLINK_PATTERN = re.compile(
    r"<(?:[A-Za-z][A-Za-z0-9+.\-]{1,31}:[^<>\s]*"
    r"|[^\s<>@]+@[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?)+)>"
)


def is_safe_mdx_tag(tag_text: str) -> bool:
    """Return True if a '<...>' occurrence is safe/valid in MDX.

    Safe cases:
    - Known HTML elements (<a>, <br/>, <sup>, ...), open or close.
    - JSX components: PascalCase names or self-closing tags with a proper
      structure (e.g. <Outlet />, <SuspenseWrapper>).

    - CommonMark autolinks: '<https://example.com>' and '<user@host>'.
      Markdown resolves these before MDX sees a JSX tag, so they are valid.

    Risky (returns False): bare placeholders in prose that are not valid
    elements, e.g. <agentName>, <token>, <your-secret>, <log-name>.
    """
    # CommonMark autolinks are resolved by the Markdown parser and never
    # reach the JSX parser. An absolute-URI autolink is '<scheme:rest>' with
    # no whitespace; an email autolink is '<local@domain>'.
    if AUTOLINK_PATTERN.fullmatch(tag_text):
        return True

    # The name charset must match the candidate pattern, otherwise a
    # placeholder such as '<time-out>' or '<a-b>' would be truncated to a
    # known HTML prefix ('time', 'a') and wrongly treated as safe.
    m = re.match(r"</?([A-Za-z][A-Za-z0-9._-]*)", tag_text)
    if not m:
        return False
    name = m.group(1)

    # Known HTML element (case-insensitive) -> always safe.
    if name.lower() in KNOWN_HTML_TAGS:
        return True

    # JSX component convention: starts with an uppercase letter.
    if name[0].isupper():
        return True

    # Self-closing tag with valid structure, with or without attributes,
    # e.g. '<thing />' or '<widget role="img" />'. Any explicitly
    # self-closed tag is safe MDX regardless of the element name.
    return bool(re.match(r"<[A-Za-z][A-Za-z0-9._-]*(\s[^<>]*)?/>", tag_text))


# A '<' only starts a tag when a letter (or '/') follows IMMEDIATELY, with no
# whitespace. '< threshold' or 'a < b' are comparisons and are safe; only
# '<word...' is a tag candidate. The tag name may be a single character
# ('<x>') and may contain underscores ('<api_key>'), matching JSX
# identifier-shaped names. The candidate is bounded by the matching '>' so the
# whole tag is available when deciding safety, and so the escape can cover it.
TAG_CANDIDATE_PATTERN = re.compile(r"</?[A-Za-z][A-Za-z0-9._-]*[^<>]*/?>")

#: The name at the head of a tag candidate, used for the message wording.
_TAG_NAME_PATTERN = re.compile(r"</?([A-Za-z][A-Za-z0-9._-]*)")


@dataclass(frozen=True)
class MdxTag:
    """One JSX-shaped ``<...>`` in prose that MDX cannot compile (MDX-001)."""

    #: 1-based line number, counted over the whole document.
    line_number: int
    #: Half-open character span of the candidate within its (unmasked) line.
    start: int
    end: int
    #: The candidate exactly as written, from the ``<`` to the matching ``>``.
    text: str

    @property
    def name(self) -> str:
        """The element name MDX-001 names in its message, e.g. ``token``."""
        match = _TAG_NAME_PATTERN.match(self.text)
        return match.group(1) if match else self.text

    @property
    def escaped(self) -> str:
        """The candidate with its angle brackets escaped as HTML entities.

        ``TAG_CANDIDATE_PATTERN`` bounds the match with ``[^<>]*``, so the only
        ``<`` is the opening one and the only ``>`` is the closing one; nothing
        in between is rewritten. An ``&`` is left alone, which is what keeps
        the fix idempotent: an already-escaped ``&lt;token&gt;`` carries no
        ``<`` at all and is never a candidate again.
        """
        return self.text.replace("<", "&lt;").replace(">", "&gt;")


def mdx_tags(content: str) -> list[MdxTag]:
    """Every JSX-shaped candidate in prose that MDX-001 reports and MDX-010 escapes.

    Code fences, inline code spans and the frontmatter block are masked out by
    :func:`mask_code` first, so only prose is inspected. Known HTML elements,
    PascalCase JSX components, explicitly self-closing tags and CommonMark
    autolinks are dropped by :func:`is_safe_mdx_tag`.

    Args:
        content: The whole document, frontmatter included, read with LF line
            endings (see :mod:`docuchango.text_io`).

    Returns:
        The unsafe candidates in file order. The spans are offsets into the
        *unmasked* lines: :func:`mask_code` blanks a masked region character by
        character, so a line that can match at all has the same length masked
        and unmasked.
    """
    tags: list[MdxTag] = []
    for line_number, line in enumerate(mask_code(content, strip_frontmatter=True), start=1):
        for match in TAG_CANDIDATE_PATTERN.finditer(line):
            text = match.group(0)
            if is_safe_mdx_tag(text):
                continue
            tags.append(MdxTag(line_number=line_number, start=match.start(), end=match.end(), text=text))
    return tags


def escape_mdx_tags(content: str) -> tuple[str, list[MdxTag]]:
    """Escape the angle brackets of every MDX-001 candidate (MDX-010).

    Args:
        content: The whole document, frontmatter included.

    Returns:
        Tuple of (rewritten content, the tags that were escaped). The content
        is returned unchanged, and the list is empty, when there is nothing to
        escape, so the caller can use the list as the "did this change
        anything" flag.
    """
    tags = mdx_tags(content)
    if not tags:
        return content, []
    lines = content.split("\n")
    # Rewrite right to left so an earlier span's offsets stay valid after a
    # later one on the same line has grown by six characters.
    for tag in reversed(tags):
        line = lines[tag.line_number - 1]
        lines[tag.line_number - 1] = line[: tag.start] + tag.escaped + line[tag.end :]
    return "\n".join(lines), tags


def mdx_finding_message(tag: MdxTag) -> str:
    """The MDX-001 message the validator reports for one unsafe candidate."""
    return (
        f"MDX-001: Line {tag.line_number}: Unescaped '<{tag.name}>' looks like a JSX tag "
        f"but is not a valid HTML/JSX element. Wrap it in backticks (`<{tag.name}>`) "
        f"or escape the angle brackets as &lt;{tag.name}&gt;"
    )


def mdx_fix_message(tag: MdxTag) -> str:
    """The MDX-010 message a fixer reports after escaping one candidate."""
    return f"MDX-010: Line {tag.line_number}: Escaped '{tag.text}' in prose as '{tag.escaped}'"
