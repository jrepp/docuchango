---
id: prd-002
title: Validation Audit Trail
status: In Review
author: Compliance Team
created: 2025-10-27
target_release: v1.3.0
tags:
- audit
- compliance
- prd
project_id: example-project
doc_uuid: 7b8c9d0e-1f2a-4345-8678-9abcdef01234
---

# PRD-002: Validation Audit Trail

## Problem Statement

Regulated projects need a structured record of each validation and export run, plus an optional live stream for external collectors.

## Requirements

| ID | Requirement | Scope |
|----|-------------|-------|
| FR-1 | Record a structured JSON audit summary for every export or validation run | In scope |
| FR-2 | Stream audit events to a remote webhook collector | In scope |
| FR-3 | Redact custom secret patterns before writing audit logs | Out of scope (handled by log shipper) |

## Acceptance Criteria

### AC-1: Emit JSON audit record for export runs

Requirement: FR-1

- **Given** an export invocation
- **When** the run completes
- **Then** a JSON record with the commit SHA, document count, and exit code is written

### AC-1.1: Include finding IDs when validation fails

Requirement: FR-1

- **Given** a validation run with remaining findings
- **When** the audit summary is written
- **Then** the summary lists each finding ID and affected file path

### AC-2: Deliver audit event to webhook collector

Requirement: FR-2

- **Given** a configured webhook endpoint
- **When** a validation run finishes
- **Then** the audit payload is sent with a bounded retry policy
