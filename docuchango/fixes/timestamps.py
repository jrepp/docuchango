"""Update document timestamps based on git history.

This module provides functionality to update document timestamps using git history:
- For all docs: Add missing 'created' from first commit datetime
- Migrates legacy 'date' field in ADRs to 'created' field

Note: The 'updated' field is not stored in frontmatter as it can be derived from git history.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date, datetime, timezone
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
        # Normalize UTC suffixes before converting to UTC.
        first_commit = first_commit.replace("Z", "+00:00")
        # Convert to UTC and format as ISO 8601 datetime
        created_dt = datetime.fromisoformat(first_commit).astimezone(timezone.utc)
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

        # Normalize UTC suffixes before converting to UTC.
        last_commit = last_commit.replace("Z", "+00:00")
        # Convert to UTC and format as ISO 8601 datetime
        updated_dt = datetime.fromisoformat(last_commit).astimezone(timezone.utc)
        updated_datetime = updated_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        return created_datetime, updated_datetime

    except subprocess.CalledProcessError:
        return None, None


def _line_indent(line: str) -> int:
    """Return the number of leading spaces on a line (YAML forbids tab indentation)."""
    stripped = line.lstrip(" ")
    return len(line) - len(stripped)


def _frontmatter_bounds(lines: list[str]) -> tuple[int, int]:
    """Return the ``[start, end)`` line range covering the frontmatter body.

    Falls back to the whole document when no ``---`` delimited block is found,
    which keeps these helpers usable on bare frontmatter snippets.
    """
    if lines and lines[0].rstrip("\r\n") == "---":
        for index in range(1, len(lines)):
            if lines[index].rstrip("\r\n") == "---":
                return 1, index
    return 0, len(lines)


def _field_blocks(lines: list[str], field_name: str) -> list[tuple[int, int]]:
    """Locate every top-level ``field_name:`` block inside the frontmatter.

    A "block" is the key's own line plus any continuation lines that belong to
    its value: block scalars (``|``/``>``), multi-line quoted or plain scalars,
    block sequences/mappings and wrapped flow collections. All of those are
    indented further than the key, so any following line that is indented (or a
    blank line followed by an indented line) is part of the value.

    Returns:
        A list of ``(start, end)`` half-open line-index ranges.
    """
    start, end = _frontmatter_bounds(lines)
    key_pattern = re.compile(rf"^{re.escape(field_name)}:")

    blocks: list[tuple[int, int]] = []
    index = start
    while index < end:
        if not key_pattern.match(lines[index]):
            index += 1
            continue

        block_end = index + 1
        cursor = index + 1
        while cursor < end:
            if not lines[cursor].strip():
                # Blank lines only belong to the value if more indented lines follow.
                cursor += 1
                continue
            if _line_indent(lines[cursor]) == 0:
                break
            cursor += 1
            block_end = cursor

        blocks.append((index, block_end))
        index = block_end

    return blocks


def _split_value_and_comment(rest: str) -> str:
    """Return the trailing comment (with its leading whitespace) from a value.

    Quotes are tracked so that a ``#`` inside a quoted scalar is not mistaken
    for a comment. Returns an empty string when there is no comment.
    """
    quote: str | None = None
    index = 0
    while index < len(rest):
        char = rest[index]
        if quote is not None:
            if quote == '"' and char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == "#" and (index == 0 or rest[index - 1] in " \t"):
            comment_start = index
            while comment_start > 0 and rest[comment_start - 1] in " \t":
                comment_start -= 1
            return rest[comment_start:]
        index += 1
    return ""


def update_frontmatter_field(content: str, field_name: str, new_value: str) -> str:
    """Update a specific field in YAML frontmatter.

    Handles simple fields (``date: value``), fields with trailing comments, and
    multi-line values. For a multi-line value (block scalar, wrapped scalar or
    block sequence) the whole value is replaced: the continuation lines are
    dropped instead of being left dangling under the new value.

    All other lines are left byte-identical, which line-oriented editing gives
    us and a YAML round-trip would not (it would drop comments, collapse
    duplicate keys and renormalize quoting).

    Args:
        content: The full file content
        field_name: Name of the field to update
        new_value: New value for the field

    Returns:
        Updated content
    """
    lines = content.splitlines(keepends=True)
    blocks = _field_blocks(lines, field_name)
    if not blocks:
        return content

    for start, end in reversed(blocks):
        line = lines[start]
        body = line.rstrip("\r\n")
        line_ending = line[len(body) :]

        after_key = body[len(field_name) + 1 :]
        separator = after_key[: len(after_key) - len(after_key.lstrip(" \t"))] or " "
        comment = _split_value_and_comment(after_key.strip())
        if comment and not comment[0].isspace():
            # The field had no value at all, only a comment: keep them apart.
            comment = f"  {comment}"

        lines[start:end] = [f"{field_name}:{separator}{new_value}{comment}{line_ending}"]

    return "".join(lines)


def remove_frontmatter_field(content: str, field_name: str) -> str:
    """Remove a top-level field, including any multi-line value it carries."""
    lines = content.splitlines(keepends=True)
    blocks = _field_blocks(lines, field_name)
    if not blocks:
        return content

    for start, end in reversed(blocks):
        del lines[start:end]

    return "".join(lines)


def insert_created_field(content: str, created_date: str) -> str:
    """Insert a created field into frontmatter near other identity metadata."""
    created_line = f"created: {created_date}\n"

    for pattern in (r"(status:.*\n)", r"(id:.*\n)", r"(^---\n)"):
        if re.search(pattern, content, flags=re.MULTILINE):
            return re.sub(pattern, rf"\1{created_line}", content, count=1, flags=re.MULTILINE)

    return content


def frontmatter_value_to_string(value: object) -> str:
    """Convert a parsed frontmatter value back to a YAML-friendly timestamp string."""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
            return value.strftime("%Y-%m-%dT%H:%M:%SZ")
        return value.strftime("%Y-%m-%dT%H:%M:%S")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    return str(value)


def migrate_date_to_created(content: str, created_date: str) -> str:
    """Migrate legacy 'date' field to 'created' field.

    Args:
        content: The full file content
        created_date: Creation date to use

    Returns:
        Updated content with 'date' removed and 'created' added if needed
    """
    new_content = remove_frontmatter_field(content, "date")
    if re.search(r"^created:.*$", new_content, flags=re.MULTILINE):
        return new_content

    return insert_created_field(new_content, created_date)


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

    modified = False
    new_content = content
    has_legacy_date = "date" in post.metadata
    has_created = "created" in post.metadata

    if has_legacy_date and has_created:
        new_content = remove_frontmatter_field(new_content, "date")
        if new_content != content:
            modified = True
            messages.append("Removed deprecated 'date' field")
    elif has_legacy_date:
        created_date, _ = get_git_dates(file_path)
        if not created_date:
            created_date = frontmatter_value_to_string(post.metadata["date"])

        new_content = migrate_date_to_created(new_content, created_date)
        if new_content != content:
            modified = True
            messages.append("Migrated 'date' → 'created'")
    elif has_created:
        return False, []
    else:
        created_date, _ = get_git_dates(file_path)
        if not created_date:
            return False, ["No git history found"]

        new_content = insert_created_field(new_content, created_date)
        if new_content != content:
            modified = True
            messages.append(f"Added 'created': {created_date}")

    # Write updated content
    if modified and not dry_run:
        try:
            file_path.write_text(new_content, encoding="utf-8")
        except Exception as e:
            return False, [f"Error writing file: {e}"]

    return modified, messages
