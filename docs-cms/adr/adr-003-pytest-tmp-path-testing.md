---
id: "adr-003"
title: "Use pytest with tmp_path for Testing"
status: Accepted
date: 2025-01-26
deciders: Engineering Team
tags: ["pytest", "testing", "tmp-path", "filesystem"]
project_id: "docuchango"
doc_uuid: "c3d4e5f6-a7b8-4c7d-0e1f-2a3b4c5d6e7f"
---

# ADR-003: Use pytest with tmp_path for Testing

## Status

Accepted

## Context

Docuchango operates on markdown files and directory structures. Testing requires:

- Creating test files and directories
- Isolated test environments (no side effects)
- Fast test execution
- Memory-backed filesystems for speed
- Easy cleanup after tests
- Cross-platform compatibility

Options considered:

1. **unittest with tempfile** - Stdlib, manual cleanup
2. **pytest with tmp_path** - Modern, automatic cleanup
3. **pytest with tmpdir** - Older pytest fixture
4. **In-memory filesystems** - Fast but complex setup
5. **Docker volumes** - Isolated but slow

## Decision

We will use **pytest with tmp_path fixture** for all file-based tests.

## Rationale

### Advantages

1. **Automatic Cleanup**: pytest handles cleanup automatically
2. **Isolation**: Each test gets its own directory
3. **Memory-Backed**: pytest uses tmpfs where available (fast)
4. **Path Objects**: Returns pathlib.Path (modern Python)
5. **Cross-Platform**: Works on Windows, Linux, macOS
6. **No Boilerplate**: Minimal setup code required
7. **pytest Ecosystem**: Integrates with all pytest features

### Example Test

```python
def test_fix_trailing_whitespace(tmp_path):
    """Test that trailing whitespace is removed."""
    test_file = tmp_path / "test.md"
    content = "Line 1   \nLine 2\t\nLine 3\n"
    test_file.write_text(content)

    changes = fix_trailing_whitespace(test_file)
    assert changes == 2

    result = test_file.read_text()
    assert result == "Line 1\nLine 2\nLine 3\n"
```

### Trade-offs

- **pytest Dependency**: Requires pytest (already chosen for testing)
- **Disk I/O**: Still uses disk (though often tmpfs)

## Consequences

### Positive

- Fast, isolated tests
- Clean test code with minimal boilerplate
- No manual cleanup needed
- Easy to create complex directory structures
- Tests are repeatable and deterministic
- CI/CD friendly (no state between runs)

### Negative

- Tests rely on pytest (can't easily run with unittest)
- Slightly slower than pure in-memory (but negligible)

## Implementation Details

### Directory Structure Setup

```python
def test_validator(tmp_path):
    docs_root = tmp_path / "repo"
    doc_dir = docs_root / "docs-cms" / "adr"
    doc_dir.mkdir(parents=True)

    doc_file = doc_dir / "adr-001-test.md"
    doc_file.write_text(content)

    validator = PrismDocValidator(repo_root=docs_root)
    validator.scan_documents()
```

### Test Coverage

With tmp_path, we created:
- **43 tests** for schemas, fixes, and frontmatter validation
- **18 tests** for link validation
- All tests isolated and fast (< 0.2s total)

## Alternatives Considered

### unittest with tempfile

Would use stdlib but:
- Manual cleanup with try/finally
- Returns strings, not Path objects
- More boilerplate code
- Less pytest integration

### In-Memory Filesystems (pyfakefs)

Would be faster but:
- Additional dependency
- More complex setup
- Debugging harder (no files on disk)
- Some Path operations may not work

### Docker Volumes

Would provide full isolation but:
- Much slower (seconds per test)
- Requires Docker
- Complex CI setup
- Overkill for file testing

## References

- [pytest tmp_path fixture](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [pytest best practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
