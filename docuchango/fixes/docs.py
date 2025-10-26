#!/usr/bin/env -S uv run python3
"""Fix documentation validation issues automatically."""

import sys
import uuid
from pathlib import Path

try:
    from rich.console import Console
except ImportError as e:
    print(f"❌ Missing dependency: {e}", file=sys.stderr)
    print("Run: uv sync", file=sys.stderr)
    sys.exit(2)

console = Console()


def fix_trailing_whitespace(file_path: Path) -> int:
    """Remove trailing whitespace from a file."""
    content = file_path.read_text()
    lines = content.splitlines(keepends=True)
    fixed_lines = [line.rstrip() + ("\n" if line.endswith("\n") else "") for line in lines]

    # Count changes
    changes = sum(1 for old, new in zip(lines, fixed_lines) if old != new)

    if changes > 0:
        file_path.write_text("".join(fixed_lines))

    return changes


def fix_code_fence_languages(file_path: Path) -> int:
    """Add 'text' language to code fences missing language."""
    content = file_path.read_text()

    lines = content.splitlines(keepends=True)
    changes = 0
    in_code_block = False

    for i, line in enumerate(lines):
        stripped = line.rstrip()

        # Check if this is a code fence line
        if stripped.startswith("```"):
            if not in_code_block:
                # Opening fence
                if stripped == "```":
                    # No language specified, add 'text'
                    lines[i] = "```text\n" if line.endswith("\n") else "```text"
                    changes += 1
                in_code_block = True
            else:
                # Closing fence - should never have language
                if stripped != "```" and stripped.startswith("```"):
                    # Has extra text after closing fence (e.g., ```text)
                    lines[i] = "```\n" if line.endswith("\n") else "```"
                    changes += 1
                in_code_block = False

    if changes > 0:
        file_path.write_text("".join(lines))

    return changes


def fix_blank_lines_before_fences(file_path: Path) -> int:
    """Add blank line before code fences when missing."""
    content = file_path.read_text()
    lines = content.splitlines(keepends=True)

    new_lines = []
    changes = 0
    in_code_block = False

    for _i, line in enumerate(lines):
        stripped = line.strip()

        # Check if this line starts a code fence (opening fence only)
        if stripped.startswith("```") and not in_code_block:
            # Check if previous line is not blank and not closing frontmatter delimiter
            if new_lines and new_lines[-1].strip() != "" and new_lines[-1].strip() != "---":
                # Add blank line before fence
                new_lines.append("\n")
                changes += 1
            in_code_block = True
        elif stripped.startswith("```") and in_code_block:
            # Closing fence
            in_code_block = False

        new_lines.append(line)

    if changes > 0:
        file_path.write_text("".join(new_lines))

    return changes


def add_missing_frontmatter_fields(file_path: Path) -> int:
    """Add missing project_id and doc_uuid fields to frontmatter."""
    content = file_path.read_text()

    # Check if file has frontmatter
    if not content.startswith("---\n"):
        return 0

    # Extract frontmatter
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return 0

    frontmatter = parts[1]
    body = parts[2]

    changes = 0

    # Check if project_id is missing
    if "project_id:" not in frontmatter:
        frontmatter += 'project_id: "agf-devportal"\n'
        changes += 1

    # Check if doc_uuid is missing
    if "doc_uuid:" not in frontmatter:
        frontmatter += f'doc_uuid: "{uuid.uuid4()}"\n'
        changes += 1

    if changes > 0:
        new_content = f"---\n{frontmatter}---\n{body}"
        file_path.write_text(new_content)

    return changes


def main():
    """Fix all documentation issues."""
    console.print("[bold blue]🔧 Fixing Documentation Issues[/bold blue]\n")

    docs_dir = Path("/Users/jrepp/hc/cloud-agf-devportal/docs-cms")

    total_fixes = 0
    files_fixed = 0

    # Find all markdown files
    md_files = list(docs_dir.rglob("*.md"))

    console.print(f"Found {len(md_files)} markdown files\n")

    for md_file in md_files:
        file_fixes = 0

        # Fix trailing whitespace
        ws_fixes = fix_trailing_whitespace(md_file)
        if ws_fixes > 0:
            console.print(f"  ✓ Fixed {ws_fixes} trailing whitespace issues in {md_file.name}")
            file_fixes += ws_fixes

        # Fix code fence languages
        lang_fixes = fix_code_fence_languages(md_file)
        if lang_fixes > 0:
            console.print(f"  ✓ Added 'text' to {lang_fixes} code fences in {md_file.name}")
            file_fixes += lang_fixes

        # Fix blank lines before fences
        blank_fixes = fix_blank_lines_before_fences(md_file)
        if blank_fixes > 0:
            console.print(f"  ✓ Added {blank_fixes} blank lines before code fences in {md_file.name}")
            file_fixes += blank_fixes

        # Add missing frontmatter fields
        fm_fixes = add_missing_frontmatter_fields(md_file)
        if fm_fixes > 0:
            console.print(f"  ✓ Added {fm_fixes} frontmatter fields to {md_file.name}")
            file_fixes += fm_fixes

        if file_fixes > 0:
            files_fixed += 1
            total_fixes += file_fixes

    console.print(f"\n[bold green]✅ Fixed {total_fixes} issues in {files_fixed} files[/bold green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
