---
id: "adr-001"
slug: adr-001-valid-code-blocks
title: "ADR-001: Valid Code Blocks Test"
date: "2025-10-16"
status: "accepted"
deciders: "Test Team"
tags:
  - test
  - validation
---

## Context

This document tests valid code block fencing.

### Go Code Example

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```

### SQL Query Example

```sql
SELECT id, name, created_at
FROM users
WHERE status = 'active'
ORDER BY created_at DESC;
```

### ASCII Diagram

```text
┌─────────────────────────────────┐
│        Architecture             │
│  ┌──────────┐    ┌──────────┐  │
│  │  Client  │───▶│  Server  │  │
│  └──────────┘    └──────────┘  │
└─────────────────────────────────┘
```

### YAML Configuration

```yaml
name: Test Workflow
on:
  push:
    branches:
      - main
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

### Bash Commands

```bash
#!/bin/bash
npm install
npm test
```

## Decision

All code blocks properly fenced with language specifiers.
