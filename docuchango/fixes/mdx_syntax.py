"""Escape JSX-incompatible angle brackets in prose (MDX-010).

``MDX-001`` reports a ``<`` that opens something MDX reads as a JSX tag but
that is not a valid HTML element, a PascalCase component, an explicitly
self-closing tag or a CommonMark autolink -- a bare prose placeholder such as
``<token>`` or ``<agentName>``. ``MDX-010`` is the repair: it rewrites those
angle brackets as ``&lt;`` and ``&gt;`` and changes nothing else. See the
finding registry in ``docs-cms/rfcs/rfc-003-validator-roadmap.md``.

The scan is not duplicated here. :func:`docuchango.markdown.mdx_tags` is the
single implementation that ``DocValidator.check_mdx_compatibility`` reports
from and that :func:`docuchango.markdown.escape_mdx_tags` rewrites, so the fix
repairs exactly what the check reports -- no more and no less. That matters
twice over: under the default atomic run, a fixer that disagreed with its check
by one candidate would withhold every fix in the tree, and escaping something
the check does not report would be an unrequested edit to a user's prose.

Content inside fenced code blocks, inside inline code spans and inside the
frontmatter block is masked before the scan and is never touched. Comparisons
(``<5ms``, ``a < b``) are not JSX tags and are left alone, as are already
escaped entities: ``&lt;token&gt;`` has no ``<`` left to match, which is what
makes a second run a no-op.
"""

from __future__ import annotations

from pathlib import Path

from docuchango.markdown import escape_mdx_tags, mdx_fix_message
from docuchango.text_io import read_text, write_text


def fix_mdx_issues(content: str) -> tuple[str, list[str]]:
    """Escape every MDX-001 candidate in ``content`` (MDX-010).

    Args:
        content: The whole document, frontmatter included, read with LF line
            endings (see :mod:`docuchango.text_io`).

    Returns:
        Tuple of (rewritten content, one ``MDX-010: ...`` message per escaped
        candidate). The content is returned unchanged, and the list is empty,
        when there is nothing to escape.
    """
    fixed, tags = escape_mdx_tags(content)
    return fixed, [mdx_fix_message(tag) for tag in tags]


def fix_mdx_syntax(file_path: Path) -> tuple[bool, list[str]]:
    """Escape MDX-001 candidates in one file, rewriting it in place.

    Args:
        file_path: The document to repair.

    Returns:
        Tuple of (whether the file was rewritten, the ``MDX-010`` messages).
        The file is left untouched when there is nothing to escape, so this
        never rewrites a document just to normalize it.
    """
    content = read_text(file_path)
    fixed, messages = fix_mdx_issues(content)
    if not messages:
        return False, []
    write_text(file_path, fixed)
    return True, messages
