---
id: "adr-002"
slug: adr-002-code-block-with-newlines
title: "ADR-002: Code Blocks with Proper Newlines"
date: "2025-10-16"
status: "accepted"
deciders: "Test"
tags:
  - test
  - validation
---

## Overview

This document demonstrates proper code block formatting with blank lines after closing fences.

## Example 1: Go Code

```go
func Example() {
    return "This has a blank line after"
}
```

The blank line above prevents markdown confusion.

## Example 2: SQL Query

```sql
SELECT * FROM users WHERE active = true;
```

Another section with proper spacing.

## Example 3: Multiple Blocks

```bash
echo "First block"
```

Text between blocks.

```python
print("Second block")
```

More text after the final block.

## Conclusion

All code blocks have proper blank lines after closing fences.
