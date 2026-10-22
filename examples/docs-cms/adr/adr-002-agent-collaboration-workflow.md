---
id: adr-002
title: Define Agent Collaboration Workflow with docs-cms
status: Accepted
created: 2025-10-27
deciders: Project Team and AI Agents
tags:
- ai-agents
- architecture
- collaboration
- workflow
project_id: example-project
doc_uuid: 7c9e6679-7425-40de-944b-e07fc1f90ae7
---

# ADR-002: Define Agent Collaboration Workflow with docs-cms

## Context

Coding agents frequently propose designs and update documentation. Without clear rules, agents might mark unreviewed decisions as accepted or invent requirements to fill templates.

## Decision

Agents read `docs-cms/` before acting, cite document IDs in responses, author new ADRs with `status: Proposed`, and run `docuchango validate` before committing. When working with PRDs and RFCs, agents preserve requirement IDs (`FR-n`, `AC-n`) and record unknown targets as open questions rather than guessing.

## Consequences

- Human reviewers retain approval authority over architectural and scope decisions.
- Requirement coverage stays checkable across [PRD-001](../prd/prd-001-doc-export.md), [PRD-002](../prd/prd-002-audit-trail.md), and their implementing RFCs.
