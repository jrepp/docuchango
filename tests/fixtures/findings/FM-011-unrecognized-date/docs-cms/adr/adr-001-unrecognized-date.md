---
id: adr-001
title: "ADR-001: Unrecognized Date Format"
status: Accepted
created: 2024-1-5
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: dddddddd-dddd-4ddd-8ddd-dddddddddddd
---

# ADR-001: Unrecognized Date Format

The `created` value above drops the zero padding, so YAML leaves it a plain
string and FM-006 cannot identify a format to rewrite it from. FM-011 reports
it in the dry run and in the fixing run alike.
