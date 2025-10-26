#!/usr/bin/env python3
"""Fix MDX code blocks without language specifiers.

MDX tries to parse unlabeled code blocks as JavaScript, which fails.
This script adds 'text' language to all unlabeled code blocks.

Usage:
    python3 tooling/fix_mdx_code_blocks.py
"""

from pathlib import Path


def fix_code_blocks(file_path: Path) -> tuple[int, str]:
    """Fix unlabeled code blocks in a file."""
    content = file_path.read_text()
    original_content = content

    # Track changes
    changes_made = []

    # Pattern to find unlabeled code blocks: ``` at start of line (not followed by a language)
    # We need to be careful not to match closing ```
    lines = content.split("\n")
    new_lines = []
    in_code_block = False
    fixes = 0

    for i, line in enumerate(lines):
        # Check if this is a code fence
        if line.strip().startswith("```"):
            code_fence = line.strip()

            if not in_code_block:
                # Opening fence
                if code_fence == "```":
                    # Unlabeled! Fix it
                    # Determine indentation
                    indent = line[: len(line) - len(line.lstrip())]
                    new_lines.append(f"{indent}```text")
                    fixes += 1
                    in_code_block = True
                    changes_made.append(f"Line {i + 1}: Added 'text' language")
                else:
                    # Has a language, keep as is
                    new_lines.append(line)
                    in_code_block = True
            else:
                # Closing fence
                new_lines.append(line)
                in_code_block = False
        else:
            new_lines.append(line)

    new_content = "\n".join(new_lines)

    if new_content != original_content:
        file_path.write_text(new_content)
        return fixes, "\n".join(changes_made)

    return 0, ""


def main():
    """Fix all MEMO, ADR, RFC, and Netflix docs."""
    docs_cms = Path(__file__).parent.parent / "docs-cms"

    directories = ["memos", "adr", "rfcs", "netflix"]
    total_fixed = 0
    total_files = 0

    for directory in directories:
        dir_path = docs_cms / directory
        if not dir_path.exists():
            continue

        for md_file in dir_path.glob("*.md"):
            if md_file.name in ["index.md", "000-template.md", "README.md"]:
                continue

            fixes, changes = fix_code_blocks(md_file)
            if fixes > 0:
                print(f"✓ Fixed {fixes} code blocks in {md_file.relative_to(docs_cms)}")
                if changes:
                    for change in changes.split("\n"):
                        print(f"  {change}")
                total_fixed += fixes
                total_files += 1

    print(f"\n✅ Fixed {total_fixed} code blocks across {total_files} files")


if __name__ == "__main__":
    main()
