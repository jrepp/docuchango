# Docuchango

[![PyPI version](https://badge.fury.io/py/docuchango.svg)](https://pypi.org/project/docuchango/)
[![CI](https://github.com/jrepp/docuchango/workflows/CI/badge.svg)](https://github.com/jrepp/docuchango/actions)
[![codecov](https://codecov.io/gh/jrepp/docuchango/branch/main/graph/badge.svg)](https://codecov.io/gh/jrepp/docuchango)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/downloads/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Code quality: strict](https://img.shields.io/badge/code%20quality-strict-brightgreen.svg)](pyproject.toml)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/jrepp/docuchango/graphs/commit-activity)
[![Development Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/jrepp/docuchango)

![Docuchango logo](docs-cms/imgs/docuchango.png)

A command-line tool to validate and automatically fix Docusaurus documentation, ensuring frontmatter, links, code blocks, and formatting meet quality standards.

## Why Docuchango?

- **Automated fixes** - Don't just find errors, fix them automatically (whitespace, code blocks, frontmatter)
- **Docusaurus-specific** - Purpose-built for docs-cms projects with ADR, RFC, Memo, and PRD templates
- **Strict validation** - Enforces consistent frontmatter schemas with Pydantic, catches issues before build time
- **Fast & CI-ready** - Processes 100+ docs in under a second, perfect for pre-commit hooks and CI pipelines

## Installation

```bash
# Install from PyPI (latest version)
pip install docuchango

# Or use uvx to run without installing
uvx docuchango --help

# Or use the install script (includes uv)
curl -sSL https://raw.githubusercontent.com/jrepp/docuchango/main/install.sh | bash
```

## Quick Start

```bash
# Initialize a new docs-cms project with templates and structure
docuchango init

# Validate your documentation and auto-fix issues where possible
docuchango validate

# Preview issues without changing files
docuchango validate --dry-run
```

```mermaid
flowchart LR
    A[docs-cms/] --> B{docuchango}
    B -->|validate --dry-run| C[✓ Report issues]
    B -->|validate| D[✓ Fix what it can]
    D --> E[Docusaurus]
    E -->|build| F[📚 Static site]

    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#bfb,stroke:#333
    style D fill:#bfb,stroke:#333
    style E fill:#feb,stroke:#333
    style F fill:#bfb,stroke:#333
```

## Usage Examples

### Validation Commands

```bash
# Run validation with verbose output
$ docuchango validate --verbose

📂 Scanning documents...
   Found 23 documents

✓ Validating links...
   Found 47 total links

❌ DOCUMENTS WITH ERRORS (2):
   adr/adr-001.md:
   ✗ Missing field: 'deciders'
   ✗ Invalid status: 'Draft'

# Validate everything (default)
docuchango validate

# Skip slow build checks
docuchango validate --skip-build
```

### Repair & Bulk Commands

```bash
# Validate and auto-fix common issues
docuchango validate

# Preview fixes without changing files
docuchango validate --dry-run --verbose

# Derive immutable created timestamps from git history
docuchango bulk timestamps --dry-run

# Bulk update frontmatter fields
docuchango bulk update --type adr --set status=Accepted --dry-run

# Migrate legacy frontmatter to the current schema
docuchango migrate --project-id my-project --dry-run
```

### Mixed-Schema Monorepos

`docs-project.yaml` can map multiple document lanes in one repository with
different schemas, naming rules, and roots. Generic lanes stay strict by
default, but you can opt specific folders into plain Markdown when frontmatter
is not a project goal.

```yaml
structure:
  docs_roots: [docs]
  doc_types:
    adr:
      schema: adr
      folders: [adr]
      filename_pattern: "^(adr)-(\\d{3})-(.+)\\.md$"
      enforce_filename_pattern: true
    design-notes:
      schema: generic
      folders: [design]
      filename_pattern: ".+\\.md$"
      enforce_filename_pattern: false
      require_frontmatter: false
```

### Bootstrap & Guides

```bash
# View agent integration guides
docuchango bootstrap --guide agent
docuchango bootstrap --guide best-practices
```

### CLI Shortcuts

```bash
dcc-validate        # Same as docuchango validate
```

## CMS Folder Structure

```text
docs-cms/
├── adr/              # Architecture Decision Records
│   ├── adr-001-*.md
│   └── adr-002-*.md
├── rfcs/             # Request for Comments
│   └── rfc-001-*.md
├── memos/            # Technical memos
│   └── memo-001-*.md
└── prd/              # Product requirements
    └── prd-001-*.md
```

### Document Schema (frontmatter)

Each document requires structured frontmatter. Here's an example with field descriptions:

```yaml
---
# Unique identifier matching the filename (e.g., "adr-001", "rfc-042")
id: "adr-001"

# Human-readable title for the document
title: "Use Click for CLI Framework"

# Current status - valid values depend on doc type
# ADR: Proposed, Accepted, Deprecated, Superseded
# RFC: Draft, In Review, Accepted, Rejected, Implemented
# Memo: Draft, Published, Archived
status: Accepted

# ISO 8601 date (YYYY-MM-DD) when the document was created
date: 2025-01-26

# Who made or approved this decision (ADR-specific field)
deciders: Engineering Team

# Categorization tags for search and filtering
tags: ["cli", "framework", "tooling"]

# Project identifier for organizing docs across multiple projects
project_id: "my-project"

# Auto-generated UUID for tracking and references (generate once, never change)
doc_uuid: "550e8400-e29b-41d4-a716-446655440000"
---
```

**Note**: Different document types (ADR, RFC, Memo, PRD) have slightly different required fields. Use `docuchango bootstrap` to see templates for each type.

### Schema Structure

```mermaid
graph TD
    A[Document] --> B[Frontmatter]
    A --> C[Content]

    B --> D[Required Fields]
    B --> E[Optional Fields]

    D --> F[id: adr-001]
    D --> G[title: string]
    D --> H[status: Literal]
    D --> I[date/created]
    D --> J[tags: list]
    D --> K[project_id]
    D --> L[doc_uuid: UUID]

    C --> M[Markdown Body]
    C --> N[Code Blocks]
    C --> O[Links]

    style A fill:#bbf,stroke:#333
    style B fill:#feb,stroke:#333
    style C fill:#bfb,stroke:#333
    style D fill:#fbb,stroke:#333
```

**Templates & Docs:**
- [ADR Template](templates/adr-template.md) | [RFC Template](templates/rfc-template.md) | [Memo Template](templates/memo-template.md)
- [Schema Docs](docuchango/schemas.py) | [ADR-001](docs-cms/adr/adr-001-pydantic-schema-validation.md)

## Features

- **Validates** frontmatter (required fields, valid formats)
- **Checks links** (internal, relative, broken refs)
- **Fixes automatically** (whitespace, code blocks, frontmatter, timestamps)
- **Bulk operations** (set, add, remove, rename frontmatter fields across all docs)
- **Git-aware** (updates timestamps from commit history)
- **Fast** (100 docs in < 1s)
- **CI-ready** (exit codes, clear errors)

## Python API

```python
from docuchango.validator import DocValidator
from docuchango.schemas import ADRFrontmatter

# Validate
validator = DocValidator(repo_root=".", verbose=True)
validator.scan_documents()
validator.check_code_blocks()
validator.check_formatting()

# Use schemas
adr = ADRFrontmatter(**frontmatter_data)
```

## Development

```bash
# Setup
uv sync
pip install -e ".[dev]"

# Test
pytest                      # Run all tests (628 tests)
pytest --cov=docuchango     # With coverage report
pytest -n auto              # Parallel execution
pytest -v                   # Verbose output

# Test Statistics
# • 628 passing tests (with textstat installed)
# • 569 core tests + 59 readability tests
# • Zero flaky or xfail tests
# • Full Python 3.9-3.13 compatibility
# • Comprehensive edge case coverage (frontmatter, links, timestamps, bulk updates)

# Lint
ruff format .
ruff check .
mypy docuchango tests
actionlint  # Lint GitHub Actions workflows

# Build
uv build
```

## Documentation

- [Templates](templates/) - Starter files for ADR, RFC, Memo, PRD
- [ADRs](docs-cms/adr/) - Architecture decisions
- [RFCs](docs-cms/rfcs/) - Technical proposals

## Requirements

- Python 3.9+
- Works on macOS, Linux, Windows

## License

Mozilla Public License Version 2.0 (MPL-2.0) - See [LICENSE](LICENSE) file

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

## Glossary: Issues Detected and Fixed

This comprehensive reference lists all documentation issues that docuchango can detect and automatically fix.

### Frontmatter Issues

**Detected:**
- Missing YAML frontmatter
- Missing required fields (`id`, `title`, `status`, `date`, `tags`, `project_id`, `doc_uuid`)
- Invalid field types or formats
- Invalid status values for document type (e.g., "Draft" instead of "Proposed" for ADRs)
- Missing document-type-specific fields (e.g., `deciders` for ADRs)
- Invalid date formats (must be ISO 8601: YYYY-MM-DD)
- Malformed UUID values
- ID/filename mismatches (frontmatter `id` doesn't match filename)
- ID/title mismatches (frontmatter `id` doesn't match title number)
- Duplicate IDs across documents
- Duplicate UUIDs across documents

**Auto-Fixed:**
- ✓ Generates missing frontmatter blocks with sensible defaults
- ✓ Adds missing required fields (id, title, status, date, tags, project_id, doc_uuid)
- ✓ Fixes invalid status values (maps common variations to valid values by doc type)
  - Handles empty strings, special characters, and whitespace
  - Supports fuzzy matching for common misspellings
- ✓ Converts invalid date formats to ISO 8601 (YYYY-MM-DD)
  - Supports multiple input formats (slash, dot, long month names)
  - Converts datetime objects to ISO 8601 strings
- ✓ Normalizes tags (converts to arrays, lowercase-with-dashes, removes duplicates, sorts)
- ✓ Trims whitespace from all string values
- ✓ Removes empty strings and null values
- ✓ Updates timestamps from git history (created/updated fields)
  - Automatically adds missing `created` or `updated` fields
  - Migrates legacy `date` field to `created`/`updated` pair
  - Works without `status` field requirement
- ✓ Handles empty frontmatter blocks (initializes with empty metadata)
- ✓ Validates operation types with clear error messages
- ✓ Detects and reports binary files (non-UTF-8 content)

**Requires Manual Fix:**
- Missing YAML frontmatter (complex cases)
- Invalid field types or formats
- Missing document-type-specific fields (e.g., `deciders` for ADRs)
- Malformed UUID values
- ID/filename mismatches (frontmatter `id` doesn't match filename)
- ID/title mismatches (frontmatter `id` doesn't match title number)
- Duplicate IDs across documents
- Duplicate UUIDs across documents

### Code Block Issues

**Detected:**
- Opening code fences without language specification (bare \`\`\`)
- Closing code fences with language/text (should be bare \`\`\`)
- Unclosed code blocks (missing closing fence)
- Missing blank line before opening fence
- Missing blank line after closing fence
- Unbalanced code fences

**Auto-Fixed:**
- ✓ Adds "text" language to bare opening fences
- ✓ Removes language from closing fences
- ✓ Adds missing closing fences
- ✓ Inserts blank lines before/after fences

### Link Issues

**Detected:**
- Broken internal document links (file not found)
- Invalid relative paths (`./path` or `../path` pointing to non-existent files)
- Ambiguous link formats
- Problematic cross-plugin links (multiple `../` levels)
- Broken ADR/RFC cross-references

**Auto-Fixed:**
- ✓ Updates broken internal links to correct paths
- ✓ Converts problematic cross-plugin links to absolute GitHub URLs
- ✓ Fixes document link formats

### MDX Compatibility Issues

**Detected:**
- Unescaped `<` before numbers (e.g., "< 10")
- Unescaped `>` before numbers (e.g., "> 5")
- MDX compilation errors
- JSX syntax incompatibilities
- Special characters that break MDX parsing

**Auto-Fixed:**
- ✓ Escapes special MDX characters (`&lt;`, `&gt;`)
- ✓ Fixes MDX syntax issues
- ✓ Corrects JSX-incompatible markdown

### Formatting Issues

**Detected:**
- Trailing whitespace on lines
- More than 2 consecutive blank lines
- Inconsistent line endings

**Auto-Fixed:**
- ✓ Removes trailing whitespace
- ✓ Normalizes multiple blank lines

### Filename & Naming Issues

**Detected:**
- Invalid filename patterns (must be: `type-NNN-slug.md`)
- Uppercase in filenames (deprecated, must be lowercase)
- Inconsistent ADR/RFC/Memo numbering

**Requires Manual Fix:** Flagged for user intervention

### Build & Compilation Issues

**Detected:**
- TypeScript compilation errors in Docusaurus config
- Full Docusaurus build failures
- MDX compilation failures via @mdx-js/mdx
- Build warnings

**Requires Manual Fix:** Reported for debugging and manual resolution

### Migration & Import Issues

**Auto-Fixed:**
- ✓ Proto import syntax issues
- ✓ Migration syntax corrections

---

**Issue Categories:**
1. **Frontmatter** - Schema validation, required fields, format checking
2. **Code Blocks** - Fence formatting, language labels, balance
3. **Links** - Broken links, cross-references, path resolution
4. **MDX** - Compilation, special character escaping, JSX compatibility
5. **Formatting** - Whitespace, blank lines
6. **Identifiers** - IDs, UUIDs, filename consistency
7. **Build** - TypeScript, Docusaurus compilation
8. **Migration** - Import syntax, migration corrections

## Links

- [GitHub](https://github.com/jrepp/docuchango)
- [PyPI](https://pypi.org/project/docuchango)
- [Issues](https://github.com/jrepp/docuchango/issues)
