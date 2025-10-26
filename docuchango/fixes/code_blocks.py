#!/usr/bin/env python3
"""Auto-fix code block formatting issues

Fixes:
1. Missing blank lines before opening code fences
2. Missing blank lines after closing code fences
3. Closing fences with extra text (```bash -> ```)
4. Opening fences without language (``` -> ```text)
5. Unclosed code blocks

Usage:
    uv run python -m tooling.fix_code_blocks
"""

import re
import sys
from pathlib import Path


def fix_code_blocks(file_path: Path) -> tuple[bool, list[str]]:
    """Fix code block issues in a file"""
    changes = []

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        fixed_lines = []

        in_code_block = False
        in_frontmatter = False
        frontmatter_count = 0
        frontmatter_end_line = None
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Track frontmatter
            if stripped == "---":
                frontmatter_count += 1
                if frontmatter_count == 1:
                    in_frontmatter = True
                elif frontmatter_count == 2:
                    in_frontmatter = False
                    frontmatter_end_line = i
                fixed_lines.append(line)
                i += 1
                continue

            # Skip frontmatter content
            if in_frontmatter:
                fixed_lines.append(line)
                i += 1
                continue

            # Check for code fence (match beginning of stripped line)
            fence_match = re.match(r"^(`{3,})(.*)$", stripped)
            if fence_match:
                fence_backticks = fence_match.group(1)
                remainder = fence_match.group(2).strip()

                if not in_code_block:
                    # Opening fence
                    content_start = (frontmatter_end_line + 1) if frontmatter_end_line is not None else 0
                    is_after_frontmatter = frontmatter_end_line is not None and i == frontmatter_end_line + 1
                    is_document_start = i == content_start

                    # Check if previous line was blank
                    previous_line_blank = len(fixed_lines) == 0 or not fixed_lines[-1].strip()

                    # Add blank line before if needed
                    if not previous_line_blank and not is_after_frontmatter and not is_document_start:
                        fixed_lines.append("")
                        changes.append(f"Line {i + 1}: Added blank line before opening fence")

                    # Check if language is missing
                    if not remainder:
                        fixed_lines.append(f"{fence_backticks}text")
                        changes.append(f"Line {i + 1}: Added 'text' language to bare opening fence")
                    else:
                        fixed_lines.append(line)

                    in_code_block = True
                else:
                    # Closing fence
                    if remainder:
                        # Remove extra text from closing fence
                        fixed_lines.append(fence_backticks)
                        changes.append(f"Line {i + 1}: Removed extra text from closing fence (```{remainder} -> ```)")
                    else:
                        fixed_lines.append(line)

                    in_code_block = False

                    # Check next line for blank line requirement
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line:  # Next line has content
                            # Insert blank line after closing fence
                            i += 1  # Move to next line
                            fixed_lines.append("")  # Add blank line
                            changes.append(f"Line {i}: Added blank line after closing fence")
                            continue  # Will process next line in next iteration
            else:
                # Regular line (not a code fence)
                if not in_code_block:
                    fixed_lines.append(line)
                else:
                    # Inside code block - preserve exactly
                    fixed_lines.append(line)

            i += 1

        # Check for unclosed code block
        if in_code_block:
            fixed_lines.append("```")
            changes.append("End of file: Added closing fence for unclosed code block")

        # Write back if changes were made
        if changes:
            new_content = "\n".join(fixed_lines)
            file_path.write_text(new_content, encoding="utf-8")
            return True, changes

        return False, []

    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False, []


def main():
    repo_root = Path(__file__).parent.parent
    docs_cms = repo_root / "docs-cms"

    print("🔧 Auto-fixing code block issues...\n")

    total_files = 0
    fixed_files = 0
    total_changes = 0

    # Process all markdown files
    for md_file in docs_cms.rglob("*.md"):
        # Skip README and index files
        if md_file.name in ["README.md", "index.md"]:
            continue

        total_files += 1
        modified, changes = fix_code_blocks(md_file)

        if modified:
            fixed_files += 1
            total_changes += len(changes)
            print(f"✓ {md_file.relative_to(repo_root)}")
            for change in changes:
                print(f"  • {change}")
            print()

    print(f"\n{'=' * 80}")
    print("📊 Summary:")
    print(f"   Files scanned: {total_files}")
    print(f"   Files fixed: {fixed_files}")
    print(f"   Total changes: {total_changes}")
    print(f"{'=' * 80}\n")

    if fixed_files > 0:
        print("✅ Fixes applied! Run validation again to verify.")
    else:
        print("✅ No fixes needed.")


if __name__ == "__main__":
    main()
