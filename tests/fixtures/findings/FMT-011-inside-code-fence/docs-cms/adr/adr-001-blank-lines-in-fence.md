---
id: adr-001
title: "ADR-001: Blank Lines Inside A Code Fence"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: 7d41b2c8-9e3a-4c15-b8f2-6a0d5e1c9b43
---

# ADR-001: Blank Lines Inside A Code Fence

A backtick fence whose sample output has a deliberate gap in it.

```text
first line




last line
```

A tilde fence with the same gap.

~~~text
first line



last line
~~~

The gaps above are content and are neither reported nor collapsed.
