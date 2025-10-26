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

## Decision

Use Click for all CLI commands.

## Why

Need to build `docuchango validate`, `docuchango fix`, etc. with subcommands, options, and good UX.

Click gives us:
- Easy subcommand nesting with decorators
- Built-in help text and colors
- Testing utilities (CliRunner)
- Used by Flask, pip, AWS CLI

```python
@click.group()
def main():
    """Docuchango CLI."""
    pass

@main.command()
@click.option("--repo-root", type=click.Path(exists=True))
@click.option("--verbose", is_flag=True)
def validate(repo_root, verbose):
    """Validate documentation."""
    validator = DocValidator(repo_root=repo_root, verbose=verbose)
    validator.scan_documents()
```

## Alternatives

**argparse**: No dependency but more verbose, no testing utilities, no colors

**Typer**: Type-first but newer, smaller ecosystem, different patterns

## Result

- Easy to add new commands
- Clean decorator-based API
- Built-in testing support
- Trade-off: One more dependency
