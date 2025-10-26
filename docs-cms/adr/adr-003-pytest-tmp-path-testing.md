---
id: "adr-003"
title: "Use pytest with tmp_path for Testing"
status: Accepted
date: 2025-01-26
deciders: Engineering Team
tags: ["pytest", "testing", "tmp-path", "filesystem"]
project_id: "docuchango"
doc_uuid: "a04e65be-7296-4051-8a64-98cca8abcdb0"
---

# ADR-003: Use pytest with tmp_path for Testing

## Decision

Use pytest's `tmp_path` fixture for all file-based tests.

## Why

Tests need to create markdown files and directory structures. Need isolation, speed, and automatic cleanup.

`tmp_path` gives us:
- Automatic cleanup (no manual try/finally)
- Each test gets its own directory
- Memory-backed where available (tmpfs)
- Returns pathlib.Path objects
- Works on Windows, Linux, macOS

```python
def test_fix_trailing_whitespace(tmp_path):
    test_file = tmp_path / "test.md"
    test_file.write_text("Line 1   \nLine 2\n")

    fix_trailing_whitespace(test_file)

    assert test_file.read_text() == "Line 1\nLine 2\n"
```

Create complex structures easily:

```python
def test_validator(tmp_path):
    docs_root = tmp_path / "repo"
    doc_dir = docs_root / "docs-cms" / "adr"
    doc_dir.mkdir(parents=True)

    doc_file = doc_dir / "adr-001-test.md"
    doc_file.write_text(content)

    validator = DocValidator(repo_root=docs_root)
    validator.scan_documents()
```

## Alternatives

**unittest + tempfile**: Manual cleanup, returns strings not Paths

**pyfakefs**: Faster but another dependency, harder to debug

## Result

- 61 tests, all isolated and fast (< 0.3s total)
- Clean test code with minimal boilerplate
- No manual cleanup needed
