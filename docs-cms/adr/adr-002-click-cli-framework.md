---
created: 2025-10-26T02:35:12Z
deciders: Engineering Team
doc_uuid: b2c3d4e5-f6a7-4b6c-9d0e-1f2a3b4c5d6e
id: adr-002
project_id: docuchango
status: Accepted
tags:
- architecture
- cli
- click
- command-line
title: Use Click for CLI Framework
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