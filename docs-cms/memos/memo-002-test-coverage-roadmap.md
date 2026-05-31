---
author: Engineering Team
created: 2026-05-30
doc_uuid: 7428b7a9-2e68-4fb2-90f0-33609d466601
id: memo-002
project_id: docuchango
tags: [coverage, roadmap, testing]
title: Test Coverage Roadmap
---

# Memo-002: Test Coverage Roadmap

## Summary

The fastest path to stronger coverage is to test zero-coverage fix modules before investing in deeper validator coverage. The prior working target was to move from roughly 49.5% coverage and 224 tests toward at least 70% coverage.

## Priority Order

Tier 1 covers zero-coverage modules with high return on investment:

| Priority | Module | Rationale |
|----------|--------|-----------|
| 1 | `internal_links.py` | Similar to existing broken-link tests |
| 2 | `mdx_syntax.py` | Regex transformations with important edge cases |
| 3 | `doc_links.py` | Straightforward link rewriting |
| 4 | `proto_imports.py` | Import statement rewrites |
| 5 | `migration_syntax.py` | Syntax transformations |
| 6 | `mdx_code_blocks.py` | Similar to existing code-block tests |

Tier 2 should target `validator.py`, especially document scanning, link validation, error aggregation, formatting checks, build validation, and integration workflows.

Tier 3 should polish existing modules such as `docs.py`, `cli.py`, `code_blocks.py`, `broken_links.py`, `code_blocks_proper.py`, `cross_plugin_links.py`, and `schemas.py`.

## Test Strategy

For each fix module, cover these cases:

- Basic transformation works.
- Files with no issues remain unchanged.
- Multiple transformations in one file work.
- Empty files and Unicode content are handled.
- Dry-run mode does not modify files where supported.
- Error handling is deterministic and does not hide failures.

Prefer `pytest` fixtures and `tmp_path` for file-based tests. Use parametrized tests for transformation tables and golden files only when expected output is complex enough to justify them.

## Commands

Run focused coverage while developing a module:

```bash
uv run pytest tests/test_internal_links.py -v --cov=docuchango.fixes.internal_links --cov-report=term-missing
```

Run the full suite and coverage report:

```bash
uv run pytest --cov=docuchango --cov-report=term-missing tests/
```

## Success Metrics

The first milestone is 70% coverage with the Tier 1 modules tested. Later milestones should reassess whether 75%, 80%, or higher coverage is worth the maintenance cost.
