#!/usr/bin/env python3
"""
Fix PostgreSQL syntax in Goose migration files.

Converts inline INDEX declarations (MySQL style) to separate CREATE INDEX statements (PostgreSQL style).

Usage:
    uv run python -m tooling.fix_migration_syntax
"""

import re
import sys
from pathlib import Path


def fix_migration_file(filepath: Path) -> bool:
    """Fix PostgreSQL syntax issues in a migration file."""
    print(f"Processing: {filepath.name}")

    content = filepath.read_text()
    original_content = content

    # Find CREATE TABLE statements and extract inline INDEX declarations
    # Pattern: INDEX idx_name (column)
    def fix_create_table(match):
        table_sql = match.group(0)
        table_name_match = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", table_sql)
        if not table_name_match:
            return table_sql

        table_name = table_name_match.group(1)

        # Extract all INDEX declarations
        index_pattern = r",?\s*INDEX\s+(\w+)\s*\(([^)]+)\)"
        indexes = []

        def collect_index(idx_match):
            index_name = idx_match.group(1)
            columns = idx_match.group(2)
            indexes.append((index_name, columns))
            return ""  # Remove from table definition

        # Remove INDEX declarations from table
        table_sql_fixed = re.sub(index_pattern, collect_index, table_sql)

        # Clean up any trailing commas before closing paren or before comments
        table_sql_fixed = re.sub(r",\s*\n\s*--[^\n]*\n\s*\)", ")", table_sql_fixed)
        table_sql_fixed = re.sub(r",\s*\)", ")", table_sql_fixed)

        # Add CREATE INDEX statements after the table
        if indexes:
            index_statements = "\n\n".join(
                [f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({cols});" for idx_name, cols in indexes]
            )
            table_sql_fixed = table_sql_fixed + "\n\n" + index_statements

        return table_sql_fixed

    # Match CREATE TABLE statements (including multi-line)
    table_pattern = r"CREATE TABLE[^;]+;"
    content = re.sub(table_pattern, fix_create_table, content, flags=re.DOTALL | re.IGNORECASE)

    # Write back if changed
    if content != original_content:
        filepath.write_text(content)
        print(f"  ✓ Fixed {filepath.name}")
        return True
    print(f"  - No changes needed for {filepath.name}")
    return False


def main():
    """Fix all migration files."""
    migrations_dir = Path(__file__).parent.parent / "models" / "migrations"

    if not migrations_dir.exists():
        print(f"Error: Directory {migrations_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    migration_files = sorted(migrations_dir.glob("*.sql"))
    migration_files = [f for f in migration_files if f.name != ".gitkeep"]

    if not migration_files:
        print("No migration files found", file=sys.stderr)
        sys.exit(1)

    print(f"Fixing {len(migration_files)} migration files...\n")

    fixed_count = 0
    for filepath in migration_files:
        if fix_migration_file(filepath):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count}/{len(migration_files)} migration files")


if __name__ == "__main__":
    main()
