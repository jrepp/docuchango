---
id: "rfc-903"
slug: rfc-903-heading-after-code-block
title: "RFC-FAIL-903: Heading Immediately After Code Block"
date: "2025-10-16"
tags:
  - test
  - validation
---

## Overview

This document has headings immediately after code blocks.

## Example

```go
func Example() {
    return "code"
}
```
## This Heading Has No Blank Line Above

This is a common mistake that causes rendering issues.

```python
def another_example():
    pass
```
### Another Heading Without Space

This should also fail validation.

## Correct Example

```bash
echo "proper spacing"
```

## This Is Correct

The blank line above the heading is proper.
