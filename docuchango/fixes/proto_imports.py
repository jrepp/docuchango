#!/usr/bin/env -S uv run python3
"""Proto Import Path Fixer

Fixes generated protobuf imports to use official google.golang.org packages
instead of locally generated ones.

Usage:
    uv run python -m tooling.fix_proto_imports
    uv run tooling/fix_proto_imports.py
    ./tooling/fix_proto_imports.py

Exit Codes:
    0 - Successfully fixed imports
    1 - Error occurred
"""

import re
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError as e:
    print("\n❌ Missing dependencies. Run: uv sync", file=sys.stderr)
    print(f"   Error: {e}\n", file=sys.stderr)
    sys.exit(1)

console = Console()


class ProtoImportFixer:
    """Fixes proto import paths in generated .pb.go files."""

    # Import replacements to apply
    REPLACEMENTS = [
        (
            r"github\.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api",
            "google.golang.org/genproto/googleapis/api",
        ),
        (
            r"github\.com/hashicorp/cloud-agf-devportal/proto-public/go/google/rpc",
            "google.golang.org/genproto/googleapis/rpc",
        ),
        (
            r"github\.com/hashicorp/cloud-agf-devportal/proto-public/go/buf/validate",
            "buf.build/gen/go/bufbuild/protovalidate/protocolbuffers/go/buf/validate",
        ),
    ]

    def __init__(self, proto_dir: Path = None):
        self.proto_dir = proto_dir or Path("proto-public/go")
        self.hashicorp_dir = self.proto_dir / "hashicorp"

    def find_pb_files(self) -> list[Path]:
        """Find all .pb.go files in the hashicorp directory."""
        if not self.hashicorp_dir.exists():
            console.print(
                f"⚠️  Directory not found: {self.hashicorp_dir}",
                style="bold yellow",
            )
            return []

        return list(self.hashicorp_dir.rglob("*.pb.go"))

    def fix_file(self, file_path: Path) -> tuple[bool, int]:
        """
        Fix imports in a single file.

        Returns:
            (modified, num_replacements)
        """
        try:
            content = file_path.read_text()
            original_content = content
            replacement_count = 0

            for pattern, replacement in self.REPLACEMENTS:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    replacement_count += count

            if content != original_content:
                file_path.write_text(content)
                return True, replacement_count

            return False, 0

        except Exception as e:
            console.print(f"❌ Error fixing {file_path}: {e}", style="bold red")
            return False, 0

    def fix_all(self) -> int:
        """
        Fix imports in all .pb.go files.

        Returns:
            Number of files modified
        """
        console.print("🔧 Fixing proto import paths...", style="bold blue")

        files = self.find_pb_files()
        if not files:
            console.print("⚠️  No .pb.go files found", style="bold yellow")
            return 0

        modified_count = 0
        total_replacements = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Processing {len(files)} files...", total=len(files))

            for file_path in files:
                modified, replacements = self.fix_file(file_path)
                if modified:
                    modified_count += 1
                    total_replacements += replacements
                progress.advance(task)

        console.print("✅ Proto import paths fixed", style="bold green")
        console.print(
            f"📊 Fixed imports in {modified_count} file(s) ({total_replacements} total replacements)",
            style="bold cyan",
        )

        return modified_count


def main():
    """Main entry point."""
    fixer = ProtoImportFixer()
    modified_count = fixer.fix_all()
    return 0 if modified_count >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
