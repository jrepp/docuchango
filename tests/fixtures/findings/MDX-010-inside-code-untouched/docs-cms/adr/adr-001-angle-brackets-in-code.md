---
id: adr-001
title: "ADR-001: Angle Brackets In Code"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee
---

# ADR-001: Angle Brackets In Code

Every placeholder below lives inside code, so MDX never parses it as JSX and
MDX-010 must leave all of it exactly as written.

Inline code carries one: set `<token>` in the header, and `</token>` closes it.

A backtick fence:

```bash
curl -H "Authorization: Bearer <token>" https://example.com
```

A tilde fence, which the fence scanner tracks separately:

~~~text
<agentName> writes to <log-name>
~~~

An already escaped placeholder in prose stays escaped and is never
double-escaped: &lt;token&gt;.
