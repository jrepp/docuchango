#!/usr/bin/env python3
"""LNK-010: rewrite a broken internal link when exactly one document matches.

``LNK-001`` reports a link whose target does not exist. Most of those are a
document that moved, or a link written from the wrong folder: the file the
author meant is still in the tree, one directory over. When the scanned set
holds *exactly one* document with the target's filename, the intent is not in
doubt and this module rewrites the link to the correct relative path. When it
holds two or more, it is a judgement call and the link stays a report, with the
candidates listed by LNK-001 so the author can pick one. When it holds none,
there is nothing to rewrite at all.

The rule is filename identity and nothing cleverer. It replaces the
date-prefix pattern rewriting this module used to do
(``2025-10-13-rfc-001-x.md`` -> ``rfc-001-x.md``), which was written for one
migration, could not tell a link that was already correct from one that was
not, and rewrote links to files that did not exist either way.

Everything that decides whether a link is broken, and where it points, lives in
:mod:`docuchango.links` and is shared with ``DocValidator.validate_links``; the
code masking is :func:`docuchango.markdown.mask_code`, shared with the prose
checks. The fixer therefore rewrites exactly the links LNK-001 reports, and a
link it rewrites is guaranteed to resolve on the next pass -- which matters
under the default atomic run, where a fix the check still reports withholds
every fix in the tree. A link inside a code fence or an inline code span is
sample text and is never touched, and neither is a reference-style link or an
image, because LNK-001 does not check those either.

See the finding registry in ``docs-cms/rfcs/rfc-003-validator-roadmap.md``.

Usage:
    docuchango validate                 # LNK-010 runs in Phase 1
    python -m docuchango.fixes.internal_links --repo-root . --dry-run
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from docuchango.config_paths import is_within_path
from docuchango.links import (
    LINK_PATTERN,
    NON_PATH_PREFIXES,
    RESOLVED_LINK_TYPES,
    classify_link,
    document_index,
    link_anchor,
    link_candidates,
    relative_link,
    resolve_internal_link,
)
from docuchango.markdown import mask_code
from docuchango.text_io import read_text, write_text

#: Filename -> the scanned documents carrying it, as :func:`build_index`
#: returns it.
DocumentIndex = dict[str, list[Path]]


def build_index(documents: Iterable[Path], repo_root: Path) -> DocumentIndex:
    """Index the scanned document set for :func:`fix_internal_links`.

    Documents outside ``repo_root`` are dropped. A sub-project with
    ``security.allow_external_paths`` can put a scanned document outside the
    repository, and a link pointing there is an LNK-002 finding
    (``check_cross_plugin_links``): rewriting one broken link into another
    finding is not a repair, so such a document is never a candidate.

    Args:
        documents: Every document the run discovered.
        repo_root: The resolved repository root of the run.

    Returns:
        The index :func:`fix_internal_links` takes, built once per run.
    """
    root = repo_root.resolve()
    return document_index(path for path in documents if is_within_path(path, root))


def fix_internal_links(
    file_path: Path,
    index: Mapping[str, list[Path]],
    repo_root: Path,
    dry_run: bool = False,
) -> tuple[bool, list[str]]:
    """Rewrite the unambiguously broken links in one document (LNK-010).

    Args:
        file_path: The document to fix.
        index: The scanned set, from :func:`build_index`.
        repo_root: The resolved repository root, for site-root link targets.
        dry_run: Report the rewrites without writing them.

    Returns:
        Tuple of (whether anything changed, one message per rewritten link).
        The messages name the line and both targets, e.g.
        ``LNK-010: Line 12: Rewrote link 'adr-003.md' to '../adr/adr-003-title.md'``.
    """
    content = read_text(file_path)
    lines = content.split("\n")
    # Frontmatter, fenced blocks and inline spans are emptied or blanked while
    # line lengths and numbers are preserved, so a match found in a masked line
    # sits at the same offsets in the real one.
    masked = mask_code(content, strip_frontmatter=True)

    messages: list[str] = []
    changed = False

    for number, (line, masked_line) in enumerate(zip(lines, masked, strict=True), start=1):
        if not masked_line:
            continue
        rewrites: list[tuple[int, int, str]] = []
        for match in LINK_PATTERN.finditer(masked_line):
            target = match.group(2)
            replacement = _rewritten_target(file_path, target, index, repo_root)
            if replacement is None:
                continue
            rewrites.append((match.start(2), match.end(2), replacement))
            messages.append(f"LNK-010: Line {number}: Rewrote link '{target}' to '{replacement}'")
        if not rewrites:
            continue
        # Right to left, so an earlier rewrite does not shift a later offset.
        for start, end, replacement in reversed(rewrites):
            line = line[:start] + replacement + line[end:]
        lines[number - 1] = line
        changed = True

    if changed and not dry_run:
        write_text(file_path, "\n".join(lines))

    return changed, messages


def _rewritten_target(
    source_doc: Path,
    target: str,
    index: Mapping[str, list[Path]],
    repo_root: Path,
) -> str | None:
    """The path one broken link should be rewritten to, or ``None`` to leave it.

    ``None`` covers every case LNK-010 declines: a link that is not resolved
    against the filesystem at all (external, anchor, Docusaurus route, a URI
    scheme), a link that already resolves, a target carrying a link title, the
    angle-bracket form or percent-escapes, and a target that zero or two or
    more scanned documents match.
    """
    if target.startswith(NON_PATH_PREFIXES):
        return None
    if classify_link(target, source_doc) not in RESOLVED_LINK_TYPES:
        return None

    path_part, anchor = link_anchor(target)
    if not path_part:
        return None

    if resolve_internal_link(source_doc, repo_root, target)[1]:
        return None

    candidates = link_candidates(target, index)
    if len(candidates) != 1:
        return None

    return f"{relative_link(source_doc, candidates[0])}{anchor}"


def fix_links_in_tree(repo_root: Path, documents: Sequence[Path], dry_run: bool = False) -> list[tuple[Path, str]]:
    """Run LNK-010 over a whole discovered document set.

    Args:
        repo_root: The repository root the documents were discovered under.
        documents: The discovered documents, which are both the files to fix
            and the candidate set links are rewritten to.
        dry_run: Report the rewrites without writing them.

    Returns:
        One ``(document, message)`` pair per rewritten link, in document order.
    """
    root = repo_root.resolve()
    index = build_index(documents, root)
    results: list[tuple[Path, str]] = []
    for file_path in documents:
        _, messages = fix_internal_links(file_path, index, root, dry_run=dry_run)
        results.extend((file_path, message) for message in messages)
    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Run LNK-010 as a standalone script over a repository.

    The documents come from the same discovery ``docuchango validate`` uses,
    rooted at ``--repo-root``. The previous version resolved ``docs-cms``
    relative to the installed package, which pointed at site-packages for
    anything but a source checkout.
    """
    from docuchango.cli import _discover_doc_files

    parser = argparse.ArgumentParser(description="Rewrite broken internal links with a single matching document")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to discover documents under (default: current directory)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    documents = _discover_doc_files(repo_root)
    if not documents:
        print(f"No documents found under {repo_root}")
        return 0

    results = fix_links_in_tree(repo_root, documents, dry_run=args.dry_run)
    for file_path, message in results:
        print(f"{file_path}: {message}")

    verb = "would be rewritten" if args.dry_run else "rewritten"
    print(f"{len(results)} link(s) {verb} across {len(documents)} document(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
