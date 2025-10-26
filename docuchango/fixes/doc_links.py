#!/usr/bin/env python3
"""Fix documentation links to use Docusaurus absolute paths with lowercase IDs.

Converts:
  - ./ADR-XXX-name.md → /adr/adr-XXX
  - ../adr/ADR-XXX-name.md → /adr/adr-XXX
  - /adr/ADR-XXX → /adr/adr-XXX
  - ./RFC-XXX-name.md → /rfc/rfc-XXX
  - /rfc/RFC-XXX → /rfc/rfc-XXX
  - ./MEMO-XXX-name.md → /memos/memo-XXX
  - /memos/MEMO-XXX → /memos/memo-XXX

Docusaurus generates lowercase URLs from frontmatter IDs:
  - id: adr-001 → /adr/adr-001
  - id: rfc-001 → /rfc/rfc-001
  - id: memo-001 → /memos/memo-001

Usage:
    uv run tooling/fix_doc_links.py
"""

import re
import sys
from pathlib import Path


def fix_links_in_file(file_path: Path) -> tuple[int, int]:
    """Fix links in a single file.
    Returns (relative_links_fixed, case_fixes_made).
    """
    content = file_path.read_text()
    original = content

    relative_count = 0
    case_count = 0

    # Fix relative markdown links (./FILE.md or ../path/FILE.md)
    # ADR: ./ADR-XXX-anything.md → /adr/adr-XXX
    def fix_relative_adr(match):
        nonlocal relative_count
        relative_count += 1
        num = match.group(1)
        return f"](/adr/adr-{num})"

    content = re.sub(r"\]\(\.\.?/(?:adr/)?ADR-(\d+)[^)]*\.md\)", fix_relative_adr, content)

    # RFC: ./RFC-XXX-anything.md → /rfc/rfc-XXX
    def fix_relative_rfc(match):
        nonlocal relative_count
        relative_count += 1
        num = match.group(1)
        return f"](/rfc/rfc-{num})"

    content = re.sub(r"\]\(\.\.?/(?:rfcs?/)?RFC-(\d+)[^)]*\.md\)", fix_relative_rfc, content)

    # MEMO: ./MEMO-XXX-anything.md → /memos/memo-XXX
    def fix_relative_memo(match):
        nonlocal relative_count
        relative_count += 1
        num = match.group(1)
        return f"](/memos/memo-{num})"

    content = re.sub(r"\]\(\.\.?/(?:memos/)?MEMO-(\d+)[^)]*\.md\)", fix_relative_memo, content)

    # Fix case in existing absolute links
    # /adr/ADR-XXX → /adr/adr-XXX
    def fix_case_adr(match):
        nonlocal case_count
        case_count += 1
        return f"/adr/adr-{match.group(1)}"

    content = re.sub(r"/adr/ADR-(\d+)", fix_case_adr, content)

    # /rfc/RFC-XXX → /rfc/rfc-XXX
    def fix_case_rfc(match):
        nonlocal case_count
        case_count += 1
        return f"/rfc/rfc-{match.group(1)}"

    content = re.sub(r"/rfc/RFC-(\d+)", fix_case_rfc, content)

    # /memos/MEMO-XXX → /memos/memo-XXX
    def fix_case_memo(match):
        nonlocal case_count
        case_count += 1
        return f"/memos/memo-{match.group(1)}"

    content = re.sub(r"/memos/MEMO-(\d+)", fix_case_memo, content)

    if content != original:
        file_path.write_text(content)

    return (relative_count, case_count)


def main():
    """Fix all markdown files in docs-cms/"""
    docs_root = Path(__file__).parent.parent / "docs-cms"

    if not docs_root.exists():
        print(f"❌ Error: {docs_root} not found")
        print("   Run this script from the repository root")
        return 1

    total_files = 0
    total_relative = 0
    total_case = 0

    # Find all markdown files
    for md_file in docs_root.rglob("*.md"):
        # Skip template files
        if "template" in md_file.name.lower():
            continue

        relative_fixes, case_fixes = fix_links_in_file(md_file)
        if relative_fixes > 0 or case_fixes > 0:
            total_files += 1
            total_relative += relative_fixes
            total_case += case_fixes
            rel_msg = f"{relative_fixes} relative" if relative_fixes else ""
            case_msg = f"{case_fixes} case" if case_fixes else ""
            sep = ", " if rel_msg and case_msg else ""
            print(f"✓ Fixed {rel_msg}{sep}{case_msg} in {md_file.relative_to(docs_root)}")

    print("\n✅ Summary:")
    print(f"   - Fixed {total_relative} relative markdown links (./FILE.md → /path/file)")
    print(f"   - Fixed {total_case} uppercase IDs (/path/FILE-XXX → /path/file-XXX)")
    print(f"   - Modified {total_files} files")

    if total_files > 0:
        print("\nNext steps:")
        print("1. Review changes: git diff docs-cms/")
        print("2. Validate docs:   uv run tooling/validate_docs.py")
        print("3. Commit changes:  git add docs-cms/ && git commit")
    else:
        print("\n✅ All links already use correct Docusaurus format!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
