---
id: "adr-903"
slug: adr-903-missing-newline-after-code-block
title: "ADR-FAIL-903: Missing Newline After Code Block"
date: "2025-10-16"
status: "accepted"
deciders: "Test"
tags:
  - test
  - validation
---

## Overview

This document demonstrates INCORRECT formatting - missing blank lines after closing fences.

## Example 1: No Blank Line After Code

```go
func BadExample() {
    return "No blank line after this block"
}
```
This text immediately follows the closing fence - INVALID!

## Example 2: Another Violation

```sql
SELECT * FROM users;
```
Another line without proper spacing.

## Example 3: Correct Usage

```bash
echo "This one is correct"
```

Proper blank line above.

## Conclusion

This document should FAIL validation due to missing blank lines after code blocks.
