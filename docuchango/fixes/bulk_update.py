"""Bulk update frontmatter fields across documentation.

This module provides flexible operations for updating YAML frontmatter fields:
- set: Set field value (updates if exists, creates if doesn't)
- add: Add field only if it doesn't exist
- remove: Remove field from frontmatter
- rename: Rename field (old_name -> new_name)
"""

from __future__ import annotations

from pathlib import Path

import frontmatter
import yaml

# Valid bulk update operations
VALID_OPERATIONS = {"set", "add", "remove", "rename"}


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped.

    Args:
        file_path: Path to the file

    Returns:
        True if file should be skipped
    """
    # Skip templates
    if "template" in file_path.name.lower() or file_path.name.startswith("000-"):
        return True

    # Skip index files
    return file_path.name == "index.md"


def serialize_frontmatter(metadata: dict) -> str:
    """Serialize frontmatter dict back to YAML with proper formatting.

    Args:
        metadata: Frontmatter metadata dictionary

    Returns:
        Formatted YAML string
    """
    yaml_str = yaml.dump(
        metadata,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=1000,  # Prevent line wrapping
    )
    return yaml_str.strip()


def update_frontmatter_bulk(
    content: str, field_name: str, new_value: str | None, operation: str
) -> tuple[str, bool, str]:
    """Update a specific field in YAML frontmatter.

    Args:
        content: Full markdown content
        field_name: Field to update
        new_value: New value for the field (or new name for rename)
        operation: Operation type (set, add, remove, rename)

    Returns:
        Tuple of (updated_content, was_modified, message)

    Raises:
        ValueError: If operation is not one of: set, add, remove, rename
    """
    # Validate operation
    if operation not in VALID_OPERATIONS:
        raise ValueError(f"Invalid operation '{operation}'. Must be one of: {', '.join(VALID_OPERATIONS)}")

    try:
        post = frontmatter.loads(content)
    except Exception as e:
        return content, False, f"Error parsing frontmatter: {e}"

    # Empty frontmatter is OK for operations that add fields (set, add)
    # For other operations (remove, rename), we need existing metadata
    if not post.metadata and operation not in ("set", "add"):
        return content, False, "No frontmatter found"

    # Initialize empty metadata if needed
    if not post.metadata:
        post.metadata = {}

    modified = False
    message = ""

    if operation == "set":
        # Set field value (update if exists, add if doesn't)
        old_value = post.metadata.get(field_name)
        if str(old_value) != new_value:
            post.metadata[field_name] = new_value
            modified = True
            if old_value is None:
                message = f"Added {field_name}={new_value}"
            else:
                message = f"Updated {field_name}: {old_value} → {new_value}"
        else:
            message = f"Field {field_name} already has value '{new_value}'"

    elif operation == "add":
        # Add field only if it doesn't exist
        if field_name not in post.metadata:
            post.metadata[field_name] = new_value
            modified = True
            message = f"Added {field_name}={new_value}"
        else:
            message = f"Field {field_name} already exists"

    elif operation == "remove":
        # Remove field if it exists
        if field_name in post.metadata:
            del post.metadata[field_name]
            modified = True
            message = f"Removed {field_name}"
        else:
            message = f"Field {field_name} not found"

    elif operation == "rename":
        # Rename field (field_name is old_name, new_value is new_name)
        if field_name in post.metadata:
            post.metadata[new_value] = post.metadata.pop(field_name)
            modified = True
            message = f"Renamed {field_name} → {new_value}"
        else:
            message = f"Field {field_name} not found"

    if not modified:
        return content, False, message

    # Reconstruct content with updated frontmatter
    try:
        new_content = frontmatter.dumps(post)
        return new_content, True, message
    except Exception as e:
        return content, False, f"Error serializing frontmatter: {e}"


def bulk_update_files(
    file_paths: list[Path],
    field_name: str,
    value: str | None,
    operation: str,
    dry_run: bool = False,
) -> list[tuple[Path, bool, str]]:
    """Bulk update frontmatter fields across multiple files.

    Note: Each file path in the list is processed independently. If the same file
    appears multiple times in the list, it will be processed multiple times.

    Args:
        file_paths: List of file paths to process (may contain duplicates)
        field_name: Field to update
        value: New value for the field (or new name for rename)
        operation: Operation type (set, add, remove, rename)
        dry_run: Preview changes without modifying files

    Returns:
        List of (file_path, changed, message) tuples - one per input file path
    """
    results = []

    # Process each file path in the list, including duplicates
    for file_path in file_paths:
        # Skip certain files
        if should_skip_file(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            results.append((file_path, False, f"Error reading file: {e}"))
            continue

        new_content, modified, message = update_frontmatter_bulk(content, field_name, value, operation)

        if modified and not dry_run:
            try:
                file_path.write_text(new_content, encoding="utf-8")
            except Exception as e:
                results.append((file_path, False, f"Error writing file: {e}"))
                continue

        if modified or message:
            results.append((file_path, modified, message))

    return results
