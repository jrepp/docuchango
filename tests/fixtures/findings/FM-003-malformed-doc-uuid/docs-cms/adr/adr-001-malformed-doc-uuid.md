---
id: adr-001
title: "ADR-001: Malformed Document UUID"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: not-a-valid-uuid
---

# ADR-001: Malformed Document UUID

The `doc_uuid` above is not a UUID, so the schema validator rejects it.
