---
title: Title Goes Here
status: Draft
author: Engineering Team  # git config user.name
created: YYYY-MM-DDTHH:MM:SSZ  # python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
tags: [rfc, design]
id: rfc-000  # lowercase rfc-XXX format matching filename
project_id: my-project  # from docs-project.yaml
implements: []  # optional: ids of the PRDs/FRDs this RFC covers, e.g. [prd-001]
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

For long-running work, identify the source baseline (path plus commit, version,
or date where needed). Resolve ID ranges against actual definitions; repeated
references are valid, but duplicate definitions or unknown IDs need clarification.

| Source requirement | Acceptance criterion | Disposition | Design section | Verification |
|--------------------|----------------------|-------------|----------------|--------------|
| [PRD reference / FR-1] | AC-1 | [Covered / deferred / unresolved] | [Relevant section] | [Test level and observable evidence] |

Covered means a mechanism and observable result address the requirement. Give a
reason and agreement source for a deferral; a proposed deferral stays unresolved.
Accounted for is not the same as covered.

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

Separate feature acceptance from shared Definition of Done checks such as lint and
peer review. Size implementation steps as reviewable outcomes, each with its own
verification. Name existing behavior that only needs verification, and attach
blockers to affected deliverables rather than automatically blocking the whole plan.

## Evidence and Review

Distinguish verified current behavior, proposed changes, and assumptions. Check
named interfaces, paths, defaults, and enum values at their authoritative sources;
mark not-yet-built behavior as planned. Record evidence limitations and what would
cause a consequential decision to be reconsidered.

Review findings should cite the claim, governing evidence, and consequence.
Separate defects from suggestions and inherited issues from introduced ones.
Before calling something missing, check scope, deferrals, sibling documents, and
source freshness. Recheck a correction before calling it resolved.

## Change Impact (when revising an existing design)

| Changed decision | Affected criterion/document/test | Follow-up | Owner and state |
|------------------|----------------------------------|-----------|-----------------|
| [Decision and reason] | [Existing reference] | [Update / verify / proposed follow-up] | [Owner; pending / verified / unresolved] |

Preserve unrelated decisions and completed-work history. An impact proposal does
not mean dependents were updated. Identify follow-up work without silently
reopening completed items. Before handoff, ask a reader to plan an implementation
or recovery task from the RFC alone; record guesses and check links from the
intended shared location.

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
