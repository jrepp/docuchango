#!/usr/bin/env python3
"""Fix code block formatting issues in markdown files.

Ensures:
1. Opening fences have language: ```language
2. Closing fences are bare: ```
3. All blocks are balanced
"""

import sys
from pathlib import Path


def fix_code_blocks(file_path: Path) -> tuple[int, str]:
    """Fix code blocks in a file."""
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    new_lines = []

    in_code_block = False
    opening_language = None
    fixes = 0
    changes = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code_block:
                # Opening fence
                language = stripped[3:].strip()
                if not language:
                    # Bare opening - add 'text' language
                    indent = line[: len(line) - len(line.lstrip())]
                    new_lines.append(f"{indent}```text")
                    changes.append(f"Line {i}: Added 'text' to bare opening fence")
                    fixes += 1
                    in_code_block = True
                    opening_language = "text"
                else:
                    # Valid opening
                    new_lines.append(line)
                    in_code_block = True
                    opening_language = language
            else:
                # Closing fence
                language = stripped[3:].strip()
                if language:
                    # Closing fence has language - remove it
                    indent = line[: len(line) - len(line.lstrip())]
                    new_lines.append(f"{indent}```")
                    changes.append(f"Line {i}: Removed '{language}' from closing fence")
                    fixes += 1
                else:
                    # Valid closing
                    new_lines.append(line)

                in_code_block = False
                opening_language = None
        else:
            new_lines.append(line)

    # Check for unclosed block
    if in_code_block:
        # Add closing fence
        new_lines.append("```")
        changes.append(f"End of file: Added missing closing fence for ```{opening_language}")
        fixes += 1

    if fixes > 0:
        file_path.write_text("\n".join(new_lines), encoding="utf-8")
        return fixes, "\n".join(changes)

    return 0, ""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_code_blocks_proper.py <file1.md> <file2.md> ...")
        sys.exit(1)

    total_fixes = 0
    files_fixed = 0

    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)
        if not file_path.exists():
            print(f"✗ File not found: {file_path}")
            continue

        fixes, changes = fix_code_blocks(file_path)
        if fixes > 0:
            print(f"✓ Fixed {fixes} code blocks in {file_path.name}")
            for change in changes.split("\n"):
                print(f"  {change}")
            total_fixes += fixes
            files_fixed += 1

    print(f"\n✅ Fixed {total_fixes} code blocks across {files_fixed} files")


if __name__ == "__main__":
    main()
