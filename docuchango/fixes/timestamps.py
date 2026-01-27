"""Update document timestamps based on git history.

This module provides functionality to update document timestamps using git history:
- For all docs: Update 'created' to first commit datetime
- Migrates legacy 'date' field in ADRs to 'created' field

Note: The 'updated' field is not stored in frontmatter as it can be derived from git history.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

import frontmatter


def get_git_dates(file_path: Path) -> tuple[str | None, str | None]:
    """Get creation and last update datetimes from git history.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (created_datetime, updated_datetime) in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
        Returns (None, None) if file is not in git history
    """
    try:
        # Get absolute path and work from file's directory
        abs_path = file_path.resolve()
        cwd = abs_path.parent

        # Get first commit date (creation)
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%aI", "--reverse", "--", abs_path.name],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        commits = result.stdout.strip().split("\n")
        if not commits or not commits[0]:
            return None, None

        first_commit = commits[0]
        # Replace 'Z' with '+00:00' for Python 3.9/3.10 compatibility (Python 3.11+ handles 'Z' natively)
        first_commit = first_commit.replace("Z", "+00:00")
        # Convert to UTC and format as ISO 8601 datetime
        created_dt = datetime.fromisoformat(first_commit).astimezone(tz=None)
        created_datetime = created_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Get last commit date (update)
        result = subprocess.run(
            ["git", "log", "--follow", "-1", "--format=%aI", "--", abs_path.name],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        last_commit = result.stdout.strip()
        if not last_commit:
            return created_datetime, created_datetime

        # Replace 'Z' with '+00:00' for Python 3.9/3.10 compatibility (Python 3.11+ handles 'Z' natively)
        last_commit = last_commit.replace("Z", "+00:00")
        # Convert to UTC and format as ISO 8601 datetime
        updated_dt = datetime.fromisoformat(last_commit).astimezone(tz=None)
        updated_datetime = updated_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        return created_datetime, updated_datetime

    except subprocess.CalledProcessError:
        return None, None


def update_frontmatter_field(content: str, field_name: str, new_value: str) -> str:
    """Update a specific field in YAML frontmatter.

    Handles both simple fields (date: value) and fields with comments.
    Pattern matches field name, value, and optional trailing comments.

    Args:
        content: The full file content
        field_name: Name of the field to update
        new_value: New value for the field

    Returns:
        Updated content
    """
    pattern = rf"^({field_name}:\s*)([^\s#]+)(.*?)$"

    def replacer(match):
        prefix = match.group(1)  # "field: "
        suffix = match.group(3)  # comments and whitespace
        return f"{prefix}{new_value}{suffix}"

    # Update the field
    return re.sub(pattern, replacer, content, flags=re.MULTILINE)


def migrate_date_to_created(content: str, created_date: str) -> str:
    """Migrate legacy 'date' field to 'created' field.

    Args:
        content: The full file content
        created_date: Creation date to use

    Returns:
        Updated content with 'date' removed and 'created' added
    """
    # Remove the old 'date' field line
    date_pattern = r"^date:.*\n"
    new_content = re.sub(date_pattern, "", content, flags=re.MULTILINE)

    # Try to insert created after the status line
    insert_pattern = r"(status:.*\n)"
    created_line = f"created: {created_date}\n"

    if re.search(insert_pattern, new_content, flags=re.MULTILINE):
        # Status field exists, insert after it
        new_content = re.sub(insert_pattern, rf"\1{created_line}", new_content, flags=re.MULTILINE)
    else:
        # No status field, insert after the id field or at the beginning of frontmatter
        id_pattern = r"(id:.*\n)"
        if re.search(id_pattern, new_content, flags=re.MULTILINE):
            new_content = re.sub(id_pattern, rf"\1{created_line}", new_content, flags=re.MULTILINE)
        else:
            # Insert right after the opening ---
            frontmatter_pattern = r"(---\n)"
            new_content = re.sub(frontmatter_pattern, rf"\1{created_line}", new_content, flags=re.MULTILINE)

    return new_content


def update_document_timestamps(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Update timestamps in a document based on git history.

    Args:
        file_path: Path to the markdown file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (changed, messages)
    """
    messages = []

    # Skip templates
    if "template" in file_path.name.lower() or file_path.name.startswith("000-"):
        return False, []

    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    # Parse frontmatter
    try:
        post = frontmatter.loads(content)
    except Exception as e:
        return False, [f"Error parsing frontmatter: {e}"]

    if not post.metadata:
        return False, ["No frontmatter found"]

    # Get git dates
    created_date, updated_date = get_git_dates(file_path)
    if not created_date:
        return False, ["No git history found"]

    modified = False
    new_content = content

    # Check if we need to migrate from legacy 'date' field
    if "date" in post.metadata and "created" not in post.metadata:
        # Legacy document with only 'date' field - migrate to 'created'
        new_content = migrate_date_to_created(new_content, created_date)
        modified = True
        messages.append("Migrated 'date' → 'created'")
    else:
        # Standard handling for created field
        # Update or add created field
        if "created" in post.metadata:
            old_created = post.metadata["created"]
            if isinstance(old_created, str):
                old_created_str = old_created
            elif hasattr(old_created, "strftime"):
                old_created_str = old_created.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                old_created_str = str(old_created)

            if old_created_str != created_date:
                new_content = update_frontmatter_field(new_content, "created", created_date)
                modified = True
                messages.append(f"Updated 'created': {old_created_str} → {created_date}")
        else:
            # Add missing created field
            # Try to insert after status field
            insert_pattern = r"(status:.*\n)"
            created_line = f"created: {created_date}\n"
            if re.search(insert_pattern, new_content, flags=re.MULTILINE):
                new_content = re.sub(insert_pattern, rf"\1{created_line}", new_content, flags=re.MULTILINE)
                modified = True
                messages.append(f"Added 'created': {created_date}")

    # Write updated content
    if modified and not dry_run:
        try:
            file_path.write_text(new_content, encoding="utf-8")
        except Exception as e:
            return False, [f"Error writing file: {e}"]

    return modified, messages
