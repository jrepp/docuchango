"""Markdown link classification and resolution shared by LNK-001 and LNK-010.

``DocValidator.validate_links`` reports a broken internal link (``LNK-001``)
and ``docuchango.fixes.internal_links`` rewrites one when the scanned set holds
exactly one document with that filename (``LNK-010``); see the finding registry
in ``docs-cms/rfcs/rfc-003-validator-roadmap.md``. The two have to agree
exactly about which targets are links at all, which of them are resolved
against the filesystem, and where a target resolves to -- a fixer that
disagreed with its check by one case would either rewrite a link the check was
happy with, or leave one it still reports, and under the default atomic run the
second of those withholds every fix in the tree.

So the resolution lives here once, and both sides call it: :func:`classify_link`
decides what kind of target this is, :func:`link_path_target` reduces a target
to the filesystem path inside it, :func:`resolve_internal_link` turns that into
a path on disk plus whether it exists, and :func:`link_candidates` is the
"exactly one document has this filename" rule LNK-010 is built on.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from enum import Enum
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

#: A link target that starts with a URI scheme ("mailto:", "tel:", "ftp://",
#: ...) is never a filesystem path and must not be resolved as one.
URI_SCHEME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*:")

#: An inline Markdown link, ``[label](target)``, matched one line at a time.
#: Deliberately no reference-style (``[label][ref]``) or image support: LNK-001
#: does not check those, and LNK-010 must not rewrite what LNK-001 never
#: reported.
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

#: Link targets that are never a filesystem path.
NON_PATH_PREFIXES = ("mailto:", "data:")


class LinkType(Enum):
    """Types of links in markdown documents"""

    INTERNAL_DOC = "internal_doc"  # ./relative.md or /docs/path.md
    INTERNAL_ADR = "internal_adr"  # ADR cross-references
    INTERNAL_RFC = "internal_rfc"  # RFC cross-references
    DOCUSAURUS_PLUGIN = "docusaurus_plugin"  # Cross-plugin links (e.g., /prism-data-layer/netflix/...)
    EXTERNAL = "external"  # http(s)://
    ANCHOR = "anchor"  # #section
    UNKNOWN = "unknown"


#: The link types ``validate_links`` resolves against the filesystem, and so
#: the only ones LNK-010 may rewrite.
RESOLVED_LINK_TYPES = frozenset({LinkType.INTERNAL_DOC, LinkType.INTERNAL_ADR, LinkType.INTERNAL_RFC})


def classify_link(target: str, source_path: Path) -> LinkType:
    """Classify a link target by what it points at."""
    if target.startswith(("http://", "https://")):
        return LinkType.EXTERNAL
    if target.startswith("#"):
        return LinkType.ANCHOR
    if target.startswith("/prism-data-layer/"):
        # Docusaurus cross-plugin links (e.g., /prism-data-layer/netflix/scale)
        return LinkType.DOCUSAURUS_PLUGIN
    if target.startswith(("/adr/", "/rfc/", "/memos/", "/docs/", "/netflix/")):
        # Docusaurus plugin routes (e.g., /adr/ADR-046, /rfc/RFC-001, /memos/MEMO-003)
        return LinkType.DOCUSAURUS_PLUGIN
    if "adr/" in target or (target.startswith("./") and "docs/adr" in str(source_path)):
        return LinkType.INTERNAL_ADR
    if "rfc" in target.lower() or (target.startswith("./") and "docs/rfcs" in str(source_path)):
        return LinkType.INTERNAL_RFC
    if target.endswith(".md") or target.startswith(("./", "../")):
        return LinkType.INTERNAL_DOC
    # Any remaining target that is not root-relative and carries no URI scheme
    # is a bare relative reference (e.g. 'other-doc', 'guide/'). Treat it as an
    # internal doc link so it is resolved against the source directory instead
    # of being reported as an unknown link type. Targets with a scheme
    # ('mailto:', 'tel:', 'ftp://', ...) stay UNKNOWN so they are reported as
    # such rather than as a nonsensical missing file.
    if not target.startswith("/") and not URI_SCHEME_PATTERN.match(target):
        return LinkType.INTERNAL_DOC
    return LinkType.UNKNOWN


def link_path_target(target: str) -> str:
    """Return the filesystem path portion of a Markdown link target.

    Strips the optional CommonMark link title ('path "Title"'), the
    angle-bracket destination form ('<path>'), and any query/anchor suffix,
    then percent-decodes what is left.
    """
    target = target.strip()
    # Optional link title: a destination followed by whitespace and a quoted
    # or parenthesized title.
    title_match = re.match(r"^(.*?)\s+(?:\"[^\"]*\"|'[^']*'|\([^()]*\))\s*$", target, flags=re.DOTALL)
    if title_match:
        target = title_match.group(1).strip()
    # Angle-bracket destination form: <path with spaces>
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return unquote(re.split(r"[?#]", target, maxsplit=1)[0])


def resolve_link_target(base_dir: Path, target: str) -> tuple[Path, bool]:
    """Resolve a link target against base_dir and report existence.

    Handles three cases without producing false negatives:
    - An existing file (with or without suffix).
    - An existing directory (e.g. a link to '../adr/'), which markdown and
      Docusaurus treat as a valid folder link and must NOT get '.md' appended.
    - A suffix-less document reference (e.g. './other-doc'), for which we try
      the '.md' extension.
    """
    resolved = (base_dir / target).resolve()

    # Directory or exact file already exists -> valid as-is.
    if resolved.exists():
        return resolved, True

    # Suffix-less reference to a markdown doc: try appending '.md'.
    if not resolved.suffix:
        with_md = Path(str(resolved) + ".md")
        if with_md.exists():
            return with_md, True
        return with_md, False

    return resolved, False


def resolve_internal_link(source_doc: Path, repo_root: Path, target: str) -> tuple[Path, bool]:
    """Resolve one internal link the way LNK-001 does.

    A site-root target ('/docs/x.md') resolves against ``repo_root``; every
    other form -- './x', '../x' and the bare relative 'adr/x.md' -- resolves
    against the linking document's own folder, which is what Markdown and
    Docusaurus do.

    Args:
        source_doc: Path of the document that contains the link.
        repo_root: Repository root, for site-root targets.
        target: The raw link destination, title and anchor included.

    Returns:
        Tuple of (resolved path, whether it exists).
    """
    path_target = link_path_target(target)
    if path_target.startswith("/"):
        return resolve_link_target(repo_root, path_target.lstrip("/"))
    return resolve_link_target(source_doc.parent, path_target)


def document_index(documents: Iterable[Path]) -> dict[str, list[Path]]:
    """Group the scanned document set by filename, for :func:`link_candidates`.

    Args:
        documents: Every document the run scanned.

    Returns:
        Filename -> the documents carrying it, sorted so the candidate list a
        finding prints is stable between runs.
    """
    index: dict[str, list[Path]] = {}
    for path in documents:
        index.setdefault(path.name, []).append(path)
    for paths in index.values():
        paths.sort()
    return index


def link_candidates(target: str, index: Mapping[str, list[Path]]) -> list[Path]:
    """Scanned documents that could be what a broken link meant (LNK-010).

    The rule is filename identity and nothing cleverer: a link to
    ``adr-003-decision.md`` from the wrong folder means the document of that
    name, wherever it now lives. A suffix-less target ('./adr-003-decision')
    is matched against ``<name>.md`` too, mirroring the '.md' that
    :func:`resolve_link_target` appends.

    Args:
        target: The raw link destination.
        index: The scanned set, as built by :func:`document_index`.

    Returns:
        The matching documents, sorted. Empty when nothing matches, and of
        length two or more when the link is ambiguous -- LNK-010 rewrites only
        the exactly-one case and LNK-001 reports the rest.
    """
    name = PurePosixPath(link_path_target(target).rstrip("/")).name
    if not name or name in (".", ".."):
        return []
    candidates = list(index.get(name, ()))
    if not PurePosixPath(name).suffix:
        candidates.extend(index.get(f"{name}.md", ()))
    return sorted(set(candidates))


def relative_link(source_doc: Path, candidate: Path) -> str:
    """The relative POSIX link from ``source_doc`` to ``candidate``.

    Same-folder and descendant targets are written with an explicit './' so
    the result is unambiguously a relative path rather than something a reader
    could mistake for a Docusaurus route.
    """
    relative = PurePosixPath(os.path.relpath(candidate, start=source_doc.parent).replace(os.sep, "/"))
    text = str(relative)
    return text if text.startswith("../") else f"./{text}"


def link_anchor(target: str) -> tuple[str, str]:
    """Split a plain link target into its path and its '#anchor'/'?query' tail.

    Returns ``("", "")`` for a target this module will not rewrite: one that
    carries a CommonMark link title, the angle-bracket destination form or
    percent-escapes, because re-encoding those is guesswork LNK-010 has no
    business doing. The caller treats an empty path as "leave this link
    alone".
    """
    match = re.match(r"^([^?#]*)([?#].*)?$", target, flags=re.DOTALL)
    if match is None:  # pragma: no cover - the pattern matches any string
        return "", ""
    path_part = match.group(1)
    if not path_part or path_part != link_path_target(target):
        return "", ""
    return path_part, match.group(2) or ""
