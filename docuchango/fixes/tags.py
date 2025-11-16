"""Auto-fixes for tags field issues.

This module provides fixes for common tag-related problems:
- Convert string tags to arrays
- Normalize tags to lowercase with dashes
- Remove duplicates
- Sort alphabetically
"""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter


def normalize_tag(tag: str) -> str:
    """Normalize a single tag to lowercase with dashes.

    Args:
        tag: Tag string to normalize

    Returns:
        Normalized tag string
    """
    # Convert to lowercase
    tag = tag.lower().strip()

    # Replace spaces and underscores with dashes
    tag = re.sub(r'[\s_]+', '-', tag)

    # Remove special characters except dashes
    tag = re.sub(r'[^a-z0-9-]', '', tag)

    # Remove multiple consecutive dashes
    tag = re.sub(r'-+', '-', tag)

    # Remove leading/trailing dashes
    tag = tag.strip('-')

    return tag


def fix_tags(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Fix tags field issues in frontmatter.

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

    # Check if tags field exists
    if "tags" not in post.metadata:
        # Add empty tags array
        post.metadata["tags"] = []
        messages.append("Added missing tags field (empty array)")
        changed = True
    else:
        tags = post.metadata["tags"]
        changed = False

        # Convert string to array
        if isinstance(tags, str):
            if tags.strip():
                tags = [tags.strip()]
            else:
                tags = []
            messages.append("Converted string tags to array")
            changed = True

        # Ensure it's a list
        if not isinstance(tags, list):
            return False, [f"Tags field has invalid type: {type(tags)}"]

        # Normalize each tag
        original_tags = tags.copy()
        normalized_tags = []

        for tag in tags:
            if not isinstance(tag, str):
                messages.append(f"Skipped non-string tag: {tag}")
                continue

            normalized = normalize_tag(tag)
            if normalized:  # Skip empty tags
                normalized_tags.append(normalized)

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in normalized_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        # Sort alphabetically
        sorted_tags = sorted(unique_tags)

        # Check if tags changed
        if sorted_tags != original_tags:
            changed = True
            if len(sorted_tags) < len(original_tags):
                removed = len(original_tags) - len(sorted_tags)
                messages.append(f"Removed {removed} duplicate/invalid tags")
            if sorted_tags != normalized_tags:
                messages.append("Sorted tags alphabetically")
            if normalized_tags != original_tags:
                messages.append(f"Normalized tags: {len(normalized_tags)} tags")

        post.metadata["tags"] = sorted_tags

    # Write changes
    if changed:
        if not dry_run:
            try:
                new_content = frontmatter.dumps(post)
                file_path.write_text(new_content, encoding="utf-8")
            except Exception as e:
                return False, [f"Error writing file: {e}"]

        return True, messages

    return False, []
