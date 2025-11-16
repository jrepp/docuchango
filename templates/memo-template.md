---
id: memo-XXX  # Use sequential numbering: memo-001, memo-002, etc.
slug: memo-XXX-brief-description
title: Memo Title
status: Draft  # Valid values: Draft, Published, Archived
created: YYYY-MM-DD  # Generate: date +%Y-%m-%d  OR  python -c "from datetime import date; print(date.today())"  OR  auto-set with: docuchango fix timestamps
updated: YYYY-MM-DD  # Last modified date - auto-updated with: docuchango fix timestamps
author: Author Name  # Generate: git config user.name
tags:  # Format: lowercase-with-dashes
  - tag1
  - tag2
  - tag3
project_id: your-project-id
doc_uuid: 00000000-0000-4000-8000-000000000000  # Generate: uuidgen  OR  python -c "import uuid; print(uuid.uuid4())"
---

# Memo Title

## Executive Summary

Brief summary of key points (2-3 sentences).

## Context

Background information and context for this memo.

## Key Points

### Point 1

Details about point 1.

### Point 2

Details about point 2.

### Point 3

Details about point 3.

## Technical Details

```text
Diagrams, code samples, or technical specifics
```

## Analysis

Detailed analysis or findings.

## Recommendations

1. Recommendation 1
2. Recommendation 2
3. Recommendation 3

## Action Items

- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3

## References

- [Related Document 1](./doc1.md)
- [Related Document 2](./doc2.md)
- External reference
