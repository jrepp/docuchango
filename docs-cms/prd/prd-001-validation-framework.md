---
author: Engineering Team
created: 2025-10-26T02:35:12Z
doc_uuid: e5f6a7b8-c9d0-4e9f-2a3b-4c5d6e7f8a9b
id: prd-001
project_id: docuchango
status: Launched
tags:
- documentation
- framework
- product
- validation
title: 'Docuchango: Documentation Validation Tool'
---

# PRD-001: Docuchango

## What It Does

Docuchango validates and fixes Docusaurus documentation. It checks frontmatter, links, code blocks, and formatting. It can automatically fix common issues.

## The Problem

Writing documentation is tedious:
- Frontmatter fields are easy to mess up
- Internal links break when files move
- Code blocks need specific formatting
- Whitespace issues cause build failures
- Every doc type needs consistent structure

Fixing these manually wastes time. Docusaurus builds catch some errors but error messages are unclear.

## The Solution

A Python CLI that:
1. Validates docs before you commit
2. Fixes common issues automatically
3. Runs in CI to prevent bad docs from merging
4. Provides clear error messages

```bash
# Validate everything
docuchango validate

# Fix issues automatically
docuchango fix all

# Fix specific things
docuchango fix code-blocks
```

## Who Uses It

- **Engineers** writing ADRs and RFCs
- **Technical writers** maintaining docs
- **DevOps teams** running it in CI
- **AI systems** that need structured docs

## Core Features

### Validation

Check required frontmatter fields:

```yaml
# ADR must have: title, status, date, deciders, tags, id
# RFC must have: title, status, author, created, tags, id
# Memo must have: title, author, created, updated, tags, id
```

Validate links:
- Internal relative links (`./other-doc.md`)
- Absolute paths (`/docs/guide.md`)
- Catches broken references before users see them

Check formatting:
- Code blocks have language tags
- No trailing whitespace
- Consistent numbering (adr-001, adr-002...)
- Valid UUID formats

### Auto-Fix

Fix these automatically:
- Add missing code fence languages (use `text` as default)
- Remove trailing whitespace
- Add blank lines before code fences
- Generate missing project_id and doc_uuid fields

### Templates

Starter files for new documents:

```bash
cp templates/adr-template.md docs/adr/adr-042-my-decision.md
# Edit and run: docuchango validate
```

Templates for: ADR, RFC, Memo, PRD, FRD, PRDFAQ

## How It Works

```bash
# Install
pip install docuchango

# Validate all docs
docuchango validate --repo-root /path/to/docs

# See errors
❌ adr/adr-001.md:
   - Missing field: 'deciders'
   - Invalid status: 'Draft' (use: Proposed, Accepted, Deprecated, Superseded)

# Fix automatically
docuchango fix all

# Use in CI
- name: Validate docs
  run: |
    pip install docuchango
    docuchango validate
```

## What's Next

**Version 1.1** (Future):
- Interactive fix mode (show diffs before applying)
- Generate new docs from command: `docuchango new adr "My Decision"`
- Config file support for custom rules

**Version 2.0** (Future):
- Git integration (validate only changed files)
- IDE plugins
- Pre-commit hooks

## Technical Details

**Requirements:**
- Python 3.10+
- Works on macOS, Linux, Windows

**Dependencies:**
- pydantic (schemas)
- click (CLI)
- python-frontmatter (YAML parsing)
- pyyaml
- rich (terminal output)

**Performance:**
- Validates 100 docs in under 1 second
- Low memory usage

**Testing:**
- 61 tests covering validation, fixing, and schemas
- Runs in CI on Python 3.10-3.13

## Why Docuchango?

Other tools don't solve the full problem:
- `markdownlint` - doesn't validate frontmatter or links
- `remark-lint` - requires complex configuration
- `vale` - checks style, not structure
- Custom scripts - not reusable or maintained

Docuchango validates frontmatter schemas, checks links, and fixes issues automatically.

## Related Docs

- [ADR-001: Pydantic Schema Validation](../adr/adr-001-pydantic-schema-validation.md)
- [ADR-002: Click CLI Framework](../adr/adr-002-click-cli-framework.md)
- [RFC-001: Document Template System](../rfcs/rfc-001-document-template-system.md)