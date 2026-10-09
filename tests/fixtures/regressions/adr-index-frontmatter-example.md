---
id: adr-index
title: Architecture Decision Records
sidebar_label: ADR Index
deciders: Core Team
author: Core Team
tags: []
doc_uuid: ced28ed9-d3c5-4206-ab17-0169148d003a
project_id: my-project
---

# Architecture Decision Records (ADRs)

This directory contains records of architectural decisions.

## Adding New ADRs

1. Copy `000-template.md` to `NNN-short-title.md`
2. Use YAML frontmatter for metadata
3. Update status when accepted

**Frontmatter Format:**

```markdown
---
title: "ADR-XXX: Descriptive Title"
status: Accepted
created: 2025-10-08T15:17:02Z
date: 2025-10-08
deciders: Core Team
tags: [architecture, backend]
---
```

## ADR Lifecycle

```text
Proposed → Reviewed → Accepted → Implemented
```
