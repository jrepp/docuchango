#!/usr/bin/env python3
"""Fix broken documentation links by converting full filenames to short-form IDs.

Usage:
    uv run tooling/fix_broken_links.py [--dry-run]
"""

import argparse
import re
from pathlib import Path

# Mapping of common broken link patterns to correct formats
LINK_FIXES = {
    # RFCs - full filename to short ID
    r"/rfc/rfc-(\d+)-[a-z-]+": r"/rfc/rfc-\1",
    r"/prism-data-layer/rfc/rfc-(\d+)-[a-z-]+": r"/rfc/rfc-\1",
    r"/prism-data-layer/rfc/RFC-(\d+)-[a-z-]+": r"/rfc/rfc-\1",
    r"\.\/RFC-(\d+)-[a-z-]+": r"/rfc/rfc-\1",
    # ADRs - full filename to short ID
    r"/adr/adr-(\d+)-[a-z-]+": r"/adr/adr-\1",
    r"/prism-data-layer/adr/adr-(\d+)-[a-z-]+": r"/adr/adr-\1",
    # MEMOs - full filename to short ID
    r"/memos/memo-(\d+)-[a-z-]+": r"/memos/memo-\1",
    r"/prism-data-layer/memos/memo-(\d+)-[a-z-]+": r"/memos/memo-\1",
    # Remove /prism-data-layer prefix from already short paths
    r"/prism-data-layer/(adr/adr-\d+)": r"/\1",
    r"/prism-data-layer/(rfc/rfc-\d+)": r"/\1",
    r"/prism-data-layer/(memos/memo-\d+)": r"/\1",
    r"/prism-data-layer/(prd)": r"/\1",
    r"/prism-data-layer/(key-documents)": r"/\1",
    r"/prism-data-layer/(netflix/[a-z\-]+)": r"/\1",
    # Fix incorrectly converted RFC numbers (rfc-211 should be rfc-021)
    r"/rfc/rfc-211([^0-9])": r"/rfc/rfc-021\1",
    r"/rfc/rfc-211$": r"/rfc/rfc-021",
    # Fix netflix links - add netflix- prefix to all document names
    r"/netflix/abstractions\b": r"/netflix/netflix-abstractions",
    r"/netflix/write-ahead-log\b": r"/netflix/netflix-write-ahead-log",
    r"/netflix/scale\b": r"/netflix/netflix-scale",
    r"/netflix/dual-write-migration\b": r"/netflix/netflix-dual-write-migration",
    r"/netflix/data-evolve-migration\b": r"/netflix/netflix-data-evolve-migration",
    r"/netflix/summary\b": r"/netflix/netflix-summary",
    r"/netflix/key-use-cases\b": r"/netflix/netflix-key-use-cases",
    r"/netflix/netflix-index\b": r"/netflix/netflix-index",  # This one is already correct but keeping for completeness
    r"/netflix/video1\b": r"/netflix/netflix-video1",
    r"/netflix/video2\b": r"/netflix/netflix-video2",
}


def fix_links_in_file(file_path: Path, dry_run: bool = False) -> int:
    """Fix broken links in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        changes = 0

        for pattern, replacement in LINK_FIXES.items():
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                changes += count
                content = new_content

        if content != original_content:
            if dry_run:
                print(f"Would fix {changes} links in: {file_path}")
            else:
                file_path.write_text(content)
                print(f"Fixed {changes} links in: {file_path}")
            return changes

        return 0
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Fix broken documentation links")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    docs_cms = repo_root / "docs-cms"
    docusaurus_docs = repo_root / "docusaurus" / "docs"

    total_changes = 0
    total_files = 0

    # Process all markdown files in docs-cms
    for md_file in docs_cms.rglob("*.md"):
        changes = fix_links_in_file(md_file, args.dry_run)
        if changes > 0:
            total_changes += changes
            total_files += 1

    # Process all markdown files in docusaurus/docs
    for md_file in docusaurus_docs.rglob("*.md"):
        changes = fix_links_in_file(md_file, args.dry_run)
        if changes > 0:
            total_changes += changes
            total_files += 1

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Fixed {total_changes} links in {total_files} files")


if __name__ == "__main__":
    main()
