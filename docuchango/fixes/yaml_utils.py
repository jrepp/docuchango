"""YAML serialization utilities for consistent frontmatter output.

Provides a custom YAML dumper that minimizes formatting changes when
round-tripping frontmatter through python-frontmatter/PyYAML:
- Preserves field order (no alphabetical sorting)
- Outputs dates/datetimes in ISO 8601 format (unquoted, with T separator)
- Keeps short lists in flow style: [tag1, tag2]
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

import frontmatter
import yaml


# Pattern matching ISO 8601 dates and datetimes
_DATE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}"  # YYYY-MM-DD
    r"(?:"  # optional time part
    r"[T ]\d{2}:\d{2}:\d{2}"  # THH:MM:SS
    r"(?:\.\d+)?"  # optional fractional seconds
    r"(?:Z|[+-]\d{2}:\d{2})?"  # optional timezone
    r")?$"
)


class _ConsistentDumper(yaml.SafeDumper):
    """YAML dumper that preserves formatting conventions."""

    pass


def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """Represent strings, using the timestamp tag for date-like values.

    PyYAML's emitter quotes plain scalars that look like dates to avoid
    ambiguity. By tagging them as timestamps, the emitter outputs them
    unquoted, consistent with native date/datetime objects.
    """
    if _DATE_RE.match(data):
        return dumper.represent_scalar("tag:yaml.org,2002:timestamp", data)
    return yaml.SafeDumper.represent_str(dumper, data)


def _represent_datetime(dumper: yaml.Dumper, data: datetime) -> yaml.ScalarNode:
    """Represent datetime objects in ISO 8601 format with T separator.

    PyYAML's default uses space separator (2026-03-05 17:56:59+00:00).
    We use the T separator to match the template format.  Aware datetimes
    are converted to UTC and suffixed with Z; naive datetimes are emitted
    without any timezone indicator.  Microseconds are preserved when present.
    """
    if data.tzinfo is not None:
        utc = data.astimezone(timezone.utc)
        if utc.microsecond:
            value = utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond:06d}Z"
        else:
            value = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        if data.microsecond:
            value = data.strftime("%Y-%m-%dT%H:%M:%S.") + f"{data.microsecond:06d}"
        else:
            value = data.strftime("%Y-%m-%dT%H:%M:%S")
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", value)


def _represent_date(dumper: yaml.Dumper, data: date) -> yaml.ScalarNode:
    """Represent date objects in ISO 8601 format (YYYY-MM-DD), unquoted."""
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", data.strftime("%Y-%m-%d"))


def _represent_list(dumper: yaml.Dumper, data: list) -> yaml.SequenceNode:  # type: ignore[type-arg]
    """Represent lists, using flow style for short scalar lists.

    Keeps tags: [architecture, design] instead of expanding to block style.
    Falls back to block style for long lists or lists containing complex values.
    """
    use_flow = len(data) <= 10 and all(isinstance(item, (str, int, float, bool)) for item in data)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=use_flow)


_ConsistentDumper.add_representer(str, _represent_str)
_ConsistentDumper.add_representer(datetime, _represent_datetime)
_ConsistentDumper.add_representer(date, _represent_date)
_ConsistentDumper.add_representer(list, _represent_list)


def dumps(post: frontmatter.Post) -> str:
    """Serialize a frontmatter Post with consistent formatting.

    Drop-in replacement for frontmatter.dumps() that:
    - Preserves field order
    - Outputs dates unquoted in ISO 8601 format
    - Keeps short lists in flow style

    Args:
        post: A python-frontmatter Post object

    Returns:
        Serialized markdown string with frontmatter
    """
    return frontmatter.dumps(post, Dumper=_ConsistentDumper, sort_keys=False)
