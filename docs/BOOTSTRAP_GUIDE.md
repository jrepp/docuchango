# docs-cms Bootstrap Guide

This guide shows you how to bootstrap a working `docs-cms` system for agent-driven knowledge management and collaboration.

## What is docs-cms?

`docs-cms` is an opinionated micro-CMS (Content Management System) designed for human-agent collaboration. It provides:

- **Structured Knowledge Base**: Organized documentation with consistent schema validation
- **Agent Grounding**: Agents can read and understand your project's context, decisions, and architecture
- **Version Control**: All documentation lives in git with full history
- **Validation**: Automated checks for frontmatter, links, formatting, and code blocks
- **Self-Documenting**: The CMS itself explains how to use it through examples

## Why Use docs-cms?

### For Humans
- Single source of truth for project decisions and architecture
- Easy to search and navigate
- Consistent format across all documents
- Automated validation catches errors early

### For Agents
- **Context Grounding**: Agents read the CMS to understand your project
- **Decision History**: ADRs document why choices were made
- **Active Knowledge**: Agents maintain and update documentation
- **Collaborative**: Agents can propose new docs, updates, and fixes

## Quick Start

### 1. Initialize docs-cms

Use the CLI to create the project structure, configuration, schema, and templates:

```bash
docuchango init --project-id my-project --project-name "My Project"
```

For an existing repository, inspect `docs-cms/` first and avoid overwriting human-authored documents. If the project already has a `docs-cms` directory, add only missing configuration or guidance files.

### 2. Review Configuration

Review `docs-cms/docs-project.yaml` and keep project-specific values accurate:

```yaml
# yaml-language-server: $schema=./docs-project.schema.json
version: "1"
project:
  id: my-project
  name: My Project
  description: Project documentation hub

structure:
  adr_dir: adr
  rfc_dir: rfcs
  memo_dir: memos
  prd_dir: prd
  template_dir: templates
  document_folders:
    - adr
    - rfcs
    - memos
    - prd
```

Use the local `docs-cms/docs-project.schema.json` file as the config reference. If it is unavailable, use the stable schema URL: `https://jrepp.github.io/docuchango/schemas/docs-project.schema.json`.

### 3. Add Agent Instructions

Create or update a repository-level `AGENTS.md` file so coding agents know that `docs-cms` is the durable project memory:

```markdown
# Agent Instructions

Use `docs-cms/` as durable project memory. Before changing architecture, workflows, documentation policy, validation behavior, templates, or release process, search and read relevant ADRs, RFCs, PRDs, and memos.

When new durable knowledge is created, add or update a `docs-cms` document instead of leaving root-level working notes. Use ADRs for accepted decisions, RFCs for proposals, PRDs for product requirements, and memos for durable findings or plans.

For this repository itself, remember that docuchango maintains docuchango's own docs-cms. Avoid circular wording such as "the tool validates itself" unless the exact scope is clear: changes to docuchango's product behavior belong in `docs-cms/`, while generated examples under `examples/docs-cms/` remain sample content.

Run `docuchango validate --dry-run` before applying automatic documentation fixes, then run `docuchango validate` and summarize any remaining manual issues.
```

### 4. Install docuchango

```bash
pip install docuchango
```

### 5. Create Your First Document

```bash
cp docs-cms/templates/adr-000-template.md docs-cms/adr/adr-001-adopt-docs-cms.md
uuidgen | tr '[:upper:]' '[:lower:]'
```

Then fill all placeholder frontmatter fields, update the heading and body, and validate before committing.

### 6. Validate Your Documentation

```bash
# Preview issues without changing files
docuchango validate --dry-run

# Validate all documents and auto-fix what can be fixed
docuchango validate

# Generate a report
docuchango validate --verbose
```

## Directory Structure

```
my-project/
├── docs-cms/
│   ├── docs-project.yaml       # Project configuration
│   ├── docs-project.schema.json # Validation schema for project configuration
│   ├── adr/                    # Architecture Decision Records
│   │   ├── adr-001-*.md
│   │   ├── adr-002-*.md
│   │   └── ...
│   ├── rfcs/                   # Request for Comments
│   │   ├── rfc-001-*.md
│   │   └── ...
│   ├── memos/                  # Project memos
│   │   ├── memo-001-*.md
│   │   └── ...
│   └── templates/              # Document templates
│       ├── adr-template.md
│       ├── rfc-template.md
│       └── memo-template.md
└── README.md
```

`docs-project.yaml` includes a YAML language-server pointer to
`docs-project.schema.json`. Use that schema when editing config by hand or from
an agent prompt. The stable published schema URL is
`https://jrepp.github.io/docuchango/schemas/docs-project.schema.json`.
Parent repositories can include nested docs projects with:

```yaml
subprojects:
  - vendor/service-a
  - vendor/service-b/docs-project.yaml
```

## Document Types

### Architecture Decision Records (ADRs)
**Purpose**: Document significant architectural decisions

**When to use:**
- Choosing technologies or frameworks
- Defining system architecture
- Setting coding standards
- Infrastructure decisions

**Schema**: See `docuchango/schemas.py` - `ADRSchema`

### Request for Comments (RFCs)
**Purpose**: Propose and discuss significant changes

**When to use:**
- New features or major changes
- Design proposals
- Process changes
- Cross-cutting concerns

**Schema**: See `docuchango/schemas.py` - `RFCSchema`

### Memos
**Purpose**: Share information and context

**When to use:**
- Meeting notes
- Status updates
- Investigation results
- Technical explanations

**Schema**: See `docuchango/schemas.py` - `MemoSchema`

## Frontmatter Fields

All documents require these fields:

```yaml
---
id: doc-NNN                    # Unique identifier (e.g., adr-001)
title: Brief title             # Human-readable title
created: 2026-05-30           # Creation date or timestamp
tags: [tag1, tag2]            # Categorization tags
project_id: my-project        # Project identifier
doc_uuid: uuid-v4-here        # Unique UUID v4
---
```

Some document types require additional fields. For example, ADRs require `status` and `deciders`, RFCs require `status` and `author`, PRDs require `status`, `author`, and `target_release`, and memos require `author`.

### Generating UUIDs

```bash
# macOS/Linux
uuidgen | tr '[:upper:]' '[:lower:]'

# Python
python -c "import uuid; print(uuid.uuid4())"

# Node.js
node -e "console.log(require('crypto').randomUUID())"
```

## Validation

### What Gets Validated

✅ **Frontmatter Schema**
- Required fields present
- Correct types and formats
- Valid UUID v4 format
- Valid status values

✅ **Links**
- Internal links resolve
- No broken references
- Proper markdown link syntax

✅ **Code Blocks**
- Properly fenced
- Language specified
- Balanced delimiters

✅ **Formatting**
- No trailing whitespace
- Blank lines before headings
- Consistent line endings

### Running Validation

```bash
# Preview issues without modifying files
docuchango validate --dry-run

# Verbose output
docuchango validate --verbose

# Check specific directory
docuchango validate --repo-root /path/to/project

# Apply automatic fixes
docuchango validate
```

## Best Practices

### Naming Conventions

**Files**: `{type}-{number}-{kebab-case-title}.md`
- ✅ `adr-001-adopt-microservices.md`
- ✅ `rfc-042-user-authentication.md`
- ❌ `ADR_001.md` (no underscores, wrong case)
- ❌ `decision-about-stuff.md` (no type prefix)

**IDs**: `{type}-{number}`
- ✅ `adr-001`, `rfc-042`, `memo-123`
- ❌ `ADR-1`, `rfc_042` (wrong format)

### Document Workflow

1. **Create from template**: Copy and modify template
2. **Add frontmatter**: Fill in all required fields
3. **Write content**: Use clear, concise language
4. **Preview issues**: Run `docuchango validate --dry-run`
5. **Apply fixes**: Run `docuchango validate` or manually fix any remaining issues
6. **Commit**: Add to git with descriptive message
7. **Review**: Have team review in PR

### Status Transitions

**ADR Status Flow:**
```
Proposed → Accepted → Implemented
        → Deprecated
        → Superseded (by adr-XXX)
```

**RFC Status Flow:**
```
Draft → Proposed → Accepted → Implemented
      → Deprecated
      → Superseded
```

**Memo Status:**
Memos do not require a status. Use them for durable findings, plans, or informational context.

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Validate Documentation

on:
  pull_request:
    paths:
      - 'docs-cms/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install docuchango
        run: pip install docuchango

      - name: Validate docs-cms
        run: docuchango validate --verbose
```

## Next Steps

1. **Add agent instructions**: Create or update `AGENTS.md` with the repository-specific docs-cms guidance above
2. **Read the Agent Guide**: See `docs/AGENT_GUIDE.md` for instructions on how agents should interact with docs-cms
3. **Review Examples**: Check `examples/docs-cms/` for sample documents
4. **Set up CI**: Add validation to your CI/CD pipeline
5. **Write Your First ADR**: Document why you adopted docs-cms!

## Troubleshooting

### Common Issues

**Invalid UUID Format**
```
Error: doc_uuid must be a valid UUID v4 format
Fix: Generate a new UUID with `uuidgen | tr '[:upper:]' '[:lower:]'`
```

**Missing Required Field**
```
Error: Field 'project_id' is required
Fix: Add project_id to frontmatter
```

**Broken Internal Link**
```
Error: Link target not found: ../nonexistent.md
Fix: Update link to point to existing file or create the target
```

**Invalid Status Value**
```
Error: status must be one of the valid values for that document type
Fix: Use a valid status value from the schema
```

## Resources

- **Schema Reference**: `docuchango/schemas.py`
- **Templates**: `docs-cms/templates/`
- **Examples**: `examples/docs-cms/`
- **Agent Guide**: `docs/AGENT_GUIDE.md`
- **GitHub**: https://github.com/jrepp/docuchango
