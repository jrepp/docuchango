#!/usr/bin/env python3
"""Fix MDX syntax issues in markdown files.

MDX parser interprets `<number` as JSX opening tag. This script fixes:
- <1 minute → `<1 minute`
- <10ms → `<10ms`
- etc.

Usage:
    uv run tooling/fix_mdx_syntax.py [--dry-run]
"""

import argparse
import re
from pathlib import Path


def fix_mdx_issues(content: str) -> tuple[str, list[str]]:
    """Fix MDX syntax issues in content."""
    changes = []

    # Pattern: < followed by number (not already in backticks or code blocks)
    # Match patterns like "<10ms", "<1 minute", etc.
    # But NOT inside code blocks or already backticked

    lines = content.split("\n")
    fixed_lines = []
    in_code_block = False

    for i, line in enumerate(lines, 1):
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            fixed_lines.append(line)
            continue

        if in_code_block:
            fixed_lines.append(line)
            continue

        # Skip if line is already in inline code
        if "`" in line and "<" in line:
            # Complex case - need to check if < is inside backticks
            # For simplicity, skip lines with both backticks and <
            # (most likely already correct)
            parts = line.split("`")
            if len(parts) > 2:  # Has inline code
                # Check if < is outside backticks
                has_unquoted_less = False
                for j in range(0, len(parts), 2):  # Even indices are outside backticks
                    if "<" in parts[j]:
                        has_unquoted_less = True
                        break

                if not has_unquoted_less:
                    fixed_lines.append(line)
                    continue

        # Find <digit patterns not in backticks
        pattern = r"(?<!`)<(\d+(?:\.\d+)?(?:ms|min|s|%|MB|GB|KB)?(?:\s+\w+)?)"

        def replace_fn(match, line_num=i):
            full_match = match.group(0)
            inner = match.group(1)
            replacement = f"`<{inner}`"
            changes.append(f"Line {line_num}: '{full_match}' → '{replacement}'")
            return replacement

        fixed_line = re.sub(pattern, replace_fn, line)
        fixed_lines.append(fixed_line)

    return "\n".join(fixed_lines), changes


def process_file(file_path: Path, dry_run: bool = False) -> bool:
    """Process a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        fixed_content, changes = fix_mdx_issues(content)

        if changes:
            print(f"\n📄 {file_path.relative_to(Path.cwd())}")
            for change in changes:
                print(f"   {change}")

            if not dry_run:
                file_path.write_text(fixed_content, encoding="utf-8")
                print(f"   ✓ Fixed {len(changes)} issues")
            else:
                print(f"   (dry-run: would fix {len(changes)} issues)")

            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix MDX syntax issues in markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview changes
    uv run tooling/fix_mdx_syntax.py --dry-run

    # Apply fixes
    uv run tooling/fix_mdx_syntax.py
        """,
    )

    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    docs_cms = repo_root / "docs-cms"

    if not docs_cms.exists():
        print(f"Error: docs-cms directory not found at {docs_cms}")
        return 1

    print("🔍 Scanning for MDX syntax issues...")

    # Find all markdown files
    md_files = list(docs_cms.rglob("*.md"))

    print(f"   Found {len(md_files)} markdown files")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - no files will be modified\n")

    files_changed = 0

    for md_file in md_files:
        if process_file(md_file, dry_run=args.dry_run):
            files_changed += 1

    print(f"\n{'Would change' if args.dry_run else 'Changed'} {files_changed} files")

    if args.dry_run and files_changed > 0:
        print("\nRun without --dry-run to apply changes")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
