"""Path containment helpers for docs-project.yaml configuration."""

from __future__ import annotations

from pathlib import Path


def is_within_path(path: Path, boundary: Path) -> bool:
    """Return true when path resolves inside boundary or is boundary itself."""
    resolved_path = path.resolve()
    resolved_boundary = boundary.resolve()
    try:
        resolved_path.relative_to(resolved_boundary)
        return True
    except ValueError:
        return False


def resolve_config_path(base_dir: Path, path_value: str, boundary: Path, allow_external_paths: bool) -> Path | None:
    """Resolve a config-relative path, enforcing containment unless explicitly allowed."""
    resolved = (base_dir / path_value).resolve()
    if allow_external_paths or is_within_path(resolved, boundary):
        return resolved
    return None
