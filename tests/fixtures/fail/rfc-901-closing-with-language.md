---
id: "rfc-fail-001"
slug: rfc-fail-001-closing-with-language
title: "RFC-FAIL-001: Closing Fence With Language"
date: "2025-10-16"
status: "proposed"
tags:
  - test
---

## Overview

This should FAIL: closing fence has language specifier.

### Valid Opening

```go
func Example() {
    return "test"
}
```go

The closing fence above has 'go' but should be bare.
