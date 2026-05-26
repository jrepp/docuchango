---
# REQUIRED FIELDS - All must be present for validation to pass
id: "adr-NNN-aNN"  # Amendment format: "adr-NNN-aNN" where NNN is the parent ADR number
                   # and NN is the amendment sequence (e.g., "adr-026-a1", "adr-026-a2")
slug: adr-NNN-amendment-NN-brief-description  # URL-friendly slug (lowercase-with-dashes)
title: "ADR-NNN Amendment NN: Brief Title"  # (e.g., "ADR-026 Amendment 01: Raise Table Cap to 8")
status: Proposed  # Valid values: Proposed, Accepted, Deprecated, Superseded, Implemented
created: YYYY-MM-DD  # ISO 8601 format - date amendment was first created, DO NOT CHANGE after initial creation
                     # Generate: date +%Y-%m-%d  OR  python -c "from datetime import date; print(date.today())"
author: Your Name  # Person or team who wrote this amendment
deciders: Your Name  # Team or person who approved the amendment
tags: ["amendment", "example-tag"]  # Always include "amendment"; add relevant topic tags
project_id: "your-project-id"  # Project identifier from docs-project.yaml
doc_uuid: "00000000-0000-4000-8000-000000000000"  # UUID v4 - Generate: uuidgen  OR  python -c "import uuid; print(uuid.uuid4())"
amends: "adr-NNN"  # id of the ADR being amended (e.g., "adr-026")
---

# ADR-NNN Amendment NN: Brief Title

> **Amends**: [ADR-NNN: Original Title](adr-NNN-original-filename.md)
> ADR-NNN remains authoritative except where explicitly overridden below.

## Context

What has changed since ADR-NNN was accepted that makes this amendment necessary?

Include:
- The specific gap, new requirement, or discovered constraint
- Why the original decision no longer fully applies in this area
- What is blocked or impacted without this amendment

## What This Amendment Changes

Describe precisely what is being changed. Reference the specific section or rule
from the original ADR.

**Before (ADR-NNN):**
> Quote or summarise the original decision being amended.

**After (this amendment):**
The new decision, rule, or constraint that replaces it.

## What Remains Unchanged

Explicitly list what is NOT affected by this amendment. This prevents readers
from assuming the entire original ADR is invalidated.

- Original decision X remains in force
- Constraint Y is unchanged
- Implementation guidance Z still applies

## Rationale

Why is this amendment the right approach?

### Why Not Supersede the Full ADR?

This change is scoped to [specific aspect] and does not invalidate the rest of
ADR-NNN. A full supersession would discard valid context and decisions that
remain correct.

### Alternatives Considered

#### Alternative 1: [Name]

Description of this alternative.

**Rejected because**: Specific reason.

#### Alternative 2: [Name]

Description of this alternative.

**Rejected because**: Specific reason.

## Consequences

### Positive Consequences

- **Benefit 1**: What becomes possible or unblocked
- **Benefit 2**: Additional positive outcome

### Negative Consequences

- **Trade-off 1**: What becomes harder or what we give up
  - **Mitigation**: How we address this

### Neutral Consequences

- What stays the same from ADR-NNN

## Acceptance Criteria

List what must be true before this amendment can be marked Implemented:

1. [Specific measurable criterion]
2. [Specific measurable criterion]

## Implementation Notes

Optional section for implementation specifics required by the amended decision.

```text
// Example code or schema if relevant
```

## Related Documents

- [ADR-NNN: Original Decision](adr-NNN-original-filename.md)
- [Related RFC or ADR if applicable]

## Revision History

- YYYY-MM-DD: Initial draft (Author Name)
- YYYY-MM-DD: Accepted after review (Deciders)
