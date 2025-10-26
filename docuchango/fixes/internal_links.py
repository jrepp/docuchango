#!/usr/bin/env python3
"""Fix internal links in documentation files to match new filenames.

Updates links from date-prefixed format to Docusaurus format:
  ../rfcs/2025-10-13-rfc-001-vpc-management-gateway.md → ../rfcs/rfc-001-vpc-management-gateway.md
  ./2025-10-15-adr-003-vpc-subnet.md → ./adr-003-vpc-subnet.md

Usage:
    uv run tooling/fix_internal_links.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path


def fix_links_in_content(content: str) -> tuple[str, int]:
    """Fix all internal markdown links in content.

    Returns: (fixed_content, number_of_fixes)
    """
    fixes = 0

    # Pattern: [text](path/YYYY-MM-DD-type-NNN-name.md)
    # Replace with: [text](path/type-NNN-name.md)
    def fix_link(match):
        nonlocal fixes
        text = match.group(1)
        before_path = match.group(2)  # ../rfcs/, ./, etc.
        match.group(3)  # YYYY-MM-DD-
        rest = match.group(4)  # type-NNN-name.md
        anchor = match.group(5) or ""  # #section or empty

        fixes += 1
        return f"[{text}]({before_path}{rest}{anchor})"

    # Match markdown links with date prefix in path
    # Captures: [text](../path/YYYY-MM-DD-type-NNN-name.md#anchor)
    pattern = r"\[([^\]]+)\]\(([./]*[^)]*/)(\d{4}-\d{2}-\d{2}-)((adr|rfc|memo)-[^)#]+\.md)(#[^)]+)?\)"
    content = re.sub(pattern, fix_link, content)

    # Also match without directory prefix: [text](YYYY-MM-DD-type-NNN-name.md)
    pattern2 = r"\[([^\]]+)\]\((\d{4}-\d{2}-\d{2}-)((adr|rfc|memo)-[^)#]+\.md)(#[^)]+)?\)"

    def fix_link2(match):
        nonlocal fixes
        text = match.group(1)
        rest = match.group(3)  # type-NNN-name.md
        anchor = match.group(4) or ""
        fixes += 1
        return f"[{text}]({rest}{anchor})"

    content = re.sub(pattern2, fix_link2, content)

    return content, fixes


def fix_links_in_file(file_path: Path, dry_run: bool = False) -> int:
    """Fix links in a single file. Returns number of fixes."""
    try:
        content = file_path.read_text(encoding="utf-8")
        fixed_content, fixes = fix_links_in_content(content)

        if fixes > 0:
            if dry_run:
                print(f"  [DRY RUN] Would fix {fixes} link(s) in {file_path.name}")
            else:
                file_path.write_text(fixed_content, encoding="utf-8")
                print(f"  ✅ Fixed {fixes} link(s) in {file_path.name}")
            return fixes

        return 0
    except Exception as e:
        print(f"  ❌ Error processing {file_path.name}: {e}")
        return 0


def process_directory(directory: Path, dry_run: bool = False) -> dict:
    """Process all markdown files in a directory."""
    stats = {
        "files_checked": 0,
        "files_modified": 0,
        "total_fixes": 0,
    }

    if not directory.exists():
        return stats

    # Find all markdown files recursively
    for md_file in sorted(directory.rglob("*.md")):
        if md_file.name == "README.md" or "template" in md_file.name.lower():
            continue

        stats["files_checked"] += 1
        fixes = fix_links_in_file(md_file, dry_run)
        if fixes > 0:
            stats["files_modified"] += 1
            stats["total_fixes"] += fixes

    return stats


def main():
    parser = argparse.ArgumentParser(description="Fix internal links to match new Docusaurus filenames")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent
    docs_cms = root_dir / "docs-cms"

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")

    print("🔗 Fixing internal documentation links...\n")

    total_stats = {"files_checked": 0, "files_modified": 0, "total_fixes": 0}

    # Process docs-cms directory recursively
    stats = process_directory(docs_cms, args.dry_run)
    total_stats["files_checked"] += stats["files_checked"]
    total_stats["files_modified"] += stats["files_modified"]
    total_stats["total_fixes"] += stats["total_fixes"]

    # Print summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Files checked:  {total_stats['files_checked']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Links fixed:    {total_stats['total_fixes']}")
    print("=" * 80)

    if args.dry_run:
        print("\n✅ Dry run complete - no files were modified")
        print("   Run without --dry-run to apply changes")
    elif total_stats["total_fixes"] > 0:
        print("\n✅ Links fixed successfully!")
        print("\nNext steps:")
        print("1. Validate docs:  uv run python3 -m tooling.validate_docs")
        print("2. Commit changes: git add docs-cms/ && git commit -m 'Fix internal links'")
    else:
        print("\n✅ All links already correct!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
