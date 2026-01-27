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
@click.option("--dry-run", is_flag=True, help="Report issues without applying fixes")
def validate(
    repo_root: Path,
    verbose: bool,
    skip_build: bool,
    dry_run: bool,
):
    """Validate and fix documentation files.

    By default, automatically fixes issues where possible. Use --dry-run to
    only report issues without making changes.

    Validates and fixes:
    - YAML frontmatter (status values, dates, missing fields)
    - Tags (normalize, deduplicate, sort)
    - Whitespace (trim values, remove empty fields)
    - Timestamps (created/updated from git history)
    - Code blocks (languages, blank lines, closing fences)
    - Internal link reachability
    - Markdown formatting issues
    - Consistent ADR/RFC numbering
    """
    from docuchango.fixes.code_blocks import fix_code_blocks
    from docuchango.fixes.frontmatter import fix_all_frontmatter
    from docuchango.fixes.tags import fix_tags
    from docuchango.fixes.timestamps import update_document_timestamps
    from docuchango.fixes.whitespace import fix_whitespace_and_fields

    try:
        from docuchango.validator import DocValidator
    except ImportError as e:
        console.print(f"[red]Error importing validator: {e}[/red]")
        sys.exit(2)

    console.print("[bold blue]🔍 Validating Documentation[/bold blue]\n")
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

    # Find all markdown files in docs directories
    # Check both repo root and docs-cms subdirectory for compatibility
    doc_patterns = [
        "adr/**/*.md",
        "rfcs/**/*.md",
        "memos/**/*.md",
        "prd/**/*.md",
        "docs-cms/adr/**/*.md",
        "docs-cms/rfcs/**/*.md",
        "docs-cms/memos/**/*.md",
        "docs-cms/prd/**/*.md",
    ]
    all_files = []
    for pattern in doc_patterns:
        all_files.extend(repo_root.glob(pattern))

    # Track fixes applied and remaining issues
    fixes_applied: list[tuple[Path, str]] = []
    remaining_issues: list[tuple[Path, str]] = []

    # Phase 1: Apply automatic fixes
    if all_files:
        # Define fix functions: (name, function, supports_dry_run)
        fix_types = [
            ("Frontmatter", fix_all_frontmatter, True),
            ("Tags", fix_tags, True),
            ("Whitespace", fix_whitespace_and_fields, True),
            ("Timestamps", update_document_timestamps, True),
            ("Code blocks", fix_code_blocks, False),
        ]

        for fix_name, fix_func, supports_dry_run_flag in fix_types:
            for file_path in all_files:
                try:
                    # Skip code blocks fix in dry_run mode since it doesn't support it
                    if not supports_dry_run_flag and dry_run:
                        continue

                    # Call the fix function
                    result = fix_func(file_path, dry_run=dry_run) if supports_dry_run_flag else fix_func(file_path)

                    # Handle different return types
                    if isinstance(result, list):
                        messages = result
                        changed = bool(messages)
                    else:
                        changed, messages = result

                    if changed and messages:
                        for msg in messages:
                            fixes_applied.append((file_path, f"[{fix_name}] {msg}"))

                except Exception as e:
                    if verbose:
                        rel_path = file_path.relative_to(repo_root)
                        console.print(f"  [red]✗[/red] {rel_path}: Error in {fix_name} - {e}")

    # Phase 2: Run validation to find remaining issues
    try:
        # Don't pass fix=True to validator since we already applied fixes above
        validator = DocValidator(repo_root=repo_root, verbose=verbose, fix=False)
        validator.scan_documents()
        validator.check_code_blocks()
        validator.check_formatting()

        # Check if we should run build validation
        if not skip_build:
            # This would need to be implemented based on the validate_docs.py logic
            pass

        # Collect remaining errors
        for doc in validator.documents:
            if doc.errors:
                for error in doc.errors:
                    remaining_issues.append((doc.file_path, error))

        for error in validator.errors:
            remaining_issues.append((repo_root, error))

    except Exception as e:
        console.print(f"[bold red]Error during validation: {e}[/bold red]")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(2)

    # Phase 3: Display results (simplified when no issues)
    if not fixes_applied and not remaining_issues:
        # Clean output when everything is valid
        console.print(f"Scanned {len(all_files)} files\n")
        console.print("[bold green]✅ All documents valid[/bold green]")
        sys.exit(0)

    # Show detailed output when there are fixes or issues
    files_with_fixes = len({f for f, _ in fixes_applied})
    files_with_issues = len({f for f, _ in remaining_issues})

    console.print(f"Scanned {len(all_files)} files\n")

    # Show fixes applied
    if fixes_applied:
        action = "would be applied" if dry_run else "applied"
        console.print(f"[bold green]✓ Fixes {action}: {len(fixes_applied)}[/bold green]")
        seen_files: set[Path] = set()
        for file_path, msg in fixes_applied:
            rel_path = file_path.relative_to(repo_root)
            if file_path not in seen_files:
                seen_files.add(file_path)
                console.print(f"  [cyan]{rel_path}[/cyan]")
            console.print(f"    • {msg}")
        console.print()

    # Show remaining issues
    if remaining_issues:
        console.print(f"[bold red]✗ Remaining issues: {len(remaining_issues)}[/bold red]")
        seen_files = set()
        for file_path, error in remaining_issues:
            try:
                rel_path = file_path.relative_to(repo_root)
            except ValueError:
                rel_path = file_path
            if file_path not in seen_files:
                seen_files.add(file_path)
                console.print(f"  [cyan]{rel_path}[/cyan]")
            console.print(f"    [red]• {error}[/red]")
        console.print()

    # Summary line
    summary_parts = []
    if files_with_fixes:
        summary_parts.append(f"{files_with_fixes} fixed")
    if files_with_issues:
        summary_parts.append(f"{files_with_issues} with issues")
    if summary_parts:
        console.print(f"[dim]{', '.join(summary_parts)}[/dim]\n")

    if dry_run and fixes_applied:
        console.print("[yellow]Run without --dry-run to apply fixes[/yellow]\n")

    if remaining_issues:
        console.print("[bold red]❌ Validation failed[/bold red]")
        sys.exit(1)
    else:
        console.print("[bold green]✅ All documents valid[/bold green]")
        sys.exit(0)


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
            # Use simultaneous replacement to prevent cascading replacement bugs
            if template_name == "docs-project.yaml":
                # Using a temporary unique marker approach to avoid collision
                markers = {
                    "my-project": "\x00PROJECT_ID\x00",
                    "My Project": "\x00PROJECT_NAME\x00",
                    "2025-01-01": "\x00DATE\x00",
                }

                # First pass: replace placeholders with unique markers
                for placeholder, marker in markers.items():
                    content = content.replace(placeholder, marker)

                # Second pass: replace markers with actual values
                content = content.replace(markers["my-project"], project_id)
                content = content.replace(markers["My Project"], project_name)
                content = content.replace(markers["2025-01-01"], datetime.date.today().isoformat())

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


# ==============================================================================
# Bulk command group
# ==============================================================================


@main.group()
def bulk():
    """Bulk operations on documentation frontmatter.

    Commands for updating frontmatter fields across multiple documents at once.
    """
    pass


@bulk.command("update")
@click.option(
    "--set",
    "set_field",
    metavar="FIELD=VALUE",
    help="Set field value (creates or updates)",
)
@click.option(
    "--add",
    "add_field",
    metavar="FIELD=VALUE",
    help="Add field only if it doesn't exist",
)
@click.option(
    "--remove",
    "remove_field",
    metavar="FIELD",
    help="Remove field from frontmatter",
)
@click.option(
    "--rename",
    "rename_field",
    metavar="OLD=NEW",
    help="Rename field (preserves value)",
)
@click.option(
    "--type",
    "doc_type",
    type=click.Choice(["adr", "rfc", "memo", "prd"]),
    help="Filter by document type",
)
@click.option(
    "--path",
    "target_path",
    type=click.Path(exists=True, path_type=Path),
    help="Target directory (default: current directory)",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def bulk_update(
    set_field: str | None,
    add_field: str | None,
    remove_field: str | None,
    rename_field: str | None,
    doc_type: str | None,
    target_path: Path | None,
    dry_run: bool,
    verbose: bool,
):
    """Bulk update frontmatter fields across documents.

    Perform bulk updates on YAML frontmatter fields. Exactly one operation
    must be specified per invocation.

    Examples:

        \b
        # Set status to 'Accepted' on all ADRs
        docuchango bulk update --set status=Accepted --type adr

        \b
        # Add project_id field only where missing
        docuchango bulk update --add project_id=my-project

        \b
        # Remove deprecated field from all docs
        docuchango bulk update --remove legacy_field

        \b
        # Rename field across all documents
        docuchango bulk update --rename old_name=new_name

        \b
        # Preview changes without applying
        docuchango bulk update --set status=Draft --dry-run
    """
    from docuchango.fixes.bulk_update import bulk_update_files

    # Validate exactly one operation
    ops = [set_field, add_field, remove_field, rename_field]
    ops_provided = [op for op in ops if op is not None]

    if len(ops_provided) == 0:
        console.print("[red]Error: Must specify one of --set, --add, --remove, or --rename[/red]")
        sys.exit(1)
    if len(ops_provided) > 1:
        console.print("[red]Error: Only one operation allowed per invocation[/red]")
        sys.exit(1)

    # Parse the operation
    if set_field:
        if "=" not in set_field:
            console.print("[red]Error: --set requires FIELD=VALUE format[/red]")
            sys.exit(1)
        field_name, value = set_field.split("=", 1)
        operation = "set"
    elif add_field:
        if "=" not in add_field:
            console.print("[red]Error: --add requires FIELD=VALUE format[/red]")
            sys.exit(1)
        field_name, value = add_field.split("=", 1)
        operation = "add"
    elif remove_field:
        field_name = remove_field
        value = None
        operation = "remove"
    elif rename_field:
        if "=" not in rename_field:
            console.print("[red]Error: --rename requires OLD=NEW format[/red]")
            sys.exit(1)
        field_name, value = rename_field.split("=", 1)
        operation = "rename"

    # Find files to process
    root = target_path or Path.cwd()

    # Build glob patterns based on doc_type filter
    if doc_type:
        type_dirs = {
            "adr": ["adr"],
            "rfc": ["rfcs"],
            "memo": ["memos"],
            "prd": ["prd"],
        }
        patterns = [f"{d}/**/*.md" for d in type_dirs[doc_type]]
        patterns += [f"docs-cms/{d}/**/*.md" for d in type_dirs[doc_type]]
    else:
        patterns = [
            "adr/**/*.md",
            "rfcs/**/*.md",
            "memos/**/*.md",
            "prd/**/*.md",
            "docs-cms/adr/**/*.md",
            "docs-cms/rfcs/**/*.md",
            "docs-cms/memos/**/*.md",
            "docs-cms/prd/**/*.md",
        ]

    all_files = []
    for pattern in patterns:
        all_files.extend(root.glob(pattern))

    if not all_files:
        console.print("[yellow]No files found matching criteria[/yellow]")
        sys.exit(0)

    # Run bulk update
    console.print(f"[bold blue]📝 Bulk {operation}[/bold blue]")
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
    console.print(f"Processing {len(all_files)} files...\n")

    results = bulk_update_files(all_files, field_name, value, operation, dry_run)

    # Display results
    modified_count = 0
    for file_path, changed, message in results:
        if changed or verbose:
            try:
                rel_path = file_path.relative_to(root)
            except ValueError:
                rel_path = file_path

            if changed:
                modified_count += 1
                console.print(f"[green]✓[/green] {rel_path}: {message}")
            elif verbose:
                console.print(f"[dim]⊘[/dim] {rel_path}: {message}")

    # Summary
    console.print()
    if dry_run:
        console.print(f"[yellow]Would modify {modified_count} of {len(all_files)} files[/yellow]")
        console.print("[dim]Run without --dry-run to apply changes[/dim]")
    else:
        console.print(f"[green]Modified {modified_count} of {len(all_files)} files[/green]")


@bulk.command("timestamps")
@click.option(
    "--type",
    "doc_type",
    type=click.Choice(["adr", "rfc", "memo", "prd"]),
    help="Filter by document type",
)
@click.option(
    "--path",
    "target_path",
    type=click.Path(exists=True, path_type=Path),
    help="Target directory (default: current directory)",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def bulk_timestamps(
    doc_type: str | None,
    target_path: Path | None,
    dry_run: bool,
    verbose: bool,
):
    """Derive created timestamp from git history.

    Updates frontmatter 'created' field based on git commit history.
    The 'created' date is set to the first commit datetime.

    Also migrates legacy 'date' fields to the new 'created' format.

    Note: The 'updated' field is not stored as it can be derived from git history.

    Examples:

        \b
        # Update timestamps for all documents
        docuchango bulk timestamps

        \b
        # Update only ADR timestamps
        docuchango bulk timestamps --type adr

        \b
        # Preview changes without applying
        docuchango bulk timestamps --dry-run

        \b
        # Show all files including unchanged
        docuchango bulk timestamps --verbose
    """
    from docuchango.fixes.timestamps import update_document_timestamps

    # Find files to process
    root = target_path or Path.cwd()

    # Build glob patterns based on doc_type filter
    if doc_type:
        type_dirs = {
            "adr": ["adr"],
            "rfc": ["rfcs"],
            "memo": ["memos"],
            "prd": ["prd"],
        }
        patterns = [f"{d}/**/*.md" for d in type_dirs[doc_type]]
        patterns += [f"docs-cms/{d}/**/*.md" for d in type_dirs[doc_type]]
    else:
        patterns = [
            "adr/**/*.md",
            "rfcs/**/*.md",
            "memos/**/*.md",
            "prd/**/*.md",
            "docs-cms/adr/**/*.md",
            "docs-cms/rfcs/**/*.md",
            "docs-cms/memos/**/*.md",
            "docs-cms/prd/**/*.md",
        ]

    all_files = []
    for pattern in patterns:
        all_files.extend(root.glob(pattern))

    if not all_files:
        console.print("[yellow]No files found matching criteria[/yellow]")
        sys.exit(0)

    # Run timestamp updates
    console.print("[bold blue]🕐 Updating timestamps from git history[/bold blue]")
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
    console.print(f"Processing {len(all_files)} files...\n")

    modified_count = 0
    error_count = 0

    for file_path in all_files:
        try:
            changed, messages = update_document_timestamps(file_path, dry_run=dry_run)

            try:
                rel_path = file_path.relative_to(root)
            except ValueError:
                rel_path = file_path

            if changed:
                modified_count += 1
                console.print(f"[green]✓[/green] {rel_path}")
                for msg in messages:
                    console.print(f"    {msg}")
            elif verbose:
                if messages:
                    console.print(f"[dim]⊘[/dim] {rel_path}: {messages[0]}")
                else:
                    console.print(f"[dim]⊘[/dim] {rel_path}: No changes needed")

        except Exception as e:
            error_count += 1
            try:
                rel_path = file_path.relative_to(root)
            except ValueError:
                rel_path = file_path
            console.print(f"[red]✗[/red] {rel_path}: {e}")

    # Summary
    console.print()
    if dry_run:
        console.print(f"[yellow]Would modify {modified_count} of {len(all_files)} files[/yellow]")
        if error_count:
            console.print(f"[red]Errors: {error_count}[/red]")
        console.print("[dim]Run without --dry-run to apply changes[/dim]")
    else:
        console.print(f"[green]Modified {modified_count} of {len(all_files)} files[/green]")
        if error_count:
            console.print(f"[red]Errors: {error_count}[/red]")


@main.command("migrate")
@click.option(
    "--project-id",
    required=True,
    help="Project ID to set for documents missing project_id",
)
@click.option(
    "--type",
    "doc_type",
    type=click.Choice(["adr", "rfc", "memo", "prd"]),
    help="Filter by document type",
)
@click.option(
    "--path",
    "target_path",
    type=click.Path(exists=True, path_type=Path),
    help="Target directory (default: current directory)",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def migrate(
    project_id: str,
    doc_type: str | None,
    target_path: Path | None,
    dry_run: bool,
    verbose: bool,
):
    """Migrate documents to the current frontmatter schema.

    Performs comprehensive migration of frontmatter fields:

    \b
    - Adds missing 'project_id' field
    - Generates 'doc_uuid' (UUID v4) if missing
    - Migrates legacy 'date' field to 'created'
    - Adds 'created' from git history if missing
    - Removes deprecated/derived fields ('updated', 'date')
    - Normalizes 'id' field to lowercase format
    - Normalizes tags to lowercase with hyphens

    Note: The 'updated' field is removed because it can be derived from
    git history. Use 'docuchango bulk timestamps' to compute it on demand.

    Examples:

        \b
        # Migrate all documents
        docuchango migrate --project-id my-project

        \b
        # Migrate only ADRs
        docuchango migrate --project-id my-project --type adr

        \b
        # Preview changes without applying
        docuchango migrate --project-id my-project --dry-run

    Agent instructions to generate required fields:

        \b
        # Generate created datetime (ISO 8601 UTC):
        python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
        # Or: date -u +%Y-%m-%dT%H:%M:%SZ

        \b
        # Generate doc_uuid:
        python -c "import uuid; print(uuid.uuid4())"
        # Or: uuidgen

        \b
        # Generate author from git config:
        git config user.name
    """
    import re
    import uuid

    import frontmatter

    from docuchango.fixes.timestamps import get_git_dates

    # Find files to process
    root = target_path or Path.cwd()

    # Build glob patterns based on doc_type filter
    if doc_type:
        type_dirs = {
            "adr": ["adr"],
            "rfc": ["rfcs"],
            "memo": ["memos"],
            "prd": ["prd"],
        }
        patterns = [f"{d}/**/*.md" for d in type_dirs[doc_type]]
        patterns += [f"docs-cms/{d}/**/*.md" for d in type_dirs[doc_type]]
    else:
        patterns = [
            "adr/**/*.md",
            "rfcs/**/*.md",
            "memos/**/*.md",
            "prd/**/*.md",
            "docs-cms/adr/**/*.md",
            "docs-cms/rfcs/**/*.md",
            "docs-cms/memos/**/*.md",
            "docs-cms/prd/**/*.md",
        ]

    all_files = []
    for pattern in patterns:
        all_files.extend(root.glob(pattern))

    if not all_files:
        console.print("[yellow]No files found matching criteria[/yellow]")
        sys.exit(0)

    # Run migration
    console.print("[bold blue]🔄 Migrating frontmatter to current schema[/bold blue]")
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
    console.print(f"Processing {len(all_files)} files...\n")

    modified_count = 0
    error_count = 0

    for file_path in all_files:
        # Skip templates
        if "template" in file_path.name.lower() or file_path.name.startswith("000-"):
            if verbose:
                try:
                    rel_path = file_path.relative_to(root)
                except ValueError:
                    rel_path = file_path
                console.print(f"[dim]⊘[/dim] {rel_path}: Skipped (template)")
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            post = frontmatter.loads(content)

            if not post.metadata:
                if verbose:
                    try:
                        rel_path = file_path.relative_to(root)
                    except ValueError:
                        rel_path = file_path
                    console.print(f"[dim]⊘[/dim] {rel_path}: No frontmatter")
                continue

            changes = []
            modified = False

            # Determine document type from path
            path_str = str(file_path).lower()
            if "/adr/" in path_str:
                doc_type_detected = "adr"
            elif "/rfcs/" in path_str:
                doc_type_detected = "rfc"
            elif "/memos/" in path_str:
                doc_type_detected = "memo"
            elif "/prd/" in path_str:
                doc_type_detected = "prd"
            else:
                doc_type_detected = None

            # 1. Add project_id if missing
            if "project_id" not in post.metadata:
                post.metadata["project_id"] = project_id
                changes.append(f"Added project_id: {project_id}")
                modified = True

            # 2. Generate doc_uuid if missing
            if "doc_uuid" not in post.metadata:
                new_uuid = str(uuid.uuid4())
                post.metadata["doc_uuid"] = new_uuid
                changes.append(f"Generated doc_uuid: {new_uuid}")
                modified = True

            # 3. Remove legacy 'date' field (will get created from git)
            if "date" in post.metadata:
                del post.metadata["date"]
                changes.append("Removed deprecated 'date' field")
                modified = True
                # Also remove created if it exists so it gets refreshed from git
                if "created" in post.metadata:
                    del post.metadata["created"]

            # 4. Add or update created from git (ensures datetime format)
            created_datetime, _ = get_git_dates(file_path)
            if created_datetime:
                old_created = post.metadata.get("created")
                # Normalize to datetime format from git
                if old_created != created_datetime:
                    old_val = str(old_created) if old_created else "None"
                    post.metadata["created"] = created_datetime
                    if old_created:
                        changes.append(f"Normalized created: {old_val} → {created_datetime}")
                    else:
                        changes.append(f"Added created: {created_datetime} (from git)")
                    modified = True

            # 5. Remove 'updated' field (derived from git history)
            if "updated" in post.metadata:
                del post.metadata["updated"]
                changes.append("Removed 'updated' field (derived from git)")
                modified = True

            # 6. Normalize id field to lowercase
            if "id" in post.metadata:
                old_id = post.metadata["id"]
                new_id = old_id.lower()
                if new_id != old_id:
                    post.metadata["id"] = new_id
                    changes.append(f"Normalized id: {old_id} → {new_id}")
                    modified = True
            elif doc_type_detected:
                # Generate id from filename
                # e.g., ADR-001-decision.md → adr-001
                filename = file_path.stem.lower()
                match = re.match(rf"({doc_type_detected})-(\d+)", filename)
                if match:
                    new_id = f"{match.group(1)}-{match.group(2).zfill(3)}"
                    post.metadata["id"] = new_id
                    changes.append(f"Generated id: {new_id}")
                    modified = True

            # 7. Normalize tags
            if "tags" in post.metadata:
                old_tags = post.metadata["tags"]
                if isinstance(old_tags, str):
                    # Convert string to list
                    old_tags = [t.strip() for t in old_tags.split(",")]
                if isinstance(old_tags, list):
                    new_tags = []
                    for tag in old_tags:
                        # Normalize: lowercase, replace spaces with hyphens
                        normalized = tag.lower().strip().replace(" ", "-")
                        # Remove non-alphanumeric except hyphens
                        normalized = re.sub(r"[^a-z0-9\-]", "", normalized)
                        if normalized:
                            new_tags.append(normalized)
                    new_tags = sorted(set(new_tags))
                    if new_tags != old_tags:
                        post.metadata["tags"] = new_tags
                        changes.append(f"Normalized tags: {old_tags} → {new_tags}")
                        modified = True

            # Write changes
            if modified and not dry_run:
                new_content = frontmatter.dumps(post)
                file_path.write_text(new_content, encoding="utf-8")

            # Report
            try:
                rel_path = file_path.relative_to(root)
            except ValueError:
                rel_path = file_path

            if modified:
                modified_count += 1
                console.print(f"[green]✓[/green] {rel_path}")
                for change in changes:
                    console.print(f"    {change}")
            elif verbose:
                console.print(f"[dim]⊘[/dim] {rel_path}: No changes needed")

        except Exception as e:
            error_count += 1
            try:
                rel_path = file_path.relative_to(root)
            except ValueError:
                rel_path = file_path
            console.print(f"[red]✗[/red] {rel_path}: {e}")

    # Summary
    console.print()
    if dry_run:
        console.print(f"[yellow]Would modify {modified_count} of {len(all_files)} files[/yellow]")
        if error_count:
            console.print(f"[red]Errors: {error_count}[/red]")
        console.print("[dim]Run without --dry-run to apply changes[/dim]")
    else:
        console.print(f"[green]Modified {modified_count} of {len(all_files)} files[/green]")
        if error_count:
            console.print(f"[red]Errors: {error_count}[/red]")


# Export the validate command as a separate entry point
def validate_main():
    """Entry point for dcc-validate command."""
    validate()


if __name__ == "__main__":
    main()
