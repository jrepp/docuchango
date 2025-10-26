#!/usr/bin/env python3
"""Fix cross-plugin documentation links.

Docusaurus plugins are isolated, so relative links between plugins don't work.
This script converts cross-plugin relative links to absolute Docusaurus paths.

Usage:
    uv run tooling/fix_cross_plugin_links.py
"""

import re
from pathlib import Path


def fix_cross_plugin_links(file_path: Path, dry_run: bool = False) -> int:
    """Fix cross-plugin links in a single file."""
    content = file_path.read_text()
    original_content = content

    # Pattern: [text](../rfcs/RFC-XXX-name.md) -> [text](/rfc/RFC-XXX-name)
    content = re.sub(r"\]\(\.\./rfcs/(RFC-[^)]+)\.md\)", r"](/rfc/\1)", content)

    # Pattern: [text](../adr/ADR-XXX-name.md) -> [text](/adr/ADR-XXX-name)
    content = re.sub(r"\]\(\.\./adr/(ADR-[^)]+)\.md\)", r"](/adr/\1)", content)

    # Pattern: [text](../memos/MEMO-XXX-name.md) -> [text](/memos/MEMO-XXX-name)
    content = re.sub(r"\]\(\.\./memos/(MEMO-[^)]+)\.md\)", r"](/memos/\1)", content)

    if content != original_content:
        if not dry_run:
            file_path.write_text(content)
        return 1
    return 0


def main():
    """Fix all cross-plugin links in docs-cms."""
    docs_cms = Path(__file__).parent.parent / "docs-cms"

    directories = ["adr", "rfcs", "memos"]
    total_fixed = 0

    for directory in directories:
        dir_path = docs_cms / directory
        if not dir_path.exists():
            continue

        for md_file in dir_path.glob("*.md"):
            if md_file.name in ["index.md", "000-template.md"]:
                continue

            fixed = fix_cross_plugin_links(md_file)
            if fixed:
                print(f"✓ Fixed {md_file.relative_to(docs_cms)}")
                total_fixed += 1

    print(f"\n✅ Fixed {total_fixed} files with cross-plugin links")


if __name__ == "__main__":
    main()
