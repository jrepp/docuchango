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

from docuchango.markdown import frontmatter_body_bounds
from docuchango.text_io import read_text, write_text


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


def _field_blocks(lines: list[str], field_name: str) -> list[tuple[int, int]]:
    """Locate every top-level ``field_name:`` block inside the frontmatter (FM-007).

    A "block" is the key's own line plus any continuation lines that belong to
    its value: block scalars (``|``/``>``), multi-line quoted or plain scalars,
    block sequences/mappings and wrapped flow collections. All of those are
    indented further than the key, so any following line that is indented (or a
    blank line followed by an indented line) is part of the value.

    Only the ``---`` delimited block on the first line is searched, using the
    delimiter rule the validator and python-frontmatter share (see
    :func:`docuchango.markdown.is_frontmatter_delimiter`). Without a closed
    block there is nothing to search: a ``field_name:`` line in the Markdown
    body is never a field.

    Returns:
        A list of ``(start, end)`` half-open line-index ranges.
    """
    bounds = frontmatter_body_bounds(lines)
    if bounds is None:
        return []
    start, end = bounds
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

    Only fields inside the ``---`` delimited block are touched; content with
    no such block is returned unchanged.

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
    """Remove a top-level frontmatter field, including any multi-line value it carries.

    Only fields inside the ``---`` delimited block are removed (FM-007); a
    look-alike line in the Markdown body, or in content with no block at all,
    is left alone.
    """
    lines = content.splitlines(keepends=True)
    blocks = _field_blocks(lines, field_name)
    if not blocks:
        return content

    for start, end in reversed(blocks):
        del lines[start:end]

    return "".join(lines)


def insert_created_field(content: str, created_date: str) -> str:
    """Insert a ``created`` field into the frontmatter block (FM-007).

    The field goes after the ``status`` value, else after the ``id`` value,
    else first in the block. Only top-level keys inside the ``---`` delimited
    block are considered, so a ``status:`` line in a fenced example or a body
    bullet such as ``- Work status: ...`` is never used as the anchor. A
    multi-line value is skipped whole, so the field never lands inside it.

    The insert is idempotent: content whose block already has ``created``, or
    that has no delimited block at all, is returned unchanged.
    """
    lines = content.splitlines(keepends=True)
    bounds = frontmatter_body_bounds(lines)
    if bounds is None or _field_blocks(lines, "created"):
        return content

    line_ending = "\r\n" if lines[0].endswith("\r\n") else "\n"
    insert_at = bounds[0]
    for anchor in ("status", "id"):
        blocks = _field_blocks(lines, anchor)
        if blocks:
            insert_at = blocks[0][1]
            break

    lines.insert(insert_at, f"created: {created_date}{line_ending}")
    return "".join(lines)


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


def _has_field(content: str, field_name: str) -> bool:
    """Whether the frontmatter block of ``content`` has a top-level ``field_name``."""
    return bool(_field_blocks(content.splitlines(keepends=True), field_name))


def migrate_date_to_created(content: str, created_date: str) -> str:
    """Migrate the legacy ``date`` field to ``created`` (FM-007).

    The migration is all or nothing. ``date`` is only removed once ``created``
    is in the frontmatter block: either it was already there, or it has just
    been inserted. When neither holds -- there is no closed ``---`` block on
    the first line, say -- the content is returned unchanged, so the date is
    never dropped without its replacement being written.

    Args:
        content: The full file content
        created_date: Creation date to write when ``created`` is missing

    Returns:
        The content with ``created`` in the block and ``date`` removed, or the
        original content when that cannot be done.
    """
    if not _has_field(content, "date"):
        return content

    with_created = content if _has_field(content, "created") else insert_created_field(content, created_date)
    if not _has_field(with_created, "created"):
        return content

    migrated = remove_frontmatter_field(with_created, "date")
    if _has_field(migrated, "date"):
        return content
    return migrated


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
        content = read_text(file_path)
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

    if has_legacy_date:
        # FM-007: 'date' is removed only together with a 'created' in the
        # block, so the date is never lost; see migrate_date_to_created.
        if has_created:
            created_date = frontmatter_value_to_string(post.metadata["created"])
        else:
            created_date, _ = get_git_dates(file_path)
            if not created_date:
                created_date = frontmatter_value_to_string(post.metadata["date"])

        new_content = migrate_date_to_created(new_content, created_date)
        if new_content == content:
            messages.append("FM-007: Left legacy 'date' in place: no closed '---' block on the first line")
        elif _has_field(content, "created"):
            modified = True
            messages.append("FM-007: Removed deprecated 'date' field")
        else:
            modified = True
            messages.append("FM-007: Migrated 'date' → 'created'")
    elif has_created:
        return False, []
    else:
        created_date, _ = get_git_dates(file_path)
        if not created_date:
            return False, ["No git history found"]

        new_content = insert_created_field(new_content, created_date)
        if new_content != content:
            modified = True
            messages.append(f"FM-007: Added 'created': {created_date}")

    # Write updated content
    if modified and not dry_run:
        try:
            write_text(file_path, new_content)
        except Exception as e:
            return False, [f"Error writing file: {e}"]

    return modified, messages
