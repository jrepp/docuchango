---
created: 2026-09-18
deciders: Engineering Team
doc_uuid: 1e81a4db-f780-47df-9822-cc59eaef4a75
id: adr-004
project_id: docuchango
status: Proposed
tags: [automation, releases]
title: Automated Releases and RC Staging on Main
---

# ADR-004: Automated Releases and RC Staging on Main

## Decision

Use `main` as the integration and release-candidate (RC) staging branch.
Releasable changes on `main` produce RCs through the release workflow.
Stable releases require an explicit promotion through that workflow.

Releases must be created through the automated release workflow, which owns
version bumps, tags, release creation, and publication.

[PUBLISHING.md](../../PUBLISHING.md) governs publishing, including workflow
invocation, promotion, verification, and recovery. Follow that guide for all
release operations and maintain operational details there.

## Why

RC staging lets changes be tested before stable promotion. Workflow-based
releases keep version metadata, published packages, and release assets
consistent and provide an auditable record of publication.

## Consequences

Stable promotion is a deliberate maintainer action executed by automation.
Release procedures have one authoritative home in `PUBLISHING.md`.
