---
id: "adr-001"
title: "Use Pydantic for Frontmatter Schema Validation"
status: Accepted
date: 2025-01-26
deciders: Engineering Team
tags: ["pydantic", "validation", "schema", "architecture"]
project_id: "docuchango"
doc_uuid: "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"
---

# ADR-001: Use Pydantic for Frontmatter Schema Validation

## Decision

Use Pydantic v2 for validating frontmatter schemas in markdown documents.

## Why

Different doc types (ADR, RFC, Memo) need different required fields. Pydantic gives us:
- Type safety with clear error messages
- Easy custom validators (UUID format, lowercase tags)
- Fast validation (Rust core)
- Clean Python API

```python
class ADRFrontmatter(BaseModel):
    status: Literal["Proposed", "Accepted", "Deprecated", "Superseded"]
    date: datetime.date
    deciders: str = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not re.match(r"^adr-\d{3}$", v.lower()):
            raise ValueError("ID must be 'adr-XXX' format")
        return v.lower()
```

## Alternatives

**Manual dict checks**: Too verbose, error-prone, bad error messages

**JSON Schema**: More complex, less Pythonic, harder to write validators

**dataclasses**: Lightweight but needs more boilerplate for validation

## Result

- Schemas are easy to read and maintain
- Users get clear validation errors
- Adding new doc types is simple
- Trade-off: One more dependency to maintain
