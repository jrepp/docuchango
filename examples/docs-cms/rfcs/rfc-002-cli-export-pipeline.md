---
author: Platform Engineering
created: 2025-10-27
doc_uuid: 8c9d0e1f-2a3b-4456-8789-abcdef012345
id: rfc-002
implements:
- prd-001
- prd-002
project_id: example-project
status: Proposed
tags:
- audit
- export
- rfc
title: CLI Export Pipeline and Local Audit Summary
---

# RFC-002: CLI Export Pipeline and Local Audit Summary

## Summary

Implement the archive builder from [PRD-001](../prd/prd-001-doc-export.md) and the local JSON audit record from [PRD-002](../prd/prd-002-audit-trail.md). Because both PRDs define `FR-1` and `AC-1`, references in this RFC use `prd-001::` and `prd-002::` qualifiers.

## Requirements Coverage

The range `prd-001::AC-1 through prd-001::AC-4` covers all defined export criteria (`AC-1`, `AC-2`, and `AC-4`, with `AC-3` intentionally unused).

| Source requirement | Acceptance criterion | Disposition | Design section | Verification |
|--------------------|----------------------|-------------|----------------|--------------|
| prd-001::FR-1, prd-001::FR-2 | prd-001::AC-1 through prd-001::AC-4 | Covered | Archive Writer | CLI integration test with byte comparison |
| prd-001::NFR-1 | — | Covered (benchmark suite) | Archive Writer | Warm-cache benchmark on 100-doc fixture |
| prd-002::FR-1 | prd-002::AC-1, prd-002::AC-1.1 | Covered | Local Audit Writer | JSON schema and exit-code integration test |

## Archive Writer

Write archive entries in sorted path order with normalized timestamps, filter by frontmatter status before staging files, and write to a temporary file before atomic rename (`prd-001::AC-1 through prd-001::AC-4`).

## Local Audit Writer

Emit the structured JSON summary required by `prd-002::AC-1` and `prd-002::AC-1.1`. Remote webhook streaming (`prd-002::FR-2` / `prd-002::AC-2`) is handled separately by [RFC-003](./rfc-003-audit-stream.md).
