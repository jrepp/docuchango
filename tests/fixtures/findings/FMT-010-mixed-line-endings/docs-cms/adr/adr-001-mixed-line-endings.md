---
id: adr-001
title: "ADR-001: Mixed Line Endings"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb
---

# ADR-001: Mixed Line Endings

Line endings in this file are mixed: some lines end with CRLF, most end
with LF, and this one ends with a bare carriage return instead.A lone CR is normalized to LF too, so the whole file ends up LF and the
rewrite stays lossless: only the terminators change.
