---
id: "adr-fail-002"
slug: adr-fail-002-markdown-fence-corruption
title: "ADR-FAIL-002: Markdown Fence Corruption"
date: "2025-10-16"
status: "accepted"
deciders: "Test Team"
tags:
  - test
---

## Context

This should FAIL: closing fence with 'markdown' creates nested block.

### ASCII Diagram

```text
┌─────────────────┐
│    Diagram      │
└─────────────────┘
```markdown
### Next Section

This creates a markdown code block instead of rendering as markdown.
