"""Auto-fixes for frontmatter validation issues.

This module provides fixes for common frontmatter problems:
- Invalid status values (converts to valid values for document type)
- Invalid date formats (converts to ISO 8601)
- Missing frontmatter blocks (adds template frontmatter)
"""

import re
import uuid
from datetime import date, datetime
from pathlib import Path

import frontmatter

from docuchango.fixes.tags import normalize_tag
from docuchango.fixes.whitespace import ensure_required_fields, normalize_empty_values, trim_string_values
from docuchango.fixes.yaml_utils import dumps as frontmatter_dumps

# Valid status values by document type
VALID_STATUSES = {
    "adr": ["Proposed", "Accepted", "Implemented", "Deprecated", "Superseded"],
    "rfc": ["Draft", "Proposed", "Accepted", "Implemented", "Deprecated", "Superseded"],
    "prd": ["Draft", "In Review", "Approved", "In Progress", "Completed", "Cancelled"],
}

# Common status value mappings (incorrect -> correct)
STATUS_MAPPINGS = {
    "adr": {
        "proposed": "Proposed",
        "accepted": "Accepted",
        "implemented": "Implemented",
        "deprecated": "Deprecated",
        "superseded": "Superseded",
        "draft": "Proposed",
        "pending": "Proposed",
        "active": "Accepted",
        "done": "Accepted",
        "retired": "Deprecated",
        "replaced": "Superseded",
    },
    "rfc": {
        "draft": "Draft",
        "proposed": "Proposed",
        "accepted": "Accepted",
        "implemented": "Implemented",
        "deprecated": "Deprecated",
        "superseded": "Superseded",
        "pending": "Proposed",
        "review": "Proposed",
        "in review": "Proposed",
        "approved": "Accepted",
        "done": "Implemented",
        "retired": "Deprecated",
        "replaced": "Superseded",
    },
    "prd": {
        "draft": "Draft",
        "in review": "In Review",
        "approved": "Approved",
        "in progress": "In Progress",
        "completed": "Completed",
        "cancelled": "Cancelled",
        "proposed": "Draft",
        "review": "In Review",
        "active": "In Progress",
        "done": "Completed",
        "closed": "Completed",
    },
}


def get_doc_type(file_path: Path) -> str | None:
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
        if not valid_statuses:
            return False, f"No status validation configured for document type '{doc_type}'"
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
                file_path.write_text(frontmatter_dumps(post), encoding="utf-8")

            return True, f"Changed status from '{status}' to '{new_status}'"

        # Try fuzzy matching
        for key, value in mappings.items():
            if key in status_lower or status_lower in key:
                post.metadata["status"] = value

                if not dry_run:
                    file_path.write_text(frontmatter_dumps(post), encoding="utf-8")

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

        # Native date/datetime objects from PyYAML indicate the YAML value was
        # unquoted, but it may not be in canonical format (e.g. PyYAML also
        # parses space-separated or +00:00 offset timestamps into datetime).
        # Read the raw frontmatter line to check if it's already canonical.
        if isinstance(date_value, datetime) or (hasattr(date_value, "strftime") and hasattr(date_value, "year")):
            # Check the raw YAML to see if the value is already canonical
            raw_lines = content.split("---")[1].strip().splitlines() if "---" in content else []
            raw_value = None
            for line in raw_lines:
                if line.startswith(f"{date_field}:"):
                    raw_value = line.split(":", 1)[1].strip()
                    break

            # Canonical formats: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, or YYYY-MM-DDTHH:MM:SSZ
            canonical_re = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z?)?$")
            if raw_value and canonical_re.match(raw_value):
                return False, "Date already in ISO 8601 format"

            # Non-canonical: re-serialize to normalize the format
            if not dry_run:
                file_path.write_text(frontmatter_dumps(post), encoding="utf-8")

            if isinstance(date_value, datetime):
                normalized = (
                    date_value.strftime("%Y-%m-%dT%H:%M:%SZ") if date_value.tzinfo else date_value.strftime("%Y-%m-%d")
                )
            else:
                normalized = str(date_value)  # date objects have ISO format __str__
            return True, f"Normalized date object to canonical format: {normalized}"

        if not isinstance(date_value, str):
            return False, f"Date is not a string or date object: {type(date_value)}"

        # Check if already ISO 8601 string (e.g. from a quoted value)
        # Accepts: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SSZ,
        # and YYYY-MM-DDTHH:MM:SS+HH:MM / -HH:MM offsets
        if re.match(
            r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$",
            date_value,
        ):
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
                    file_path.write_text(frontmatter_dumps(post), encoding="utf-8")

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

        # Extract ID from filename (e.g., "adr-001" from "adr-001-some-title.md").
        filename = file_path.stem
        id_match = re.match(rf"^({doc_type})-(\d+)", filename, re.IGNORECASE)
        doc_id = f"{doc_type}-{int(id_match.group(2)):03d}" if id_match else f"{doc_type}-001"

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
            f"created: {today}",
            "tags: []",
            'project_id: "my-project"',
            f'doc_uuid: "{doc_uuid}"',
        ]

        # Add document-type-specific fields
        if doc_type == "adr":
            frontmatter_lines.insert(3, f"status: {default_status}")
            frontmatter_lines.insert(-2, 'deciders: "Engineering Team"')
        elif doc_type == "rfc":
            frontmatter_lines.insert(3, f"status: {default_status}")
            frontmatter_lines.insert(-2, 'author: "Engineering Team"')
        elif doc_type == "memo":
            frontmatter_lines.insert(-2, 'author: "Engineering Team"')
        elif doc_type == "prd":
            frontmatter_lines.insert(3, f"status: {default_status}")
            frontmatter_lines.insert(-2, 'author: "Product Team"')
            frontmatter_lines.insert(-2, 'target_release: "TBD"')

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


def _fix_status_metadata(metadata: dict, doc_type: str | None) -> str | None:
    """Normalize status in already-parsed metadata."""
    if "status" not in metadata:
        return None
    if not doc_type:
        return None

    status = metadata["status"]
    if not isinstance(status, str) or not status.strip():
        return None

    valid_statuses = VALID_STATUSES.get(doc_type, [])
    if status in valid_statuses:
        return None

    mappings = STATUS_MAPPINGS.get(doc_type, {})
    status_lower = status.lower().strip()
    if status_lower in mappings:
        new_status = mappings[status_lower]
        metadata["status"] = new_status
        return f"Changed status from '{status}' to '{new_status}'"

    for key, value in mappings.items():
        if key in status_lower or status_lower in key:
            metadata["status"] = value
            return f"Changed status from '{status}' to '{value}'"

    return None


def _fix_date_metadata(metadata: dict, content: str) -> str | None:
    """Normalize date or created in already-parsed metadata."""
    if "date" in metadata:
        date_field = "date"
    elif "created" in metadata:
        date_field = "created"
    else:
        return None

    date_value = metadata[date_field]

    if isinstance(date_value, (datetime, date)):
        raw_lines = content.split("---")[1].strip().splitlines() if "---" in content else []
        raw_value = None
        for line in raw_lines:
            if line.startswith(f"{date_field}:"):
                raw_value = line.split(":", 1)[1].strip()
                break
        canonical_re = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z?)?$")
        if raw_value and canonical_re.match(raw_value):
            return None
        return f"Normalized {date_field} object to canonical format"

    if not isinstance(date_value, str):
        return None

    if re.match(
        r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$",
        date_value,
    ):
        return None

    formats = [
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y.%m.%d",
        "%d.%m.%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_value, fmt)
        except ValueError:
            continue
        iso_date = parsed_date.strftime("%Y-%m-%d")
        metadata[date_field] = iso_date
        return f"Converted {date_field} from '{date_value}' to '{iso_date}'"

    return None


def _fix_tags_metadata(metadata: dict) -> list[str]:
    """Normalize tags in already-parsed metadata."""
    messages = []
    if "tags" not in metadata:
        metadata["tags"] = []
        return ["Added missing tags field (empty array)"]

    tags = metadata["tags"]
    if isinstance(tags, str):
        tags = [tags.strip()] if tags.strip() else []
        messages.append("Converted string tags to array")
    if not isinstance(tags, list):
        return messages

    original_tags = tags.copy()
    normalized_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            messages.append(f"Skipped non-string tag: {tag}")
            continue
        normalized = normalize_tag(tag)
        if normalized:
            normalized_tags.append(normalized)

    unique_tags = []
    seen = set()
    for tag in normalized_tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    sorted_tags = sorted(unique_tags)
    if sorted_tags != original_tags:
        if len(sorted_tags) < len(original_tags):
            messages.append(f"Removed {len(original_tags) - len(sorted_tags)} duplicate/invalid tags")
        if sorted_tags != normalized_tags:
            messages.append("Sorted tags alphabetically")
        if normalized_tags != original_tags:
            messages.append(f"Normalized tags: {len(normalized_tags)} tags")
    metadata["tags"] = sorted_tags
    return messages


def fix_frontmatter_metadata(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Apply frontmatter metadata fixes with a single parse/write pass."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"File contains binary content: {e}") from e
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    try:
        post = frontmatter.loads(content)
    except Exception as e:
        return False, [f"Error parsing frontmatter: {e}"]

    if not post.metadata:
        changed, message = add_missing_frontmatter(file_path, dry_run=dry_run)
        return (changed, [message] if changed else [])

    metadata = post.metadata.copy()
    original_metadata = metadata.copy()
    messages = []

    status_message = _fix_status_metadata(metadata, get_doc_type(file_path))
    if status_message:
        messages.append(status_message)

    date_message = _fix_date_metadata(metadata, content)
    force_write = date_message is not None and metadata == original_metadata
    if date_message:
        messages.append(date_message)

    messages.extend(_fix_tags_metadata(metadata))

    metadata, trim_messages = trim_string_values(metadata)
    messages.extend(trim_messages)

    metadata, empty_messages = normalize_empty_values(metadata)
    messages.extend(empty_messages)

    metadata, required_messages = ensure_required_fields(metadata)
    messages.extend(required_messages)

    changed = metadata != original_metadata or force_write
    if changed:
        post.metadata = metadata
        if not dry_run:
            file_path.write_text(frontmatter_dumps(post), encoding="utf-8")
        return True, messages

    return False, []
