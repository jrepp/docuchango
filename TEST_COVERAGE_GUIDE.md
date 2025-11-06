# Test Coverage Improvement Guide

**Current Status:** 49.53% coverage (224 tests)
**Quick Win Target:** 70% coverage (310+ tests)
**Ultimate Target:** 80% coverage (380+ tests)

---

## 📚 Documentation Overview

This directory contains a complete roadmap for improving test coverage. Choose your starting point:

### 🚀 Quick Start (Want results now?)
**→ Read: [QUICK_WINS.md](QUICK_WINS.md)**
- Step-by-step guide for 6 modules
- 2-3 hours to 70% coverage
- Includes code templates and examples

### 📊 Strategic Planning (Want the big picture?)
**→ Read: [COVERAGE_ROADMAP.md](COVERAGE_ROADMAP.md)**
- Complete 3-phase roadmap
- Success metrics and timelines
- Testing techniques and best practices

### 🎯 At-a-Glance (Want priorities only?)
**→ Read: [COVERAGE_PRIORITIES.txt](COVERAGE_PRIORITIES.txt)**
- Ranked list by ROI
- Effort estimates
- Quick command reference

### 📈 Visual Roadmap (Want to see the journey?)
**→ Read: [COVERAGE_VISUAL.txt](COVERAGE_VISUAL.txt)**
- Coverage progression charts
- ROI analysis graphs
- Impact heat maps

---

## 🎯 The Bottom Line

### Fastest Path to 70% Coverage

1. **Test 6 zero-coverage modules** (391 statements, 0% → 65%)
   - `internal_links.py` (~20 min)
   - `mdx_syntax.py` (~20 min)
   - `doc_links.py` (~15 min)
   - `proto_imports.py` (~20 min)
   - `migration_syntax.py` (~15 min)
   - `mdx_code_blocks.py` (~15 min)

2. **Time Investment:** 2-3 hours
3. **Result:** 49.53% → 70% coverage (+20.47%)
4. **New Tests:** +86 tests

### Why These 6 Modules?

✅ **Zero coverage** = Maximum impact
✅ **Simple patterns** = Copy existing tests
✅ **Independent** = Can do in any order
✅ **High value** = Core fixing functionality

---

## 💡 Key Insights

### ROI by Phase

| Phase | Time | Coverage Gain | Tests Added | ROI (Coverage/Hour) |
|-------|------|---------------|-------------|---------------------|
| **Phase 1** | 2h | +20% | +86 | **10.24%/hr** ⭐ |
| Phase 2 | 8h | +5% | +40 | 0.63%/hr |
| Phase 3 | 4h | +5% | +30 | 1.25%/hr |

**Phase 1 has 4x better ROI than other phases!**

### Coverage Sweet Spots

- **40-50%**: Basic coverage, many gaps
- **50-70%**: Good coverage, core paths tested ← **We are here**
- **70-80%**: Excellent coverage, edge cases handled ← **Phase 1 target**
- **80-90%**: Very good coverage, diminishing returns
- **90%+**: Exceptional, may not be worth the effort

**Target 70% first, then reassess.**

---

## 🛠️ Getting Started

### Prerequisites

```bash
# Ensure dependencies installed
uv sync

# Verify current coverage
uv run pytest --cov=docuchango --cov-report=term tests/ | grep TOTAL
# Should show: TOTAL ... 49.53%
```

### Step 1: Pick a Module

Start with `internal_links.py` (easiest, similar to existing tests):

```bash
# Read the source
cat docuchango/fixes/internal_links.py | head -50

# Copy similar test as template
cp tests/test_broken_links.py tests/test_internal_links.py
```

### Step 2: Adapt the Tests

Edit `tests/test_internal_links.py`:
1. Update imports
2. Change function names
3. Adapt test scenarios to match the module's logic
4. Update assertions

### Step 3: Run and Iterate

```bash
# Run with coverage
uv run pytest tests/test_internal_links.py -v \
  --cov=docuchango.fixes.internal_links \
  --cov-report=term-missing

# See uncovered lines, add more tests
# Repeat until 60-65% coverage
```

### Step 4: Verify

```bash
# Run all tests
uv run pytest tests/ -v

# Check overall coverage
uv run pytest --cov=docuchango --cov-report=term tests/

# Generate HTML report
uv run pytest --cov=docuchango --cov-report=html tests/
open htmlcov/index.html
```

### Step 5: Repeat for Other 5 Modules

Continue with:
- `mdx_syntax.py`
- `doc_links.py`
- `proto_imports.py`
- `migration_syntax.py`
- `mdx_code_blocks.py`

---

## 📋 Test Checklist

For each module, ensure tests cover:

- ✅ **Happy path**: Basic transformation works
- ✅ **No changes**: File already correct
- ✅ **Multiple**: Multiple transformations in one file
- ✅ **Edge cases**: Empty files, Unicode, special characters
- ✅ **Error handling**: Handles invalid input gracefully
- ✅ **Dry-run**: Doesn't modify files in dry-run mode

**Don't test:**
- ❌ `main()` functions extensively (low value)
- ❌ CLI argument parsing (covered elsewhere)
- ❌ Exact output formatting (brittle)

---

## 🎓 Learning from Existing Tests

### Best Examples to Copy

**For link fixing modules:**
```bash
# Use as template for: internal_links, doc_links
cat tests/test_broken_links.py
```

**For code block modules:**
```bash
# Use as template for: mdx_code_blocks
cat tests/test_code_blocks.py
```

**For regex/syntax modules:**
```bash
# Use as template for: mdx_syntax, migration_syntax, proto_imports
cat tests/test_bug_fixes.py  # See regex ReDoS tests
```

---

## 📊 Tracking Progress

### During Development

```bash
# Quick check
uv run pytest --cov=docuchango tests/ -q | tail -5

# Detailed report
uv run pytest --cov=docuchango --cov-report=term-missing tests/
```

### Coverage Milestones

Track your progress:

```
Start:  49.53% ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░
After 1: ~53% ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░
After 2: ~57% ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░
After 3: ~61% ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░
After 4: ~64% ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░
After 5: ~67% ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░
After 6: ~70% ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░ ✨
```

---

## 🚦 Decision Points

### After Reaching 70%

**Option A: Stop Here** ✅
- 70% is excellent coverage
- Core functionality well-tested
- Good ROI achieved

**Option B: Continue to Validator** 💪
- Big prize: validator.py (409 uncovered statements)
- High effort: 6-8 hours
- Lower ROI: 0.63%/hour
- Worth it if validator is critical

**Option C: Polish Existing** 🎨
- Improve modules to 80-90% each
- Lower effort: 3-4 hours
- Moderate ROI: 1.25%/hour
- Good for completeness

---

## 🎯 Success Criteria

You've succeeded when:

✅ Overall coverage ≥ 70%
✅ All 6 zero-coverage modules ≥ 60%
✅ All tests pass
✅ No coverage regressions
✅ Tests run in < 3 seconds
✅ HTML report shows green for critical paths

---

## 💬 Common Questions

**Q: Why not aim for 100%?**
A: Diminishing returns. 70-80% is the sweet spot for most projects.

**Q: Should I test main() functions?**
A: Usually no. They're thin CLI wrappers with low business value.

**Q: What about edge cases?**
A: Test the important ones (empty files, Unicode), skip obscure ones.

**Q: How do I know when to stop?**
A: When adding tests feels like busywork rather than adding value.

**Q: What if I find bugs?**
A: Great! Write a failing test, fix the bug, watch test pass.

---

## 📚 Additional Resources

- **Existing Tests:** `tests/` directory - learn from examples
- **Fixtures:** `tests/conftest.py` - reusable test utilities
- **Coverage Report:** `htmlcov/index.html` - visual coverage explorer
- **pytest Docs:** https://docs.pytest.org/

---

## 🎉 Celebrate Progress!

Remember:
- **39.81% → 49.53%** already achieved (+9.72%) ✅
- **49.53% → 70%** is the next quick win (+20.47%)
- Every test adds value and confidence
- Perfect is the enemy of good

**Start with just ONE module today. You've got this!** 💪

---

## Quick Command Reference

```bash
# Start a new test module
cp tests/test_broken_links.py tests/test_internal_links.py

# Run one test file
uv run pytest tests/test_internal_links.py -v

# Check coverage
uv run pytest --cov=docuchango tests/ -q | tail -5

# View HTML report
uv run pytest --cov=docuchango --cov-report=html tests/ && open htmlcov/index.html

# Run all checks (format, lint, type, test)
uv run ruff format . && uv run ruff check . && uv run mypy docuchango && uv run pytest tests/
```

---

**Last Updated:** 2025-11-05
**Status:** Phase 0 Complete ✅ | Phase 1 Ready 🚀
