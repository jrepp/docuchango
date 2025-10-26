---
id: "adr-002"
title: "Use Click for CLI Framework"
status: Accepted
date: 2025-01-26
deciders: Engineering Team
tags: ["click", "cli", "command-line", "architecture"]
project_id: "docuchango"
doc_uuid: "b2c3d4e5-f6a7-4b6c-9d0e-1f2a3b4c5d6e"
---

# ADR-002: Use Click for CLI Framework

## Status

Accepted

## Context

Docuchango provides command-line tools (`docuchango`, `dcc-validate`, `dcc-fix`) that need:

- Multiple subcommands (validate, fix, test)
- Options and flags (--verbose, --repo-root, --fix)
- Help text generation
- Argument validation
- Good user experience

Options considered:

1. **argparse** - Python stdlib, no dependencies
2. **Click** - Popular, feature-rich, excellent UX
3. **Typer** - Modern, uses type hints
4. **argcomplete** - Adds completion to argparse

## Decision

We will use **Click** for all command-line interfaces.

## Rationale

### Advantages

1. **Mature and Stable**: Battle-tested in production across thousands of projects
2. **Excellent Documentation**: Comprehensive guides and examples
3. **Composable**: Easy to nest commands and share options
4. **Decorators**: Clean, Pythonic API using decorators
5. **Testing Support**: Built-in testing utilities (CliRunner)
6. **Wide Adoption**: Used by Flask, pip, AWS CLI, and many others
7. **Rich Features**: Colors, prompts, progress bars out of the box

### Example Usage

```python
@click.group()
@click.version_option(version="0.1.0")
def main():
    """Docuchango - Docusaurus validation and repair framework."""
    pass

@main.command()
@click.option("--repo-root", type=click.Path(exists=True))
@click.option("--verbose", is_flag=True)
def validate(repo_root, verbose):
    """Validate documentation."""
    validator = PrismDocValidator(repo_root=repo_root, verbose=verbose)
    validator.scan_documents()
    validator.validate_links()
```

### Trade-offs

- **Dependency**: Adds Click as a dependency
- **Not Type-First**: Doesn't use type hints for arguments (unlike Typer)

## Consequences

### Positive

- Easy to add new commands
- Consistent CLI experience across all tools
- Built-in testing with CliRunner
- Good error messages and help text
- Extensible for future features

### Negative

- External dependency (though widely used)
- Click decorators may feel magical to some developers

## Alternatives Considered

### argparse (stdlib)

Would avoid dependency but:
- More verbose code
- Less composable
- No built-in testing utilities
- Manual help text formatting
- No colors or progress bars

### Typer

Would provide type-first API but:
- Newer, less mature
- Smaller ecosystem
- Uses FastAPI patterns (may be unfamiliar)
- Extra learning curve

## References

- [Click Documentation](https://click.palletsprojects.com/)
- [Click Examples](https://github.com/pallets/click/tree/main/examples)
- [Testing Click Applications](https://click.palletsprojects.com/en/8.1.x/testing/)
