---
title: Title Goes Here
status: Draft
author: Engineering Team  # git config user.name
created: YYYY-MM-DDTHH:MM:SSZ  # python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
tags: [rfc, design]
id: rfc-000  # lowercase rfc-XXX format matching filename
project_id: my-project  # from docs-project.yaml
doc_uuid: 00000000-0000-4000-8000-000000000000  # python -c "import uuid; print(uuid.uuid4())"
---

# Summary

Brief one-paragraph explanation of the proposal.

# Motivation

Why are we doing this? What use cases does it support? What is the expected outcome?

# Detailed Design

This is the bulk of the RFC. Explain the design in enough detail for somebody familiar with the system to understand, and for somebody familiar with the code to implement.

## Requirements Coverage

Reference the parent PRD and its requirement/acceptance IDs. If there is no PRD,
state the requirements and their rationale locally. Keep IDs stable; identify
deferred requirements explicitly rather than silently omitting them.

| Source requirement | Acceptance criterion | Design section | Verification |
|--------------------|----------------------|----------------|--------------|
| [PRD reference / FR-1] | AC-1 | [Relevant section] | [Test level and observable evidence] |

Use a brief list instead of a table for small changes. A link to a test plan is
planned coverage, not proof that a test exists or has passed.

## API Changes

If applicable, describe any API changes.

## Data Model Changes

If applicable, describe any data model changes.

## Migration Strategy

How will we migrate existing systems/data?

## Technical Acceptance Criteria

For each source criterion, specify the technical contract needed to satisfy it:
API or CLI responses, error behavior, persistence, compatibility, and recovery.
Identify the source requirement or decision; label new decisions as proposed.
Do not repeat the PRD as a second source of truth or prescribe incidental helper
names and file layouts as acceptance requirements.

### Technical contract for AC-1

- Source: [requirement or agreed decision]
- Given [state], when [action], then [observable technical result].
- On failure: [response, permitted side effects, preserved state, recovery].
- Verification: [unit / integration / CLI / API / benchmark / manual evidence].

Select relevant boundaries, retry/concurrency cases, and compatibility scenarios.
For performance targets, state the metric/percentile, workload, dataset,
environment, measurement period, and rationale. Leave unknown targets explicit.

## Verification Plan

Map criteria to tests or other evidence. Explain what incorrect behavior each
check detects. Verify internal constraints at the appropriate test level rather
than requiring every property to be observed through an end-to-end test.
Keep execution results with the test or release record; do not equate a filled
coverage table with passing tests or demonstrated user value.

# Drawbacks

Why should we *not* do this? What are the costs and risks?

# Alternatives

What other designs have been considered? What is the impact of not doing this?

## Alternative 1

Description and comparison.

## Alternative 2

Description and comparison.

# Adoption Strategy

How will existing users adopt this change? Do we need documentation updates? Training?

# Unresolved Questions

What parts of the design are still TBD? What questions need to be resolved during implementation?

| Question | Owner | Blocking impact | Resolution or next step |
|----------|-------|-----------------|-------------------------|
| [Decision needed] | [Decision maker] | [Affected criterion, or non-blocking] | [Pending / agreed answer and source] |

Do not invent requirements to close gaps. “Warn or reject” needs a decision unless
both outcomes intentionally satisfy a stated invariant. Unblocked work may proceed
while unrelated questions remain open.

# Future Possibilities

What related future work might build on this RFC?
