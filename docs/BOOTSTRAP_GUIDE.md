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

### 1. Bootstrap the Structure

Create the core `docs-cms` directory structure:

```bash
mkdir -p docs-cms/{adr,rfcs,memos,templates}
```

### 2. Create Configuration

Create `docs-cms/docs-project.yaml`:

```yaml
project:
  id: my-project
  name: My Project
  description: Project documentation hub

structure:
  adr_dir: adr
  rfc_dir: rfcs
  memo_dir: memos
  template_dir: templates
```

### 3. Copy Templates

Copy templates from docuchango:

```bash
# ADR Template
cat > docs-cms/templates/adr-template.md << 'EOF'
---
id: adr-NNN
title: Brief decision title
status: Proposed
date: YYYY-MM-DD
tags: [architecture, decision]
project_id: my-project
doc_uuid: generate-uuid-v4-here
---

# ADR-NNN: Brief Decision Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue we're facing? What constraints exist?

## Decision
What did we decide to do?

## Consequences
What are the positive and negative outcomes?

## Alternatives Considered
- Alternative 1: Why not chosen
- Alternative 2: Why not chosen
EOF

# RFC Template
cat > docs-cms/templates/rfc-template.md << 'EOF'
---
id: rfc-NNN
title: Proposal title
status: Draft
date: YYYY-MM-DD
author: Your Name
tags: [rfc, proposal]
project_id: my-project
doc_uuid: generate-uuid-v4-here
---

# RFC-NNN: Proposal Title

## Summary
Brief 2-3 sentence overview

## Motivation
Why are we doing this? What problem does it solve?

## Proposed Solution
Detailed explanation of the proposal

## Implementation
How will this be implemented?

## Alternatives
What other approaches were considered?

## Open Questions
- Question 1?
- Question 2?
EOF

# Memo Template
cat > docs-cms/templates/memo-template.md << 'EOF'
---
id: memo-NNN
title: Memo title
date: YYYY-MM-DD
author: Your Name
tags: [memo]
project_id: my-project
doc_uuid: generate-uuid-v4-here
---

# Memo: Title

## Purpose
Why this memo exists

## Key Points
- Point 1
- Point 2
- Point 3

## Next Actions
- [ ] Action 1
- [ ] Action 2
EOF
```

### 4. Install docuchango

```bash
pip install docuchango
```

### 5. Create Your First Document

```bash
# Generate a UUID
uuidgen | tr '[:upper:]' '[:lower:]'
# Output: 550e8400-e29b-41d4-a716-446655440000

# Create first ADR
cat > docs-cms/adr/adr-001-adopt-docs-cms.md << 'EOF'
---
id: adr-001
title: Adopt docs-cms for Documentation
status: Accepted
date: 2025-10-27
tags: [architecture, documentation]
project_id: my-project
doc_uuid: 550e8400-e29b-41d4-a716-446655440000
---

# ADR-001: Adopt docs-cms for Documentation

## Status
Accepted

## Context
We need a structured way to document architectural decisions and collaborate with AI agents on documentation.

## Decision
Adopt docs-cms as our documentation framework with docuchango validation.

## Consequences

**Positive:**
- Consistent documentation structure
- Automated validation
- Version controlled in git
- Agent-friendly format

**Negative:**
- Requires learning frontmatter schema
- Need to install docuchango tooling

## Alternatives Considered
- Wiki: Too unstructured, hard to validate
- Confluence: Not in version control, not agent-friendly
- Plain markdown: No validation, no consistency
EOF
```

### 6. Validate Your Documentation

```bash
# Validate all documents
docuchango validate

# Fix common issues
docuchango fix

# Generate a report
docuchango validate --verbose
```

## Directory Structure

```
my-project/
├── docs-cms/
│   ├── docs-project.yaml       # Project configuration
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
status: Draft                  # Status (varies by type)
date: 2025-10-27              # Creation/update date
tags: [tag1, tag2]            # Categorization tags
project_id: my-project        # Project identifier
doc_uuid: uuid-v4-here        # Unique UUID v4
---
```

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
# Quick validation
docuchango validate

# Verbose output
docuchango validate --verbose

# Check specific directory
docuchango validate --repo-root /path/to/project

# Auto-fix issues
docuchango fix
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
4. **Validate**: Run `docuchango validate`
5. **Fix issues**: Run `docuchango fix` or manually fix
6. **Commit**: Add to git with descriptive message
7. **Review**: Have team review in PR

### Status Transitions

**ADR Status Flow:**
```
Proposed → Accepted → Implemented
        → Rejected
        → Superseded (by adr-XXX)
```

**RFC Status Flow:**
```
Draft → In Review → Approved → Implemented
      → Rejected
      → Withdrawn
```

**Memo Status:**
Memos typically don't have status (informational only)

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

      - name: Check for broken links
        run: docuchango validate --check-links
```

## Next Steps

1. **Read the Agent Guide**: See `docs/AGENT_GUIDE.md` for instructions on how agents should interact with docs-cms
2. **Review Examples**: Check `examples/docs-cms/` for sample documents
3. **Set up CI**: Add validation to your CI/CD pipeline
4. **Write Your First ADR**: Document why you adopted docs-cms!

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
Error: status must be one of: Proposed, Accepted, Rejected, Superseded
Fix: Use a valid status value from the schema
```

## Resources

- **Schema Reference**: `docuchango/schemas.py`
- **Templates**: `docs-cms/templates/`
- **Examples**: `examples/docs-cms/`
- **Agent Guide**: `docs/AGENT_GUIDE.md`
- **GitHub**: https://github.com/jrepp/docuchango
