"""YAML serialization utilities for consistent frontmatter output.

Provides a custom YAML dumper that ensures date-like strings are serialized
without quotes, matching the behavior of native YAML date types. This prevents
inconsistent quoting when dates are stored as strings vs datetime objects.
"""

from __future__ import annotations

import re

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
    """YAML dumper that outputs date-like strings without quotes."""

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


_ConsistentDumper.add_representer(str, _represent_str)


def dumps(post: frontmatter.Post) -> str:
    """Serialize a frontmatter Post with consistent date formatting.

    Drop-in replacement for frontmatter.dumps() that ensures date-like
    strings are never single-quoted in the output.

    Args:
        post: A python-frontmatter Post object

    Returns:
        Serialized markdown string with frontmatter
    """
    return frontmatter.dumps(post, Dumper=_ConsistentDumper)
