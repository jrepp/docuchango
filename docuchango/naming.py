"""Naming standards for document file names.

This module provides built-in naming conventions and utilities for validating
document filenames against established patterns like kebab-case, snake_case, etc.

Usage:
    from docuchango.naming import BUILTIN_STANDARDS, validate_name

    pattern = BUILTIN_STANDARDS["kebab-case"]
    is_valid = validate_name("my-document.md", pattern)
"""

from __future__ import annotations

import re
from typing import Final

BUILTIN_NAMING_STANDARDS: Final[dict[str, str]] = {
    "nnn-name": r"^(\d{3})-(.+)\.md$",
    "year-month-day-name": r"^\d{4}-\d{2}-\d{2}-(.+)\.md$",
    "kebab-case": r"^[a-z0-9]+(-[a-z0-9]+)*\.md$",
    "snake_case": r"^[a-z0-9]+(_[a-z0-9]+)*\.md$",
    "camelCase": r"^[a-z][a-zA-Z0-9]*\.md$",
    "PascalCase": r"^[A-Z][a-zA-Z0-9]*\.md$",
    "lowercase": r"^[a-z0-9]+\.md$",
    "uppercase": r"^[A-Z0-9]+\.md$",
}

ALL_BUILTIN_NAMES: Final[list[str]] = sorted(BUILTIN_NAMING_STANDARDS.keys())


def validate_name(name: str, pattern: str) -> bool:
    """Validate a filename against a regex pattern.

    Args:
        name: The filename to validate (e.g., "my-document.md")
        pattern: Regex pattern (with or without ^ anchor)

    Returns:
        True if the filename matches the pattern, False otherwise
    """
    if not pattern.startswith("^"):
        pattern = f"^{pattern}"
    return bool(re.match(pattern, name))


def validate_name_with_standard(name: str, standard: str, custom_standards: dict[str, str] | None = None) -> bool:
    """Validate a filename against a named standard.

    Args:
        name: The filename to validate (e.g., "my-document.md")
        standard: Named standard (e.g., "kebab-case") or raw regex pattern
        custom_standards: Optional dict of custom standards defined by user

    Returns:
        True if the filename matches the standard, False otherwise

    Raises:
        ValueError: If the standard is not found
    """
    if standard in BUILTIN_NAMING_STANDARDS:
        pattern = BUILTIN_NAMING_STANDARDS[standard]
    elif custom_standards and standard in custom_standards:
        pattern = custom_standards[standard]
    elif standard.startswith("^"):
        pattern = standard
    else:
        raise ValueError(f"Unknown naming standard: {standard}. Available: {ALL_BUILTIN_NAMES}")
    return validate_name(name, pattern)


def resolve_standard(standard: str | None, custom_standards: dict[str, str] | None = None) -> str | None:
    """Resolve a naming standard name to a regex pattern.

    Args:
        standard: Named standard (e.g., 'kebab-case') or direct regex pattern
        custom_standards: Custom standards defined in docs-project.yaml

    Returns:
        Regex pattern string or None if not found/provided

    Raises:
        ValueError: If the standard name is not found and it's not a raw pattern
    """
    if not standard:
        return None
    if custom_standards and standard in custom_standards:
        return custom_standards[standard]
    if standard in BUILTIN_NAMING_STANDARDS:
        return BUILTIN_NAMING_STANDARDS[standard]
    if standard.startswith("^"):
        return standard
    return None


resolve_naming_standard = resolve_standard


def describe_standard(standard: str, custom_standards: dict[str, str] | None = None) -> str:
    """Get a human-readable description of a naming standard.

    Args:
        standard: Named standard or pattern
        custom_standards: Optional custom standards

    Returns:
        Human-readable description of the standard
    """
    descriptions: dict[str, str] = {
        "nnn-name": "NNN-name.md (e.g., 001-intro.md)",
        "year-month-day-name": "YYYY-MM-DD-name.md (e.g., 2025-05-25-intro.md)",
        "kebab-case": "kebab-case.md (e.g., my-document-name.md)",
        "snake_case": "snake_case.md (e.g., my_document_name.md)",
        "camelCase": "camelCase.md (e.g., myDocumentName.md)",
        "PascalCase": "PascalCase.md (e.g., MyDocumentName.md)",
        "lowercase": "lowercase.md (e.g., mydocumentname.md)",
        "uppercase": "UPPERCASE.md (e.g., MYDOCUMENTNAME.md)",
    }

    if standard in descriptions:
        return descriptions[standard]
    if custom_standards and standard in custom_standards:
        return f"{standard}: {custom_standards[standard]}"
    if standard.startswith("^"):
        return f"Custom pattern: {standard}"
    return f"Unknown standard: {standard}"
