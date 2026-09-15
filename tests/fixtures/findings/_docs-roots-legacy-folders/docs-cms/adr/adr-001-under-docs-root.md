---
id: adr-001
title: "ADR-001: Legacy Folder Under A Docs Root"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: dddddddd-dddd-4ddd-8ddd-dddddddddddd
---

# ADR-001: Legacy Folder Under A Docs Root

This line ends with two spaces.  

The config names `adr` through `adr_dir` rather than `doc_types`, and puts it
under `docs_roots: [docs-cms]`. Discovery must find this file, so the trailing
whitespace above has to be reported and repaired.
