---
id: adr-001
title: Adopt docs-cms for Documentation Management
status: Accepted
created: 2025-10-27
deciders: Project Team
tags:
- architecture
- documentation
- tooling
project_id: example-project
doc_uuid: 550e8400-e29b-41d4-a716-446655440000
---

# ADR-001: Adopt docs-cms for Documentation Management

## Context

Engineering decisions and product requirements were split across pull requests and chat threads. Teams needed one versioned place in git where humans and coding agents can read and validate project memory.

## Decision

We adopt `docs-cms` with automated validation in CI. Decisions live in `adr/`, proposals in `rfcs/`, product requirements in `prd/`, and status notes in `memos/`.

## Consequences

- Every document carries validated frontmatter and a stable ID.
- Agents can ground answers in [ADR-002](./adr-002-agent-collaboration-workflow.md) and trace requirements from [PRD-001](../prd/prd-001-doc-export.md) to [RFC-002](../rfcs/rfc-002-cli-export-pipeline.md).
- We would reconsider this layout if the repository splits into independent repositories with separate release cadences.
