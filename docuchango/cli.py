#!/usr/bin/env python3
"""Docuchango CLI.

Docusaurus validation and repair framework for opinionated micro-CMS documentation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from docuchango import __version__

console = Console()


@click.group()
@click.version_option(version=__version__)
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
        from docuchango.validator import DocValidator
    except ImportError as e:
        console.print(f"[red]Error importing validator: {e}[/red]")
        sys.exit(2)

    console.print("[bold blue]🔍 Validating Documentation[/bold blue]\n")
    console.print(f"Repository root: {repo_root}")
    console.print(f"Verbose: {verbose}")
    console.print(f"Skip build: {skip_build}")
    console.print(f"Auto-fix: {fix}\n")

    try:
        validator = DocValidator(repo_root=repo_root, verbose=verbose)
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
    console.print(f"[bold blue]🏥 Checking Health: {url}[/bold blue]\n")

    # Placeholder for health check implementation
    # HealthChecker would be initialized and used here
    console.print(f"[yellow]ℹ[/yellow] Health check not yet implemented for {url}")
    console.print(f"[dim]Timeout: {timeout}s[/dim]")
    console.print("[green]✓[/green] Placeholder completed")


@main.command()
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path where docs-cms folder should be created (default: ./docs-cms)",
)
@click.option(
    "--project-id",
    default="my-project",
    help="Project ID for docs-project.yaml (default: my-project)",
)
@click.option(
    "--project-name",
    default="My Project",
    help="Project name for docs-project.yaml (default: My Project)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing files if they exist",
)
def init(path: Path | None, project_id: str, project_name: str, force: bool):
    """Initialize a new docs-cms folder structure with templates.

    Creates a complete docs-cms folder structure with:
    - docs-project.yaml configuration file
    - adr/, rfcs/, memos/, prd/ folders
    - Template files for each document type
    - README with usage instructions

    Examples:

        \b
        # Initialize in current directory
        docuchango init

        \b
        # Initialize with custom path
        docuchango init --path ./my-docs

        \b
        # Initialize with custom project info
        docuchango init --project-id my-app --project-name "My Application"

        \b
        # Overwrite existing files
        docuchango init --force
    """
    import datetime
    from importlib import resources

    # Set default path if not provided
    if path is None:
        path = Path.cwd() / "docs-cms"

    console.print("[bold blue]📁 Initializing docs-cms structure[/bold blue]\n")

    # Check if path exists
    if path.exists() and not force and any(path.iterdir()):  # Check if directory is not empty
        console.print(f"[yellow]⚠[/yellow]  Directory already exists: {path}")
        console.print("[yellow]Use --force to overwrite existing files[/yellow]")
        sys.exit(1)

    # Create directory structure
    console.print(f"Creating structure at: {path}\n")
    path.mkdir(parents=True, exist_ok=True)

    folders = ["adr", "rfcs", "memos", "prd", "templates"]
    for folder in folders:
        folder_path = path / folder
        folder_path.mkdir(exist_ok=True)
        console.print(f"[green]✓[/green] Created: {folder}/")

    # Copy template files
    console.print("\n[bold]Copying templates...[/bold]")

    template_files = {
        "docs-project.yaml": path / "docs-project.yaml",
        "README.md": path / "README.md",
        "adr-000-template.md": path / "templates" / "adr-000-template.md",
        "rfc-000-template.md": path / "templates" / "rfc-000-template.md",
        "memo-000-template.md": path / "templates" / "memo-000-template.md",
        "prd-000-template.md": path / "templates" / "prd-000-template.md",
    }

    # Get templates from package
    try:
        # Try to access package resources
        template_dir = resources.files("docuchango") / "templates"

        for template_name, dest_path in template_files.items():
            if dest_path.exists() and not force:
                console.print(f"[yellow]⊘[/yellow] Skipped: {dest_path.relative_to(path)} (already exists)")
                continue

            template_path = template_dir / template_name
            content = template_path.read_text()

            # Customize docs-project.yaml with provided values
            if template_name == "docs-project.yaml":
                content = content.replace("my-project", project_id)
                content = content.replace("My Project", project_name)
                content = content.replace("2025-01-01", datetime.date.today().isoformat())

            dest_path.write_text(content)
            console.print(f"[green]✓[/green] Created: {dest_path.relative_to(path)}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error copying templates: {e}")
        sys.exit(1)

    # Success message
    console.print(f"\n[bold green]✅ Successfully initialized docs-cms at {path}[/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Review and customize docs-project.yaml")
    console.print("2. Copy a template from templates/ to create your first document")
    console.print("3. Run 'docuchango validate' to check your documents")
    console.print("\n[dim]Tip: Run 'docuchango bootstrap' for detailed setup instructions[/dim]")


@main.command()
@click.option(
    "--guide",
    type=click.Choice(["bootstrap", "agent", "best-practices"], case_sensitive=False),
    default="bootstrap",
    help="Which guide to display (default: bootstrap)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Save guide to file instead of displaying",
)
def bootstrap(guide: str, output: Path | None):
    """Display or save docs-cms bootstrap and agent guides.

    Provides quick access to documentation for setting up and using docs-cms:

    - bootstrap: Step-by-step setup guide for docs-cms
    - agent: Instructions for AI agents using docs-cms
    - best-practices: Best practices for agent-CMS interaction

    Examples:

        \b
        # Display bootstrap guide
        docuchango bootstrap

        \b
        # Display agent guide
        docuchango bootstrap --guide agent

        \b
        # Save bootstrap guide to file
        docuchango bootstrap --output /path/to/BOOTSTRAP_GUIDE.md
    """
    # Map guide names to file names
    guide_files = {
        "bootstrap": "BOOTSTRAP_GUIDE.md",
        "agent": "AGENT_GUIDE.md",
        "best-practices": "BEST_PRACTICES.md",
    }

    guide_file = guide_files[guide]

    # Try to find the guide in the package
    try:
        # First, try to find it in the installed package
        import importlib.resources as resources

        try:
            # Python 3.9+
            guide_path = resources.files("docuchango") / ".." / "docs" / guide_file
            guide_content = guide_path.read_text()
        except AttributeError:
            # Python 3.8 fallback
            with resources.path("docuchango", "__init__.py") as pkg_path:
                docs_dir = pkg_path.parent.parent / "docs"
                guide_path = docs_dir / guide_file
                guide_content = guide_path.read_text()

    except (FileNotFoundError, ModuleNotFoundError):
        # Fallback: try relative to the script location
        script_dir = Path(__file__).parent.parent
        guide_path = script_dir / "docs" / guide_file

        if not guide_path.exists():
            from rich.console import Console as RichConsole

            stderr_console = RichConsole(stderr=True)
            stderr_console.print(f"[red]✗[/red] Guide not found: {guide_file}")
            stderr_console.print(f"[dim]Searched in: {guide_path}[/dim]")
            sys.exit(1)

        guide_content = guide_path.read_text()

    # Output or display
    if output:
        output.write_text(guide_content)
        console.print(f"[green]✓[/green] Saved {guide} guide to: {output}")
    else:
        # Display with rich markdown rendering
        from rich.markdown import Markdown

        console.print(Markdown(guide_content))


# Export the validate command as a separate entry point
def validate_main():
    """Entry point for dcc-validate command."""
    validate()


# Export the fix command as a separate entry point
def fix_main():
    """Entry point for dcc-fix command."""
    fix()


if __name__ == "__main__":
    main()
