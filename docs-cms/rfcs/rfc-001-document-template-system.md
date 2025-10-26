---
id: "rfc-001"
title: "Document Template System for Structured Documentation"
status: Accepted
author: Engineering Team
created: 2025-01-26
updated: 2025-01-26
tags: ["templates", "documentation", "standards"]
project_id: "docuchango"
doc_uuid: "d4e5f6a7-b8c9-4d8e-1f2a-3b4c5d6e7f8a"
---

# RFC-001: Document Template System for Structured Documentation

## Summary

Proposes a standardized template system for different document types (ADR, RFC, Memo, PRD, FRD, PRDFAQ, Generic) to ensure consistency and completeness across technical documentation.

## Motivation

Teams writing documentation face challenges:

- **Inconsistent Structure**: Different authors use different formats
- **Missing Information**: Documents lack required context or metadata
- **Hard to Find**: No standard location or naming convention
- **Review Friction**: Reviewers spend time on formatting vs content
- **Validation Gaps**: No automated checking of document completeness

A template system solves these by providing:

- Standard structure for each document type
- Required frontmatter fields
- Section guidance and examples
- Automated validation with docuchango

## Proposed Design

### Template Structure

Each template includes:

1. **Complete YAML Frontmatter** - All required fields with examples
2. **Document Sections** - Standard headings and guidance
3. **Inline Comments** - Explain what to include in each section
4. **UUID Placeholder** - Clear instructions for generation

### Template Types

| Template | Use Case | Key Sections |
|----------|----------|--------------|
| **ADR** | Architecture decisions | Context, Decision, Consequences |
| **RFC** | Feature proposals | Summary, Motivation, Design, Alternatives |
| **Memo** | Technical findings | Executive Summary, Findings, Recommendations |
| **PRD** | Product requirements | Goals, User Stories, Success Metrics |
| **FRD** | Feature specifications | Requirements, Acceptance Criteria, API |
| **PRDFAQ** | Product announcements | Press Release, FAQ |
| **Generic** | Guides and tutorials | Flexible structure |

### Example: ADR Template

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

## Status

Proposed | Accepted | Deprecated | Superseded

## Context

What is the issue we're seeing that is motivating this decision?

## Decision

What is the change we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

### Validation Integration

All templates are designed to pass `docuchango validate`:

```bash
# Copy template
cp templates/adr-template.md docs-cms/adr/adr-042-my-decision.md

# Edit: Update XXX, dates, UUID, content
vi docs-cms/adr/adr-042-my-decision.md

# Validate
docuchango validate --repo-root .

# Auto-fix common issues
docuchango fix all --repo-root .
```

## Detailed Design

### Frontmatter Requirements

Each document type has specific required fields:

**ADR**:
- `id`, `title`, `status`, `date`, `deciders`
- `tags`, `project_id`, `doc_uuid`

**RFC**:
- `id`, `title`, `status`, `author`, `created`
- `updated` (optional), `tags`, `project_id`, `doc_uuid`

**Memo**:
- `id`, `title`, `author`, `created`, `updated`
- `tags`, `project_id`, `doc_uuid`

### UUID Generation

Templates provide multiple UUID generation methods:

```bash
# macOS/Linux
uuidgen | tr '[:upper:]' '[:lower:]'

# Python
python -c "import uuid; print(uuid.uuid4())"

# Node.js
node -e "console.log(require('crypto').randomUUID())"
```

### Template Location

Templates live in `templates/` directory:

```text
templates/
├── README.md              # Usage guide
├── adr-template.md
├── rfc-template.md
├── memo-template.md
├── prd-template.md
├── frd-template.md
├── prdfaq-template.md
└── generic-doc-template.md
```

## Implementation Plan

### Phase 1: Core Templates (Complete)

- [x] Create template directory structure
- [x] Implement ADR, RFC, Memo templates
- [x] Add validation schemas in docuchango
- [x] Write templates README with usage guide

### Phase 2: Product Templates (Complete)

- [x] Implement PRD template
- [x] Implement FRD template
- [x] Implement PRDFAQ template
- [x] Add examples in docs-cms/

### Phase 3: Tooling Integration (In Progress)

- [ ] Add `docuchango init` command to scaffold new documents
- [ ] Generate UUIDs automatically
- [ ] Validate template compliance in CI

### Phase 4: Documentation (Pending)

- [ ] Add template usage to main README
- [ ] Create video walkthrough
- [ ] Document best practices

## Alternatives Considered

### 1. No Templates - Free-Form Documentation

**Pros**:
- Maximum flexibility
- No learning curve

**Cons**:
- Inconsistent structure
- Missing information
- Hard to validate
- Review friction

**Decision**: Rejected - Too much inconsistency

### 2. Strict Document Generator Tool

**Pros**:
- Enforces consistency
- Guided experience

**Cons**:
- Additional tooling complexity
- Harder to customize
- Learning curve for tool

**Decision**: Rejected - Templates + validation is simpler

### 3. Docusaurus Built-in Templates

**Pros**:
- Integrated with platform

**Cons**:
- Docusaurus-specific
- Less flexible
- Harder to validate

**Decision**: Rejected - Need standalone solution

## Security Considerations

- Templates use placeholder UUIDs (not real secrets)
- No sensitive data in templates
- Users must generate their own UUIDs
- Validation prevents accidental secret commits (via .env check)

## Testing Plan

- All templates pass `docuchango validate`
- Templates work with `docuchango fix`
- Test docs-cms uses all templates
- CI validates template compliance

## Success Metrics

- 90%+ of new docs use templates
- Validation errors reduced by 80%
- Review time reduced by 50%
- Template satisfaction score > 4/5

## Open Questions

1. Should we add more specialized templates (e.g., RFD, PEP)?
2. Should templates support multiple languages?
3. Should we provide IDE snippets for templates?

## References

- [ADR GitHub Repository](https://adr.github.io/)
- [RFC Process (Rust)](https://rust-lang.github.io/rfcs/)
- [Amazon PRDFAQ Process](https://www.producttalk.org/2023/03/amazon-prfaq/)
- [C4 Model](https://c4model.com/)

## Related Documents

- [ADR-001: Pydantic Schema Validation](../adr/adr-001-pydantic-schema-validation.md)
- [Memo-001: Template Usage Patterns](../memos/memo-001-template-usage-patterns.md)
