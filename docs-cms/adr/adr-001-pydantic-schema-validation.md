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

## Status

Accepted

## Context

Docuchango needs to validate YAML frontmatter in markdown documents against strict schemas. Different document types (ADR, RFC, Memo, PRD, etc.) have different required fields and validation rules. We need a solution that provides:

- Strong type validation
- Clear error messages
- Field-level validators
- Python 3.9+ compatibility
- Good developer experience

Options considered:

1. **Manual validation with dict checks** - Simple but error-prone and verbose
2. **JSON Schema with jsonschema library** - Industry standard but complex for simple cases
3. **Pydantic v2** - Modern Python validation with excellent DX
4. **dataclasses with custom validators** - Lightweight but requires more boilerplate

## Decision

We will use **Pydantic v2** for all frontmatter schema validation.

## Rationale

### Advantages

1. **Type Safety**: Pydantic provides runtime type checking with excellent error messages
2. **Field Validators**: Easy to write custom validators (e.g., UUID format, tag lowercase check)
3. **Developer Experience**: Clean, Pythonic API that's easy to maintain
4. **Documentation**: Schemas serve as living documentation
5. **Ecosystem**: Wide adoption, active development, excellent IDE support
6. **Performance**: Pydantic v2 uses Rust core for fast validation

### Example Schema

```python
class ADRFrontmatter(BaseFrontmatter):
    """ADR (Architecture Decision Record) frontmatter schema."""

    status: Literal["Proposed", "Accepted", "Deprecated", "Superseded"]
    date: datetime.date
    deciders: str = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not re.match(r"^adr-\d{3}$", v.lower()):
            raise ValueError("ID must be 'adr-XXX' format (lowercase)")
        return v.lower()
```

### Trade-offs

- **Dependency**: Adds Pydantic as a core dependency
- **Learning Curve**: Team needs to learn Pydantic patterns
- **Migration**: Harder to switch validation libraries later

## Consequences

### Positive

- Clear, maintainable validation code
- Excellent error messages for users
- Easy to add new document types
- Schema definitions serve as documentation
- IDE autocomplete for frontmatter fields

### Negative

- Additional dependency to maintain
- Pydantic major version upgrades may require changes
- Slightly larger package size

## Alternatives Considered

### JSON Schema

Would provide vendor-neutral validation but:
- More verbose schema definitions
- Less Pythonic API
- Harder to write custom validators
- Error messages less clear

### Manual Validation

Would avoid dependencies but:
- Much more code to write and maintain
- Error-prone
- Poor error messages
- No type safety

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic v2 Performance](https://docs.pydantic.dev/latest/concepts/performance/)
