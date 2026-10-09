# Fixer regression fixtures

Reduced copies of real documents that a Phase 1 fixer once damaged. Each file
keeps the structure that triggered the bug and drops unrelated content. The
tests that load them are in `tests/test_timestamp_fixes.py`.

| File | Bug |
|------|-----|
| `adr-index-frontmatter-example.md` | FM-007 inserted `created` after the `status:` line of the frontmatter example inside a code block, because the frontmatter has `id` but no `status` |
| `rfc-index-status-bullet.md` | FM-007 inserted `created` after the body bullet `- Work status: ...`; every later run added another line |
