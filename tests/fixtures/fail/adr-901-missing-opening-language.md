---
id: "adr-fail-001"
slug: adr-fail-001-missing-opening-language
title: "ADR-FAIL-001: Missing Opening Language"
date: "2025-10-16"
status: "accepted"
deciders: "Test Team"
tags:
  - test
---

## Context

This should FAIL: opening fence without language.

### Code Block Without Language

```
package main

func main() {
    println("Missing language specifier")
}
```

## Decision

The validator should catch the bare opening fence.
