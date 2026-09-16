#!/usr/bin/env python3
"""LNK-011: rewrite a link that leaves the repository to an absolute URL.

``LNK-002`` reports a relative link whose target resolves outside the
repository root: a Docusaurus plugin or sibling project checked out next to
this one, reached with a run of ``../``. Nothing inside the repository can
satisfy such a link, and the finding has always ended with "use an absolute
GitHub URL for external references". When ``project.repository_url`` is set in
the config that governs the linking document, this module writes that URL for
the author: the link becomes ``<repository_url>/<path from the repository root
to the target>``, anchor and query kept as written.

Two things keep the rewrite honest.

* The target must exist on disk. A link that escapes the repository *and*
  points at nothing is a typo, and turning a typo into a well-formed absolute
  URL would hide it behind a 404 that no checker in this repository can see
  again. Those stay LNK-002 reports.
* Which links escape at all is decided by
  :func:`docuchango.links.resolve_repository_escape`, shared with
  ``DocValidator.check_cross_plugin_links``, so the fixer can only ever rewrite
  a link the check reports. That matters under the default atomic run, where a
  fix the check still reports withholds every fix in the tree.

The code masking is :func:`docuchango.markdown.mask_code`, shared with the
check, so a link inside a code fence or an inline code span is sample text and
is invisible to both. Reference-style links and images are not rewritten,
matching LNK-010, and neither is a target carrying a CommonMark link title, the
angle-bracket destination form or percent-escapes, because re-encoding those is
guesswork.

What this module used to do was rewrite ``../rfcs/RFC-001-x.md`` to the
Docusaurus route ``/rfc/RFC-001-x`` for three hard-coded folder names. Those
links resolve perfectly well on disk and are not LNK-002 findings at all, the
routes were a single site's layout, and nothing checked that the route existed.

See the finding registry in ``docs-cms/rfcs/rfc-003-validator-roadmap.md``.

Usage:
    docuchango validate                 # LNK-011 runs in Phase 1
    python -m docuchango.fixes.cross_plugin_links --repo-root . --dry-run
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from docuchango.links import (
    LINK_PATTERN,
    link_anchor,
    repository_file_url,
    resolve_repository_escape,
)
from docuchango.markdown import mask_code
from docuchango.text_io import read_text, write_text


def fix_cross_plugin_links(
    file_path: Path,
    repo_root: Path,
    repository_url: str,
    dry_run: bool = False,
) -> tuple[bool, list[str]]:
    """Rewrite the escaping links in one document to repository URLs (LNK-011).

    Args:
        file_path: The document to fix.
        repo_root: The resolved repository root of the run, which is both the
            boundary a link has to cross to be a finding and the directory
            ``repository_url`` is the base for.
        repository_url: ``project.repository_url`` from the config that governs
            ``file_path``.
        dry_run: Report the rewrites without writing them.

    Returns:
        Tuple of (whether anything changed, one message per rewritten link).
        The messages name the line and both targets, e.g.
        ``LNK-011: Line 14: Rewrote link '../../shared/x.md' to
        'https://github.com/org/repo/blob/main/shared/x.md'``.
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
            replacement = _rewritten_target(file_path, target, repo_root, repository_url)
            if replacement is None:
                continue
            rewrites.append((match.start(2), match.end(2), replacement))
            messages.append(f"LNK-011: Line {number}: Rewrote link '{target}' to '{replacement}'")
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
    repo_root: Path,
    repository_url: str,
) -> str | None:
    """The absolute URL one escaping link becomes, or ``None`` to leave it.

    ``None`` covers every case LNK-011 declines: a target that is not a
    filesystem path (external, anchor, a URI scheme), one that stays inside the
    repository and so is not an LNK-002 finding, one carrying a link title, the
    angle-bracket form or percent-escapes, one that does not exist on disk, and
    one that the configured ``repository_url`` is not deep enough to address.
    """
    path_part, anchor = link_anchor(target)
    if not path_part:
        return None

    resolved = resolve_repository_escape(source_doc, repo_root, target)
    if resolved is None:
        return None
    # A link that escapes the repository and points at nothing is a typo, not a
    # cross-repository reference; rewriting it would freeze the typo into a
    # dead URL.
    if not resolved.exists():
        return None

    url = repository_file_url(repository_url, repo_root, resolved)
    if url is None:
        return None
    return f"{url}{anchor}"


def fix_cross_plugin_links_in_tree(
    repo_root: Path,
    documents: Sequence[Path],
    repository_urls: Mapping[Path, str | None],
    dry_run: bool = False,
) -> list[tuple[Path, str]]:
    """Run LNK-011 over a whole discovered document set.

    Args:
        repo_root: The repository root the documents were discovered under.
        documents: The discovered documents.
        repository_urls: Document -> the ``project.repository_url`` of the
            config that governs it, as ``cli._repository_urls_from_claims``
            builds it. A document with no URL is skipped, and its escaping
            links stay LNK-002 reports.
        dry_run: Report the rewrites without writing them.

    Returns:
        One ``(document, message)`` pair per rewritten link, in document order.
    """
    root = repo_root.resolve()
    results: list[tuple[Path, str]] = []
    for file_path in documents:
        repository_url = repository_urls.get(file_path)
        if not repository_url:
            continue
        _, messages = fix_cross_plugin_links(file_path, root, repository_url, dry_run=dry_run)
        results.extend((file_path, message) for message in messages)
    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Run LNK-011 as a standalone script over a repository.

    The documents and their governing ``repository_url`` come from the same
    discovery ``docuchango validate`` uses, rooted at ``--repo-root``.
    """
    from docuchango.cli import _discover_doc_claims, _repository_urls_from_claims

    parser = argparse.ArgumentParser(description="Rewrite links that leave the repository to absolute repository URLs")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to discover documents under (default: current directory)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    claims = _discover_doc_claims(repo_root)
    documents = sorted(claims)
    if not documents:
        print(f"No documents found under {repo_root}")
        return 0

    repository_urls = _repository_urls_from_claims(claims)
    if not any(repository_urls.values()):
        print("No project.repository_url configured; nothing to rewrite (LNK-002 stays a report)")
        return 0

    results = fix_cross_plugin_links_in_tree(repo_root, documents, repository_urls, dry_run=args.dry_run)
    for file_path, message in results:
        print(f"{file_path}: {message}")

    verb = "would be rewritten" if args.dry_run else "rewritten"
    print(f"{len(results)} link(s) {verb} across {len(documents)} document(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
