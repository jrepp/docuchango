---
id: "rfc-001"
slug: rfc-001-nested-code-blocks
title: "RFC-001: Nested Code Blocks Test"
date: "2025-10-16"
status: "proposed"
tags:
  - test
  - rfc
---

## Overview

Testing multiple code blocks in sequence.

### Example 1: Function Definition

```go
func ProcessRequest(ctx context.Context, req *Request) (*Response, error) {
    if err := validate(req); err != nil {
        return nil, err
    }
    return &Response{Status: "ok"}, nil
}
```

### Example 2: Database Query

```sql
CREATE TABLE deployments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Example 3: Protobuf Definition

```protobuf
syntax = "proto3";

message Request {
    string id = 1;
    string name = 2;
}

message Response {
    string status = 1;
}
```

## Conclusion

All blocks properly closed and opened.
