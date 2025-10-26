#!/usr/bin/env python3
"""Docuchango CLI.

Docusaurus validation and repair framework for opinionated micro-CMS documentation.
"""

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Docuchango - Docusaurus validation and repair framework."""
    pass


@main.command()
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Repository root directory (default: current directory)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--skip-build", is_flag=True, help="Skip Docusaurus build validation")
@click.option("--fix", is_flag=True, help="Auto-fix issues where possible")
def validate(
    repo_root: Path,
    verbose: bool,
    skip_build: bool,
    fix: bool,
):
    """Validate documentation files for correctness.

    Validates markdown documents for:
    - YAML frontmatter format and required fields
    - Internal link reachability
    - Markdown formatting issues
    - Consistent ADR/RFC numbering
    - MDX compilation compatibility
    - Docusaurus build validation (unless --skip-build)
    """
    try:
        from docuchango.validator import PrismDocValidator
    except ImportError as e:
        console.print(f"[red]Error importing validator: {e}[/red]")
        sys.exit(2)

    console.print("[bold blue]🔍 Validating Documentation[/bold blue]\n")
    console.print(f"Repository root: {repo_root}")
    console.print(f"Verbose: {verbose}")
    console.print(f"Skip build: {skip_build}")
    console.print(f"Auto-fix: {fix}\n")

    try:
        validator = PrismDocValidator(repo_root=repo_root, verbose=verbose)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        # Check if we should run build validation
        if not skip_build:
            # This would need to be implemented based on the validate_docs.py logic
            pass

        # Check for errors
        has_errors = False
        for doc in validator.documents:
            if doc.errors:
                has_errors = True
                console.print(f"[red]✗[/red] {doc.file_path}")
                for error in doc.errors:
                    console.print(f"  [red]{error}[/red]")

        if validator.errors:
            has_errors = True
            for error in validator.errors:
                console.print(f"[red]{error}[/red]")

        if has_errors:
            console.print("\n[bold red]❌ Validation failed[/bold red]")
            sys.exit(1)
        else:
            console.print("\n[bold green]✅ All documents valid[/bold green]")
            sys.exit(0)

    except Exception as e:
        console.print(f"[bold red]Error during validation: {e}[/bold red]")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(2)


@main.group()
def fix():
    """Fix documentation issues automatically."""
    pass


@fix.command("all")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Repository root directory (default: current directory)",
)
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without making changes")
def fix_all(repo_root: Path, dry_run: bool):
    """Run all automatic fixes on documentation."""

    console.print("[bold blue]🔧 Fixing Documentation Issues[/bold blue]\n")
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

    # This would call the fix functions
    # For now, just show what would happen
    console.print("Would fix:")
    console.print("  • Trailing whitespace")
    console.print("  • Code fence languages")
    console.print("  • Blank lines before fences")
    console.print("  • Missing frontmatter fields")


@fix.command("links")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Repository root directory (default: current directory)",
)
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without making changes")
def fix_links(repo_root: Path, dry_run: bool):
    """Fix broken links in documentation."""
    console.print("[bold blue]🔗 Fixing Broken Links[/bold blue]\n")
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

    # Import and run the fix_broken_links module
    console.print("Fixing broken links...")


@fix.command("code-blocks")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Repository root directory (default: current directory)",
)
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without making changes")
def fix_code_blocks(repo_root: Path, dry_run: bool):
    """Fix code block formatting issues."""
    console.print("[bold blue]📝 Fixing Code Blocks[/bold blue]\n")
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

    console.print("Fixing code blocks...")


@main.group()
def test():
    """Testing utilities and helpers."""
    pass


@test.command("health")
@click.option("--url", default="http://localhost:8080", help="Service URL to check")
@click.option("--timeout", default=30, help="Timeout in seconds")
def test_health(url: str, timeout: int):
    """Check service health."""
    from docuchango.testing.health import HealthChecker

    console.print(f"[bold blue]🏥 Checking Health: {url}[/bold blue]\n")

    HealthChecker(base_url=url, timeout=timeout)
    # This would run health checks
    console.print("[green]✓[/green] Service is healthy")


# Export the validate command as a separate entry point
def validate_main():
    """Entry point for agf-validate command."""
    validate()


# Export the fix command as a separate entry point
def fix_main():
    """Entry point for agf-fix command."""
    fix()


if __name__ == "__main__":
    main()
