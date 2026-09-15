---
id: adr-001
title: "ADR-001: CRLF With An Unfixable Finding"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: cccccccc-cccc-4ccc-8ccc-cccccccccccc
---

# ADR-001: CRLF With An Unfixable Finding

Every line in this file ends with CRLF, which FMT-010 repairs, and the file
also links to [a sibling that does not exist](./adr-999-does-not-exist.md),
which nothing repairs. Under the default atomic run the CRLF rewrite is
therefore withheld and the file is restored to its original bytes.
