"""Compress document IDs and update references across a repository."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from docuchango.fixes.yaml_utils import dumps as frontmatter_dumps

DOC_ID_RE = re.compile(r"\b(adr|rfc|memo|prd)-(\d{3})\b", re.IGNORECASE)
FILENAME_ID_RE = re.compile(r"^(adr|rfc|memo|prd)-(\d{3})(-.+)?\.md$", re.IGNORECASE)

TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mdx",
    ".py",
    ".rst",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "node_modules",
    "venv",
}


@dataclass(frozen=True)
class DocumentIdChange:
    """A planned document ID and filename change."""

    file_path: Path
    new_path: Path
    old_id: str
    new_id: str


@dataclass(frozen=True)
class ReferenceHit:
    """A reference found during stale-reference audit."""

    file_path: Path
    line_number: int
    reference: str


@dataclass
class CompressionResult:
    """Result of a document ID compression run."""

    changes: list[DocumentIdChange] = field(default_factory=list)
    updated_files: dict[Path, int] = field(default_factory=dict)
    synced_files: list[Path] = field(default_factory=list)
    stale_references: list[ReferenceHit] = field(default_factory=list)
    missing_references: list[ReferenceHit] = field(default_factory=list)


def compress_document_ids(
    repo_root: Path,
    doc_files: list[Path],
    doc_type: str | None = None,
    dry_run: bool = False,
) -> CompressionResult:
    """Compress document IDs and rewrite references across the repository.

    Documents are compressed independently per type. For example, memo IDs
    001, 010, and 011 become 001, 002, and 003 while preserving each filename's
    descriptive suffix.
    """
    repo_root = repo_root.resolve()
    changes = _plan_id_changes(doc_files, doc_type)
    result = CompressionResult(changes=changes)

    updated_files = _rewrite_references(repo_root, changes, dry_run=dry_run)
    result.updated_files = updated_files

    if not dry_run:
        _apply_document_changes(changes)

    result.synced_files = _sync_frontmatter_ids(doc_files, changes, dry_run=dry_run)
    result.stale_references = _audit_old_references(
        repo_root, changes, planned_updates=updated_files if dry_run else None
    )
    result.missing_references = audit_missing_document_references(repo_root, doc_files, planned_changes=changes)
    return result


def audit_missing_document_references(
    repo_root: Path,
    doc_files: list[Path],
    planned_changes: list[DocumentIdChange] | None = None,
) -> list[ReferenceHit]:
    """Find document-like references that do not resolve to a current document ID."""
    current_ids = {_document_id_for_file(path) for path in doc_files}
    current_ids.discard(None)

    for change in planned_changes or []:
        current_ids.discard(change.old_id)
        current_ids.add(change.new_id)

    id_map = {change.old_id: change.new_id for change in planned_changes or []}
    missing: list[ReferenceHit] = []
    for file_path in _iter_text_files(repo_root):
        content = _read_text(file_path)
        if content is None:
            continue
        if id_map:
            content = _replace_ids(content, id_map)
        for line_number, line in enumerate(content.splitlines(), start=1):
            for match in DOC_ID_RE.finditer(line):
                reference = match.group(0).lower()
                if reference.endswith("-000"):
                    continue
                if reference not in current_ids:
                    missing.append(ReferenceHit(file_path=file_path, line_number=line_number, reference=match.group(0)))
    return missing


def _plan_id_changes(doc_files: list[Path], doc_type: str | None) -> list[DocumentIdChange]:
    docs_by_type: dict[str, list[tuple[int, Path, str]]] = {}
    for file_path in doc_files:
        old_id = _document_id_for_file(file_path)
        if not old_id:
            continue
        prefix, number_text = old_id.split("-", 1)
        if doc_type and prefix != doc_type:
            continue
        docs_by_type.setdefault(prefix, []).append((int(number_text), file_path, old_id))

    changes: list[DocumentIdChange] = []
    for prefix, docs in sorted(docs_by_type.items()):
        for new_number, (_old_number, file_path, old_id) in enumerate(sorted(docs), start=1):
            new_id = f"{prefix}-{new_number:03d}"
            if new_id == old_id:
                continue

            match = FILENAME_ID_RE.match(file_path.name)
            suffix = match.group(3) if match else f"-{file_path.stem}"
            new_path = file_path.with_name(f"{new_id}{suffix}.md")
            changes.append(DocumentIdChange(file_path=file_path, new_path=new_path, old_id=old_id, new_id=new_id))
    return changes


def _apply_document_changes(changes: list[DocumentIdChange]) -> None:
    for change in changes:
        _set_frontmatter_id(change.file_path, change.new_id)
        if change.file_path == change.new_path:
            continue
        if change.new_path.exists():
            raise FileExistsError(f"Cannot rename {change.file_path} to {change.new_path}: destination exists")
        change.file_path.rename(change.new_path)


def _sync_frontmatter_ids(doc_files: list[Path], changes: list[DocumentIdChange], dry_run: bool) -> list[Path]:
    current_paths = {change.new_path if change.new_path.exists() else change.file_path for change in changes}
    changed_paths = {change.file_path for change in changes}
    current_paths.update(path for path in doc_files if path not in changed_paths)

    synced: list[Path] = []
    for file_path in current_paths:
        filename_id = _filename_id(file_path)
        if not filename_id or not file_path.exists():
            continue

        try:
            post = frontmatter.load(file_path)
        except Exception:  # noqa: S112 - malformed docs are ignored by this repair pass
            continue
        if post.metadata.get("id") == filename_id:
            continue

        synced.append(file_path)
        if not dry_run:
            _set_frontmatter_id(file_path, filename_id)
    return sorted(synced)


def _rewrite_references(repo_root: Path, changes: list[DocumentIdChange], dry_run: bool) -> dict[Path, int]:
    if not changes:
        return {}

    id_map = {change.old_id: change.new_id for change in changes}
    filename_map = {
        change.file_path.name: change.new_path.name
        for change in changes
        if change.file_path.name != change.new_path.name
    }
    updated_files: dict[Path, int] = {}

    for file_path in _iter_text_files(repo_root):
        content = _read_text(file_path)
        if content is None:
            continue

        new_content = content
        for old_name, new_name in filename_map.items():
            new_content = new_content.replace(old_name, new_name)
        new_content = _replace_ids(new_content, id_map)

        if new_content != content:
            updated_files[file_path] = _count_reference_updates(content, id_map, filename_map)
            if not dry_run:
                file_path.write_text(new_content, encoding="utf-8")

    return updated_files


def _replace_ids(content: str, id_map: dict[str, str]) -> str:
    lowered_map = {old.lower(): new.lower() for old, new in id_map.items()}

    def replace_match(match: re.Match[str]) -> str:
        old = match.group(0)
        new = lowered_map.get(old.lower())
        if not new:
            return old
        prefix, number = new.split("-", 1)
        old_prefix = old.split("-", 1)[0]
        if old_prefix.isupper():
            prefix = prefix.upper()
        elif old_prefix[:1].isupper():
            prefix = prefix.capitalize()
        return f"{prefix}-{number}"

    return DOC_ID_RE.sub(replace_match, content)


def _count_reference_updates(content: str, id_map: dict[str, str], filename_map: dict[str, str]) -> int:
    count = 0
    old_ids = set(id_map)
    for match in DOC_ID_RE.finditer(content):
        if match.group(0).lower() in old_ids:
            count += 1
    for old_name in filename_map:
        count += content.count(old_name)
    return max(1, count)


def _audit_old_references(
    repo_root: Path,
    changes: list[DocumentIdChange],
    planned_updates: dict[Path, int] | None = None,
) -> list[ReferenceHit]:
    old_ids = {change.old_id for change in changes} - {change.new_id for change in changes}
    if not old_ids:
        return []

    stale: list[ReferenceHit] = []
    for file_path in _iter_text_files(repo_root):
        content = _read_text(file_path)
        if content is None:
            continue
        if planned_updates and file_path in planned_updates:
            content = _replace_ids(content, {change.old_id: change.new_id for change in changes})
        for line_number, line in enumerate(content.splitlines(), start=1):
            for match in DOC_ID_RE.finditer(line):
                if match.group(0).lower() in old_ids:
                    stale.append(ReferenceHit(file_path=file_path, line_number=line_number, reference=match.group(0)))
    return stale


def _document_id_for_file(file_path: Path) -> str | None:
    filename_id = _filename_id(file_path)
    if filename_id:
        return filename_id

    try:
        post = frontmatter.load(file_path)
    except Exception:
        post = None
    if post and isinstance(post.metadata.get("id"), str):
        metadata_id = post.metadata["id"].lower()
        if DOC_ID_RE.fullmatch(metadata_id):
            return metadata_id

    return None


def _filename_id(file_path: Path) -> str | None:
    match = FILENAME_ID_RE.match(file_path.name)
    if not match:
        return None
    return f"{match.group(1).lower()}-{match.group(2)}"


def _set_frontmatter_id(file_path: Path, doc_id: str) -> None:
    content = file_path.read_text(encoding="utf-8")
    post = frontmatter.loads(content)
    post.metadata["id"] = doc_id
    file_path.write_text(frontmatter_dumps(post), encoding="utf-8")


def _iter_text_files(repo_root: Path):  # type: ignore[no-untyped-def]
    for path in repo_root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield path


def _read_text(file_path: Path) -> str | None:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
