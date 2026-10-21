---
title: Title Goes Here
status: Draft
author: Product Team  # git config user.name
created: YYYY-MM-DDTHH:MM:SSZ  # python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
target_release: v1.0.0
tags: [feature, product]
id: prd-000  # lowercase prd-XXX format matching filename
project_id: my-project  # from docs-project.yaml
doc_uuid: 00000000-0000-4000-8000-000000000000  # python -c "import uuid; print(uuid.uuid4())"
---

# Executive Summary

Brief overview of the product feature or initiative.

# Problem Statement

What problem are we solving? Who has this problem? Why is it important?

# Goals and Objectives

## Primary Goals

- Goal 1
- Goal 2

## Success Metrics

- Metric 1: Target
- Metric 2: Target

# User Stories

## As a [user type]

- I want to [action]
- So that [benefit]

## As a [another user type]

- I want to [action]
- So that [benefit]

# Requirements

Keep requirement and acceptance-criterion IDs stable when adding new items.
Use only the detail needed for this change; a small fix may need one requirement
and a few scenarios. These are authoring prompts, not validation requirements.

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Requirement description | Must Have |
| FR-2 | Requirement description | Should Have |
| FR-3 | Requirement description | Nice to Have |

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Performance requirement | < 200ms response time |
| NFR-2 | Scalability requirement | 10,000 concurrent users |

For each target, state its source or rationale and how it will be measured:
metric/percentile, workload, dataset, environment, and observation period.
Do not invent a target to fill the table; record unknown targets as open questions.
Test pass rates are delivery evidence, not measures of user or business value.

## Acceptance Criteria

Reference a requirement ID and describe observable behavior, not implementation
tasks. Given / When / Then is one useful format; equivalent testable prose is fine.

### AC-1: [Observable outcome]

Requirement: FR-1

- **Given** [initial state and relevant preconditions]
- **When** [action or event]
- **Then** [observable result that distinguishes success from failure]
- **And** [what must remain unchanged, if relevant]

Include failure and boundary scenarios where relevant: invalid or missing input,
empty results, partial failure, retries, concurrency, and compatibility. State
allowed side effects and recovery behavior rather than just “returns an error.”
Keep the product outcome here; the RFC references these criteria and adds the
technical contract and verification method. Reference the requirement instead
of maintaining competing copies of it in several documents.

Acceptance criteria define feature behavior. Keep shared Definition of Done items
(review completed, lint passes, release notes written) separate; they do not prove
that the user outcome holds. When revising criteria, preserve conditions,
exceptions, negative constraints, and IDs. Ask whether the rewrite could pass
while the original promise fails; do not move required outcomes into Given.

# Design

## User Interface

Mockups, wireframes, or descriptions of the user interface.

## Technical Architecture

High-level technical approach and system architecture.

## Data Model

Key data entities and relationships.

# Out of Scope

What are we explicitly NOT doing in this release?

- Out of scope item 1
- Out of scope item 2

# Dependencies

What other systems, teams, or features does this depend on?

- Dependency 1
- Dependency 2

# Timeline

| Milestone | Date | Status |
|-----------|------|--------|
| Design Complete | 2025-02-01 | Not Started |
| Development Start | 2025-02-15 | Not Started |
| Testing | 2025-03-01 | Not Started |
| Release | 2025-03-15 | Not Started |

# Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Risk 1 | High | Mitigation strategy |
| Risk 2 | Medium | Mitigation strategy |

# Open Questions

| Question | Owner | Blocking impact | Resolution or next step |
|----------|-------|-----------------|-------------------------|
| [Decision needed] | [Decision maker] | [Blocks AC-1, or non-blocking] | [Pending / agreed answer and source] |

Separate agreed requirements from proposed decisions. Do not silently turn an
assumption into a requirement. Choose a deterministic outcome before implementing
a blocked criterion, or explicitly define the allowed outcomes and invariant.

# Appendix

Additional information, research, or supporting materials.

Distinguish observations and their sources from interpretations and recommendations.
Name material assumptions, contrary evidence, and the limits of the sources read.
Do not turn examples, reviewer preferences, or inferred needs into agreed scope.
