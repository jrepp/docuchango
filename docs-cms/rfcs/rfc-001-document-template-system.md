---
id: "rfc-001"
title: "Document Template System"
status: Accepted
author: Engineering Team
created: 2025-01-26
updated: 2025-01-26
tags: ["templates", "documentation", "standards"]
project_id: "docuchango"
doc_uuid: "fe162317-3fa5-44b5-a1f3-1b2471d47548"
---

# RFC-001: Document Template System

## Summary

Provide templates for ADR, RFC, Memo, PRD, FRD, PRDFAQ to ensure consistent documentation structure.

## Problem

Without templates:
- Every author uses different formats
- Documents miss required fields
- Reviews waste time on formatting
- Hard to validate completeness

## Solution

Templates in `templates/` directory with:
- Complete frontmatter with all required fields
- Standard sections and guidance
- UUID generation instructions
- Work with `docuchango validate`

### Templates

| Type | Use Case |
|------|----------|
| ADR | Architecture decisions |
| RFC | Feature proposals |
| Memo | Technical findings |
| PRD | Product requirements |
| FRD | Feature specifications |
| PRDFAQ | Product announcements |

### Usage

```bash
# Copy template
cp templates/adr-template.md docs-cms/adr/adr-042-my-decision.md

# Edit content, update XXX placeholders, generate UUID
vi docs-cms/adr/adr-042-my-decision.md

# Validate
docuchango validate
```

### Example Template

```yaml
---
id: "adr-XXX"
title: "Decision Title Here"
status: Proposed
date: YYYY-MM-DD
deciders: Team Name
tags: ["tag1", "tag2"]
project_id: "your-project-id"
doc_uuid: "00000000-0000-4000-8000-000000000000"
---

# ADR-XXX: Decision Title

## Context
What problem are we solving?

## Decision
What are we doing?

## Consequences
What becomes easier or harder?
```

### Generate UUID

```bash
# macOS/Linux
uuidgen | tr '[:upper:]' '[:lower:]'

# Python
python -c "import uuid; print(uuid.uuid4())"
```

## Implementation

**Done:**
- Created all templates (ADR, RFC, Memo, PRD, FRD, PRDFAQ)
- Templates pass validation
- Templates README with usage guide

**Next:**
- Add `docuchango new adr "Title"` command
- Auto-generate UUIDs

## Alternatives

**No templates**: Too inconsistent, hard to validate

**Generator tool**: More complex, less flexible than templates + validation

## Result

- Standard structure for all doc types
- Validation ensures completeness
- Faster document creation
