---
# REQUIRED FIELDS - All must be present for validation to pass
id: "adr-XXX"  # Lowercase format: "adr-XXX" where XXX matches filename number (e.g., "adr-001")
slug: adr-XXX-brief-description  # URL-friendly slug (lowercase-with-dashes)
title: "ADR-XXX: Decision Title"  # Must start with "ADR-XXX:" where XXX is 3-digit number
status: Proposed  # Valid values: Proposed, Accepted, Deprecated, Superseded, Implemented
created: YYYY-MM-DD  # ISO 8601 format (YYYY-MM-DD) - date ADR was first created, DO NOT CHANGE after initial creation
                     # Generate: date +%Y-%m-%d  OR  python -c "from datetime import date; print(date.today())"  OR  auto-set with: docuchango bulk timestamps
author: Your Name  # Person or team who wrote this ADR (e.g., "Jacob Repp", "Platform Team")
                   # Generate: git config user.name
deciders: Your Name  # Team or person who made the decision (e.g., "Core Team", "Platform Team", "John Smith")
tags: ["architecture", "example-tag"]  # List of lowercase-with-dashes tags (e.g., ["api-design", "performance"])
project_id: "your-project-id"  # Project identifier from docs-project.yaml
doc_uuid: "00000000-0000-4000-8000-000000000000"  # UUID v4 - Generate: uuidgen  OR  python -c "import uuid; print(uuid.uuid4())"
---

# ADR-XXX: Decision Title

## Context

What is the issue we're trying to solve? What is the background context?

Include:
- Problem statement and why this decision is necessary now
- Current situation and requirements/constraints
- Stakeholders and decision drivers
- Forces at play (technical, organizational, timeline)

## Decision

What did we decide to do? Be specific and concrete.

State the chosen solution clearly:
- What we will do
- How we will implement it
- Key technical choices and approach

## Rationale

Why did we choose this approach? What makes this the best solution?

### Decision Drivers

Key factors that influenced this decision:

- **Driver 1**: Description (e.g., Performance requirements)
- **Driver 2**: Description (e.g., Developer experience)
- **Driver 3**: Description (e.g., Cost/maintenance)

### Alternatives Considered

#### Alternative 1: [Name]

Description of this alternative approach.

**Pros:**
- Benefit 1
- Benefit 2

**Cons:**
- Limitation 1
- Limitation 2

**Rejected because**: Specific reason tied to decision drivers

#### Alternative 2: [Name]

Description of this alternative approach.

**Pros:**
- Benefit 1
- Benefit 2

**Cons:**
- Limitation 1
- Limitation 2

**Rejected because**: Specific reason tied to decision drivers

## Consequences

What are the implications of this decision?

### Positive Consequences

- **Benefit 1**: What becomes easier or what capability we gain
- **Benefit 2**: Additional positive outcome

### Negative Consequences

- **Trade-off 1**: What becomes harder or what we're giving up
  - **Mitigation**: How we'll address this limitation
- **Trade-off 2**: Additional constraint or limitation
  - **Mitigation**: How we'll handle this

### Neutral Consequences

- What stays the same
- New considerations that emerge
- Operational changes that are neither positive nor negative

## Implementation Notes

Optional section for implementation details, milestones, or technical specifics.

Key technical details, gotchas, or migration steps:

```text
// Example code if relevant
```

**Migration Steps** (if applicable):
1. Step one
2. Step two
3. Step three

**Timeline** (if applicable):
- Phase 1: Description (date range)
- Phase 2: Description (date range)

## Related Documents

- [Related ADR](../adr/adr-XXX)
- [Related RFC](../rfcs/rfc-XXX)
- [External Resource](https://example.com)

## Revision History

Optional section to track major changes to this ADR:

- YYYY-MM-DD: Initial draft (Author Name)
- YYYY-MM-DD: Accepted after review (Deciders)
- YYYY-MM-DD: Amended with clarification (Author Name)
