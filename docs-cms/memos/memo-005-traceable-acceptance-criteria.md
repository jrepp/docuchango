---
author: Engineering Team
created: 2026-10-20
doc_uuid: b8f24ea2-7464-4b43-8d31-c82b62e160af
id: memo-005
project_id: docuchango
tags: [documentation, requirements, templates, testing]
title: Traceable Requirements and Acceptance Criteria
---

# Memo-005: Traceable Requirements and Acceptance Criteria

## Context

The template system described in [RFC-001](../rfcs/rfc-001-document-template-system.md)
provides standard document structure. A comparison with PRD, RFC, technical-AC,
and review examples highlighted a gap:
the bundled PRD has requirement IDs but no acceptance scenarios, and the bundled
RFC has no explicit requirements-coverage or verification section.

The useful lesson is connecting requirements, observable behavior, technical
contracts, and tests. The examples also show pitfalls: ambiguous alternatives,
speculative constraints, and inconsistent measurement or release scope.

## Implementation scope

The user requested implementation of the template enhancement proposal. Both
bundled and detailed PRD/RFC templates now prompt stable criterion references,
failure/boundary behavior, measurement conditions, and owned open questions.
The detailed FRD reuses its existing Given / When / Then format with criterion IDs.

The [authoring guide and worked example](../../docs/ACCEPTANCE_CRITERIA.md) connect
an illustrative read-only inspection requirement to design and verification.
That example does not decide CLI defaults or accept the separate
[read-only validation proposal](../rfcs/rfc-004-read-only-validate.md).

## Maintenance boundaries

- These are optional authoring prompts, not mandatory frontmatter or new schemas.
- No validator behavior or finding registry entries change.
- Keep one authoritative requirement and reference it from technical criteria.
- Label new decisions as proposed; do not fill missing decisions with assumptions.
- Keep the bundled guidance self-contained because `init` distributes it.
- Keep detailed templates aligned without requiring identical document length.
- Existing documents need no migration; use the guidance when authoring or revising.

## Verification approach

The initialization content test checks that generated PRD/RFC templates include
acceptance criteria, coverage, and verification guidance. Existing initialization
tests cover custom paths and template distribution. Documentation validation checks
the project memo and links; it does not assess the semantic quality of criteria.

Evaluate usefulness through real reviews: did the guidance reveal missing behavior
or decisions, and was the writing effort proportionate? Do not assume quantified
productivity gains or treat a filled coverage table as passing test evidence.
