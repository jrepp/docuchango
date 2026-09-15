---
id: adr-002
title: "ADR-002: Accepted Date Forms"
status: Accepted
created: 2026-01-02T09:35:12Z
updated: 2026-01-03
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee
---

# ADR-002: Accepted Date Forms

Both forms FM-011 accepts appear here: a `Z` timestamp, which YAML resolves to
an aware datetime, and a bare date, which it resolves to a date object.
Neither may be reported.
