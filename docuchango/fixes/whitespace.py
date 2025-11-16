"""Auto-fixes for whitespace issues in frontmatter.

This module provides fixes for:
- Trailing/leading whitespace in string values
- Empty string vs null normalization
- Required field enhancement
"""

from __future__ import annotations

from pathlib import Path

import frontmatter


def trim_string_values(metadata: dict) -> tuple[dict, list[str]]:
    """Trim whitespace from all string values in metadata.

    Args:
        metadata: Frontmatter metadata dictionary

    Returns:
        Tuple of (updated_metadata, messages)
    """
    messages = []
    updated = {}

    for key, value in metadata.items():
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed != value:
                messages.append(f"Trimmed whitespace from '{key}' field")
                updated[key] = trimmed
            else:
                updated[key] = value
        elif isinstance(value, list):
            # Trim strings in arrays
            new_list = []
            list_changed = False
            for item in value:
                if isinstance(item, str):
                    trimmed = item.strip()
                    if trimmed != item:
                        list_changed = True
                    new_list.append(trimmed)
                else:
                    new_list.append(item)
            if list_changed:
                messages.append(f"Trimmed whitespace from items in '{key}' array")
            updated[key] = new_list
        else:
            updated[key] = value

    return updated, messages


def normalize_empty_values(metadata: dict) -> tuple[dict, list[str]]:
    """Normalize empty values (remove empty strings, keep empty arrays).

    Args:
        metadata: Frontmatter metadata dictionary

    Returns:
        Tuple of (updated_metadata, messages)
    """
    messages = []
    updated = {}

    # Fields that should be empty arrays, not missing
    array_fields = {"tags", "authors", "reviewers", "related"}

    for key, value in metadata.items():
        # Convert empty strings to missing (don't add to updated)
        if isinstance(value, str) and value.strip() == "":
            messages.append(f"Removed empty string value from '{key}'")
            continue

        # Convert None to missing for optional fields
        if value is None:
            messages.append(f"Removed null value from '{key}'")
            continue

        # Keep empty arrays for list fields
        if isinstance(value, list) and len(value) == 0:
            if key in array_fields:
                updated[key] = value
            else:
                messages.append(f"Removed empty array from '{key}'")
            continue

        updated[key] = value

    return updated, messages


def ensure_required_fields(metadata: dict, doc_type: str | None) -> tuple[dict, list[str]]:  # noqa: ARG001
    """Ensure required fields are present with defaults.

    Args:
        metadata: Frontmatter metadata dictionary
        doc_type: Document type (adr, rfc, memo, prd) - reserved for future use

    Returns:
        Tuple of (updated_metadata, messages)
    """
    import uuid

    messages = []
    updated = metadata.copy()

    # Common required fields
    if "tags" not in updated:
        updated["tags"] = []
        messages.append("Added missing 'tags' field (empty array)")

    if "doc_uuid" not in updated or not updated.get("doc_uuid"):
        updated["doc_uuid"] = str(uuid.uuid4())
        messages.append("Generated missing 'doc_uuid'")

    if "project_id" not in updated or not updated.get("project_id"):
        updated["project_id"] = "my-project"
        messages.append("Added default 'project_id'")

    return updated, messages


def fix_whitespace_and_fields(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Fix whitespace and missing required fields.

    Args:
        file_path: Path to the markdown file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (changed, messages)
    """
    messages = []

    try:
        content = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(content)
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    if not post.metadata:
        return False, ["No frontmatter found"]

    # Determine document type from path
    doc_type = None
    path_str = str(file_path).lower()
    if "/adr/" in path_str:
        doc_type = "adr"
    elif "/rfc" in path_str:
        doc_type = "rfc"
    elif "/memo" in path_str:
        doc_type = "memo"
    elif "/prd/" in path_str:
        doc_type = "prd"

    original = post.metadata.copy()

    # Apply fixes
    metadata = post.metadata

    # 1. Trim whitespace
    metadata, trim_msgs = trim_string_values(metadata)
    messages.extend(trim_msgs)

    # 2. Normalize empty values
    metadata, empty_msgs = normalize_empty_values(metadata)
    messages.extend(empty_msgs)

    # 3. Ensure required fields
    metadata, required_msgs = ensure_required_fields(metadata, doc_type)
    messages.extend(required_msgs)

    # Check if anything changed
    changed = metadata != original

    if changed:
        post.metadata = metadata

        if not dry_run:
            try:
                new_content = frontmatter.dumps(post)
                file_path.write_text(new_content, encoding="utf-8")
            except Exception as e:
                return False, [f"Error writing file: {e}"]

        return True, messages

    return False, []
