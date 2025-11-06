# Test Coverage Improvement Roadmap

**Current Coverage:** 49.53% (224 tests)
**Target Coverage:** 70%+ (350+ tests)
**Last Updated:** 2025-11-05

## Priority Ranking (Maximize ROI)

### Tier 1: Quick Wins - Zero Coverage Modules (391 statements, ~20% coverage gain)
*Estimated effort: 2-3 hours | Impact: Very High | Difficulty: Low*

These modules follow similar patterns to already-tested modules. Each should take ~15-20 minutes.

| Priority | Module | Statements | Complexity | Estimated Tests | Notes |
|----------|--------|-----------|------------|-----------------|-------|
| **1** | `internal_links.py` | 83 (0%) | LOW | ~18 tests | Similar to broken_links.py pattern |
| **2** | `mdx_syntax.py` | 76 (0%) | MEDIUM | ~16 tests | Regex replacements, test edge cases |
| **3** | `doc_links.py` | 70 (0%) | LOW | ~15 tests | Link fixing, straightforward |
| **4** | `proto_imports.py` | 61 (0%) | MEDIUM | ~13 tests | Import statement fixes |
| **5** | `migration_syntax.py` | 51 (0%) | MEDIUM | ~12 tests | Syntax transformations |
| **6** | `mdx_code_blocks.py` | 50 (0%) | LOW | ~12 tests | Similar to code_blocks.py |

**Subtotal Impact:** +391 statements covered → **~70% total coverage**

---

### Tier 2: High-Value Improvements (409 statements, ~21% coverage gain)
*Estimated effort: 6-8 hours | Impact: Very High | Difficulty: Medium-High*

| Priority | Module | Miss | Current | Target | Estimated Tests | Notes |
|----------|--------|------|---------|--------|-----------------|-------|
| **7** | `validator.py` | 409 | 48.10% | 75%+ | ~40 tests | **Biggest prize**: Core validation logic, complex workflows |

**Key Areas to Test in validator.py:**
- Document scanning and parsing (lines 484-561)
- Link validation logic (lines 565-607)
- Error reporting and aggregation (lines 611-631)
- Formatting checks (lines 635-674)
- Build validation (lines 678-746)
- Integration scenarios (lines 1084-1196)

---

### Tier 3: Incremental Improvements (139 statements, ~7% coverage gain)
*Estimated effort: 3-4 hours | Impact: Medium | Difficulty: Low-Medium*

Polish existing coverage to 90%+ where practical.

| Priority | Module | Miss | Current | Target | Estimated Tests | Focus Areas |
|----------|--------|------|---------|--------|-----------------|-------------|
| **8** | `docs.py` | 34 | 75.26% | 90%+ | ~10 tests | Main function, edge cases (lines 179-224) |
| **9** | `cli.py` | 42 | 76.82% | 85%+ | ~12 tests | Exception handling, import errors (lines 55-57, 86-88, 100-102) |
| **10** | `code_blocks.py` | 27 | 73.43% | 85%+ | ~8 tests | Main function logic (lines 134-170) |
| **11** | `broken_links.py` | 19 | 55.00% | 80%+ | ~8 tests | Main function (lines 77-102) |
| **12** | `code_blocks_proper.py` | 18 | 67.44% | 85%+ | ~6 tests | Main function (lines 78-99) |
| **13** | `cross_plugin_links.py` | 15 | 41.86% | 75%+ | ~8 tests | Main function (lines 38-57) |
| **14** | `schemas.py` | 9 | 92.53% | 95%+ | ~5 tests | Edge cases in validators |

---

### Tier 4: Low Priority (11 statements, <1% coverage gain)
*Estimated effort: 1 hour | Impact: Low | Difficulty: Low*

| Priority | Module | Miss | Current | Target | Notes |
|----------|--------|------|---------|--------|-------|
| **15** | `__init__.py` | 2 | 77.78% | 100% | ~2 tests | Import edge cases |

---

## Implementation Strategy

### Phase 1: Quick Wins (Week 1)
**Goal:** Reach 70% coverage

1. Add tests for all Tier 1 modules (6 test files)
2. Use existing test patterns from similar modules
3. Focus on:
   - Happy path coverage
   - Common edge cases (empty files, Unicode, multiple matches)
   - Dry-run modes
   - Error handling

**Expected Outcome:** 49.53% → ~70% coverage (+115 tests)

---

### Phase 2: Validator Deep Dive (Week 2-3)
**Goal:** Reach 75% coverage

1. Break validator.py into test suites:
   - `test_validator_scanning.py` - Document discovery
   - `test_validator_links.py` - Link validation
   - `test_validator_formatting.py` - Format checks
   - `test_validator_errors.py` - Error handling
   - `test_validator_integration.py` - End-to-end scenarios

2. Use property-based testing for complex scenarios
3. Create comprehensive validator fixtures

**Expected Outcome:** 70% → ~75% coverage (+40 tests)

---

### Phase 3: Polish (Week 4)
**Goal:** Reach 80% coverage

1. Fill gaps in existing modules (Tier 3)
2. Add integration tests
3. Test main() functions that were skipped
4. Add edge case coverage

**Expected Outcome:** 75% → 80%+ coverage (+30 tests)

---

## Testing Techniques to Apply

### 1. **Fixture Reuse**
- Leverage existing `conftest.py` generators
- Create module-specific fixtures for fix patterns

### 2. **Parameterized Tests**
```python
@pytest.mark.parametrize("input,expected", [
    ("case1", "result1"),
    ("case2", "result2"),
])
def test_multiple_cases(input, expected):
    assert fix(input) == expected
```

### 3. **Property-Based Testing** (for validator.py)
```python
from hypothesis import given, strategies as st

@given(st.text())
def test_validator_handles_any_markdown(content):
    # Should not crash on any input
    result = validate(content)
    assert isinstance(result, ValidationResult)
```

### 4. **Golden Files**
- Store expected outputs for complex transformations
- Compare against known-good results

### 5. **Mocking External Dependencies**
- Mock file system operations where appropriate
- Mock subprocess calls for build validation

---

## Success Metrics

| Milestone | Coverage | Tests | Timeline |
|-----------|----------|-------|----------|
| ✅ Baseline | 39.81% | 115 | Completed |
| ✅ Phase 0 | 49.53% | 224 | Completed |
| 🎯 Phase 1 | 70% | 330+ | Week 1 |
| 🎯 Phase 2 | 75% | 370+ | Week 2-3 |
| 🎯 Phase 3 | 80% | 400+ | Week 4 |
| 🌟 Stretch | 85%+ | 450+ | Week 5-6 |

---

## Test Quality Checklist

For each new test module, ensure:

- ✅ Uses pytest fixtures from conftest.py
- ✅ Tests happy path
- ✅ Tests edge cases (empty, Unicode, special chars)
- ✅ Tests error handling
- ✅ Tests dry-run modes (where applicable)
- ✅ Descriptive test names and docstrings
- ✅ Grouped by functionality (test classes)
- ✅ No flaky tests (deterministic)
- ✅ Fast execution (< 0.1s per test)

---

## Quick Reference: Test File Templates

### Fix Module Pattern
```python
"""Tests for {module_name}.py fix module."""

from docuchango.fixes.{module_name} import fix_function

class Test{ModuleName}Fixes:
    """Test {module} fixing functionality."""

    def test_basic_fix(self, tmp_path):
        """Test basic fix scenario."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content", encoding="utf-8")

        result = fix_function(test_file)
        assert result > 0

    def test_no_changes_needed(self, tmp_path):
        """Test file with no issues."""
        # ...

    def test_dry_run(self, tmp_path):
        """Test dry-run mode."""
        # ...

    def test_unicode_content(self, tmp_path):
        """Test Unicode handling."""
        # ...
```

---

## Command Reference

```bash
# Run all tests with coverage
uv run pytest --cov=docuchango --cov-report=term-missing tests/

# Run specific module tests
uv run pytest tests/test_internal_links.py -v

# Watch mode for TDD
uv run pytest-watch tests/ -- --cov=docuchango

# Coverage HTML report
uv run pytest --cov=docuchango --cov-report=html tests/
open htmlcov/index.html

# Run only new tests
uv run pytest tests/test_*.py -v --co  # List tests
uv run pytest tests/test_internal_links.py -v  # Run one
```

---

## Notes

- **Don't over-optimize**: 80% coverage is excellent for most projects
- **Focus on value**: Test important paths, not just coverage numbers
- **Keep tests fast**: Total suite should run in < 3 seconds
- **Maintain quality**: Every test should be valuable and maintainable
- **Document complex tests**: Add docstrings explaining "why" not just "what"

---

## Estimated Total Effort

| Phase | Effort | Coverage Gain | Test Gain |
|-------|--------|---------------|-----------|
| Phase 1 | 2-3 hours | +20% | +115 tests |
| Phase 2 | 6-8 hours | +5% | +40 tests |
| Phase 3 | 3-4 hours | +5% | +30 tests |
| **Total** | **11-15 hours** | **+30%** | **+185 tests** |

**ROI:** Achievable in 2-3 focused work sessions to reach 80% coverage milestone.
