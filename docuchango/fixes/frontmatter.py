"""Auto-fixes for frontmatter validation issues.

This module provides fixes for common frontmatter problems:
- Invalid status values (converts to valid values for document type)
- Invalid date formats (converts to ISO 8601)
- Missing frontmatter blocks (adds template frontmatter)
"""

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter

# Valid status values by document type
VALID_STATUSES = {
    "adr": ["Proposed", "Accepted", "Deprecated", "Superseded"],
    "rfc": ["Draft", "In Review", "Accepted", "Rejected", "Implemented"],
    "memo": ["Draft", "Published", "Archived"],
    "prd": ["Draft", "In Review", "Approved", "In Progress", "Completed", "Cancelled"],
}

# Common status value mappings (incorrect -> correct)
STATUS_MAPPINGS = {
    "adr": {
        "draft": "Proposed",
        "pending": "Proposed",
        "active": "Accepted",
        "done": "Accepted",
        "retired": "Deprecated",
        "replaced": "Superseded",
    },
    "rfc": {
        "proposed": "Draft",
        "pending": "In Review",
        "approved": "Accepted",
        "done": "Implemented",
        "declined": "Rejected",
    },
    "memo": {
        "pending": "Draft",
        "public": "Published",
        "retired": "Archived",
    },
    "prd": {
        "proposed": "Draft",
        "review": "In Review",
        "active": "In Progress",
        "done": "Completed",
        "closed": "Completed",
        "cancelled": "Cancelled",
    },
}


def get_doc_type(file_path: Path) -> Optional[str]:
    """Extract document type from file path.

    Args:
        file_path: Path to the document

    Returns:
        Document type ('adr', 'rfc', 'memo', 'prd') or None
    """
    parts = file_path.parts
    for part in parts:
        part_lower = part.lower()
        if part_lower in ["adr", "rfcs", "memos", "prd"]:
            if part_lower == "rfcs":
                return "rfc"
            if part_lower == "memos":
                return "memo"
            return part_lower
    return None


def fix_status_value(file_path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Fix invalid status values in frontmatter.

    Args:
        file_path: Path to the markdown file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (changed, message)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(content)

        if "status" not in post.metadata:
            return False, "No status field found"

        doc_type = get_doc_type(file_path)
        if not doc_type:
            return False, "Could not determine document type"

        status = post.metadata["status"]
        if not isinstance(status, str):
            return False, f"Status is not a string: {type(status)}"

        # Skip empty strings
        if not status.strip():
            return False, "Status is empty"

        # Check if already valid
        valid_statuses = VALID_STATUSES.get(doc_type, [])
        if status in valid_statuses:
            return False, "Status already valid"

        # Try to map to valid status
        mappings = STATUS_MAPPINGS.get(doc_type, {})
        status_lower = status.lower().strip()

        # Direct mapping
        if status_lower in mappings:
            new_status = mappings[status_lower]
            post.metadata["status"] = new_status

            if not dry_run:
                file_path.write_text(frontmatter.dumps(post), encoding="utf-8")

            return True, f"Changed status from '{status}' to '{new_status}'"

        # Try fuzzy matching
        for key, value in mappings.items():
            if key in status_lower or status_lower in key:
                post.metadata["status"] = value

                if not dry_run:
                    file_path.write_text(frontmatter.dumps(post), encoding="utf-8")

                return True, f"Changed status from '{status}' to '{value}'"

        return False, f"No mapping found for status '{status}'"

    except Exception as e:
        return False, f"Error processing file: {e}"


def fix_date_format(file_path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Fix invalid date formats to ISO 8601 (YYYY-MM-DD).

    Args:
        file_path: Path to the markdown file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (changed, message)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(content)

        # Check for date or created field
        date_field = None
        if "date" in post.metadata:
            date_field = "date"
        elif "created" in post.metadata:
            date_field = "created"
        else:
            return False, "No date field found"

        date_value = post.metadata[date_field]

        # If already a date or datetime object, convert to string
        if isinstance(date_value, datetime):
            date_str = date_value.strftime("%Y-%m-%d")
            post.metadata[date_field] = date_str

            if not dry_run:
                file_path.write_text(frontmatter.dumps(post), encoding="utf-8")

            return True, f"Converted datetime object to ISO 8601: {date_str}"

        # Handle datetime.date objects
        if hasattr(date_value, "strftime") and hasattr(date_value, "year"):
            date_str = date_value.strftime("%Y-%m-%d")
            post.metadata[date_field] = date_str

            if not dry_run:
                file_path.write_text(frontmatter.dumps(post), encoding="utf-8")

            return True, f"Converted date object to ISO 8601: {date_str}"

        if not isinstance(date_value, str):
            return False, f"Date is not a string or date object: {type(date_value)}"

        # Check if already ISO 8601
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_value):
            return False, "Date already in ISO 8601 format"

        # Try various date formats
        formats = [
            "%Y/%m/%d",  # 2025/01/26
            "%d/%m/%Y",  # 26/01/2025
            "%m/%d/%Y",  # 01/26/2025
            "%Y.%m.%d",  # 2025.01.26
            "%d.%m.%Y",  # 26.01.2025
            "%B %d, %Y",  # January 26, 2025
            "%b %d, %Y",  # Jan 26, 2025
            "%d %B %Y",  # 26 January 2025
            "%d %b %Y",  # 26 Jan 2025
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_value, fmt)
                iso_date = parsed_date.strftime("%Y-%m-%d")
                post.metadata[date_field] = iso_date

                if not dry_run:
                    file_path.write_text(frontmatter.dumps(post), encoding="utf-8")

                return True, f"Converted date from '{date_value}' to '{iso_date}'"
            except ValueError:
                continue

        return False, f"Could not parse date: '{date_value}'"

    except Exception as e:
        return False, f"Error processing file: {e}"


def add_missing_frontmatter(file_path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Add missing frontmatter block to a document.

    Args:
        file_path: Path to the markdown file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (changed, message)
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        # Check if frontmatter already exists
        if content.strip().startswith("---"):
            return False, "Frontmatter already exists"

        doc_type = get_doc_type(file_path)
        if not doc_type:
            return False, "Could not determine document type"

        # Extract ID from filename (e.g., "adr-001" from "adr-001-some-title.md")
        filename = file_path.stem
        id_match = re.match(r"^([a-z]+-\d+)", filename)
        doc_id = id_match.group(1) if id_match else filename

        # Generate title from filename
        title_parts = filename.replace("-", " ").split()
        title = " ".join(word.capitalize() for word in title_parts)

        # Get default status for document type
        default_status = VALID_STATUSES.get(doc_type, ["Draft"])[0]

        # Current date
        today = datetime.now().strftime("%Y-%m-%d")

        # Generate UUID
        doc_uuid = str(uuid.uuid4())

        # Build frontmatter template
        frontmatter_lines = [
            "---",
            f'id: "{doc_id}"',
            f'title: "{title}"',
            f"status: {default_status}",
            f"date: {today}",
            "tags: []",
            'project_id: "my-project"',
            f'doc_uuid: "{doc_uuid}"',
        ]

        # Add document-type-specific fields
        if doc_type == "adr":
            frontmatter_lines.insert(-2, 'deciders: "Engineering Team"')

        frontmatter_lines.append("---")
        frontmatter_block = "\n".join(frontmatter_lines)

        # Prepend frontmatter to content
        new_content = f"{frontmatter_block}\n\n{content}"

        if not dry_run:
            file_path.write_text(new_content, encoding="utf-8")

        return True, f"Added frontmatter block with ID '{doc_id}'"

    except Exception as e:
        return False, f"Error processing file: {e}"


def fix_all_frontmatter(file_path: Path, dry_run: bool = False) -> list[str]:
    """Apply all frontmatter fixes to a file.

    Args:
        file_path: Path to the markdown file
        dry_run: If True, don't write changes

    Returns:
        List of messages describing changes made

    Raises:
        UnicodeDecodeError: If file contains binary content
        ValueError: If file is not a valid text file
    """
    messages = []

    # Check if file is readable as text
    try:
        file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"File contains binary content: {e}") from e

    # Try to add missing frontmatter first
    changed, msg = add_missing_frontmatter(file_path, dry_run)
    if changed:
        messages.append(f"✓ {msg}")

    # Fix status value
    changed, msg = fix_status_value(file_path, dry_run)
    if changed:
        messages.append(f"✓ {msg}")

    # Fix date format
    changed, msg = fix_date_format(file_path, dry_run)
    if changed:
        messages.append(f"✓ {msg}")

    return messages
