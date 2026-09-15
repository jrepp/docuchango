---
id: adr-099
title: "ADR-099: Archived Superseded Decision"
status: Superseded
created: 2025-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: 66666666-6666-4666-8666-666666666666
---

# ADR-099: Archived Superseded Decision

Nested in `adr/archive/`. Its frontmatter `id` does not match its filename,
and it reuses the `doc_uuid` of `adr-005-original.md`. With
`structure.scan_subfolders: true` this file is scanned like a top-level
document, so both problems are reported.
