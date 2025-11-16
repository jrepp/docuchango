---
id: "rfc-XXX"  # Use sequential numbering: rfc-001, rfc-002, etc.
slug: rfc-XXX-brief-description
title: "RFC Title"
status: Draft  # Valid values: Draft, In Review, Accepted, Rejected, Implemented
created: YYYY-MM-DD  # Generate: date +%Y-%m-%d  OR  python -c "from datetime import date; print(date.today())"  OR  auto-set with: docuchango fix timestamps
updated: YYYY-MM-DD  # Last modified date - auto-updated with: docuchango fix timestamps
author: Author Name  # Generate: git config user.name
tags: ["tag1", "tag2", "md"]  # Format: lowercase-with-dashes, e.g., ["api-design", "performance"]
project_id: "your-project-id"
doc_uuid: "00000000-0000-4000-8000-000000000000"  # Generate: uuidgen  OR  python -c "import uuid; print(uuid.uuid4())"
---

# RFC-XXX: Title

## Summary

Brief one-paragraph description of the proposed change.

## Motivation

Why are we doing this? What use cases does it support? What problems does it solve?

### Goals

- Goal 1
- Goal 2
- Goal 3

### Non-Goals

- What this proposal explicitly does not address
- Future work that might be related but is out of scope

## Proposal

Detailed description of the proposal.

### Architecture

High-level architecture diagram and explanation.

### API Design

```proto
// Proposed API or interface
```

### Data Model

Describe any data structures, schemas, or persistence requirements.

### Implementation

Key implementation details, technical approach, dependencies.

## Alternatives Considered

### Alternative 1

Description and why it was not chosen.

### Alternative 2

Description and why it was not chosen.

## Trade-offs

- Trade-off 1
- Trade-off 2

## Security Considerations

Security implications and how they are addressed.

## Testing Plan

How will this be tested? What are the test scenarios?

## Migration/Rollout Plan

How will this be deployed? Any migration steps required?

## Timeline

- Phase 1: Description (date range)
- Phase 2: Description (date range)
- Phase 3: Description (date range)

## Open Questions

1. Question 1?
2. Question 2?

## References

- [Related ADR](../adr/adr-XXX)
- [Related RFC](../rfcs/rfc-XXX)
- External documentation
