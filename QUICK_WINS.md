# Quick Wins: Zero-Coverage Modules

**Time to 70% Coverage: ~2-3 hours**

This guide provides step-by-step instructions for the fastest path to 70% coverage.

---

## Test Creation Order (By ROI)

### 1. test_internal_links.py (~15-20 min)
**Impact:** 83 statements | **Pattern:** Similar to test_broken_links.py

<details>
<summary><b>Key Functions to Test</b></summary>

```python
# docuchango/fixes/internal_links.py
def fix_links_in_content(content: str) -> tuple[str, int]
def fix_file(file_path: Path, dry_run: bool = False) -> int
def main()  # Lines 77-145
```

**Test Scenarios:**
- ✅ Remove date prefix from RFC links: `2025-10-13-rfc-001-name.md` → `rfc-001-name.md`
- ✅ Remove date prefix from ADR links: `2025-10-15-adr-003-name.md` → `adr-003-name.md`
- ✅ Remove date prefix from MEMO links: `2025-11-01-memo-005-name.md` → `memo-005-name.md`
- ✅ Handle relative paths: `../rfcs/2025-10-13-rfc-001.md`
- ✅ Handle same-dir paths: `./2025-10-15-adr-003.md`
- ✅ Preserve anchors: `...rfc-001.md#section`
- ✅ Dry-run mode
- ✅ No changes needed (already fixed)
- ✅ Multiple links in one file
- ✅ Unicode content preservation

**Copy From:** `test_broken_links.py` (very similar structure)

</details>

**Command:**
```bash
# Create the test file
touch tests/test_internal_links.py

# Run while developing
uv run pytest tests/test_internal_links.py -v --cov=docuchango.fixes.internal_links
```

---

### 2. test_mdx_syntax.py (~20 min)
**Impact:** 76 statements | **Pattern:** Regex replacements

<details>
<summary><b>Key Functions to Test</b></summary>

```python
# docuchango/fixes/mdx_syntax.py
def fix_mdx_syntax(file_path: Path) -> tuple[int, list[str]]
def main()  # Lines 77-153
```

**Test Scenarios:**
- ✅ Fix bare numbers to backticks: `<10ms` → `` `<10ms` ``
- ✅ Fix percentage: `<100%` → `` `<100%` ``
- ✅ Fix with units: `<5MB`, `<2.5GB`, `<1KB`
- ✅ Fix with words: `<1 minute`, `<10 seconds`
- ✅ Skip already backticked: `` `<10ms` ``
- ✅ ReDoS protection (test with adversarial input)
- ✅ Multiple replacements in one file
- ✅ Preserve indentation
- ✅ Unicode content
- ✅ Empty file

**Key Edge Cases:**
- Input with 30+ repeated patterns (test regex performance)
- Long words (test bounded backtracking)

</details>

---

### 3. test_doc_links.py (~15 min)
**Impact:** 70 statements | **Pattern:** Link transformations

<details>
<summary><b>Key Functions to Test</b></summary>

```python
# docuchango/fixes/doc_links.py
def fix_doc_links(file_path: Path, dry_run: bool = False) -> int
def main()  # Lines 77-138
```

**Test Scenarios:**
- ✅ Convert .md links to docusaurus format
- ✅ Remove file extensions from internal links
- ✅ Fix relative path references
- ✅ Handle anchor links
- ✅ Dry-run mode
- ✅ No changes needed
- ✅ Multiple links
- ✅ Preserve link text
- ✅ Unicode

</details>

---

### 4. test_proto_imports.py (~20 min)
**Impact:** 61 statements | **Pattern:** Import statement fixes

<details>
<summary><b>Key Functions to Test</b></summary>

```python
# docuchango/fixes/proto_imports.py
def fix_proto_imports(file_path: Path) -> tuple[int, list[str]]
def main()  # Lines 77-138
```

**Test Scenarios:**
- ✅ Fix old import style to new style
- ✅ Update import paths
- ✅ Handle multiple imports in file
- ✅ Preserve non-proto imports
- ✅ Handle already-correct imports
- ✅ Preserve import ordering
- ✅ Unicode in comments
- ✅ Empty file

**Note:** This may be project-specific. Read the file first to understand the transformation rules.

</details>

---

### 5. test_migration_syntax.py (~15 min)
**Impact:** 51 statements | **Pattern:** Syntax transformations

<details>
<summary><b>Key Functions to Test</b></summary>

```python
# docuchango/fixes/migration_syntax.py
def fix_migration_syntax(file_path: Path) -> tuple[int, list[str]]
def main()  # Lines 55-94
```

**Test Scenarios:**
- ✅ Transform old syntax to new syntax
- ✅ Handle multiple transformations
- ✅ Skip already-migrated code
- ✅ Preserve formatting
- ✅ Handle edge cases
- ✅ Unicode content
- ✅ Empty file

</details>

---

### 6. test_mdx_code_blocks.py (~15 min)
**Impact:** 50 statements | **Pattern:** Very similar to test_code_blocks.py

<details>
<summary><b>Key Functions to Test</b></summary>

```python
# docuchango/fixes/mdx_code_blocks.py
def fix_code_blocks(file_path: Path) -> tuple[int, str]
def main()  # Lines 67-90
```

**Test Scenarios:**
- ✅ Add 'text' to unlabeled code blocks
- ✅ Preserve labeled code blocks
- ✅ Track line numbers correctly
- ✅ Handle nested code blocks
- ✅ Handle indented code blocks
- ✅ Empty file
- ✅ No code blocks

**Copy From:** `test_code_blocks.py` (almost identical)

</details>

---

## Template Code

### Basic Test Structure
```python
"""Tests for {module}.py fix module."""

from pathlib import Path
from docuchango.fixes.{module} import {function_name}


class Test{Module}Fixes:
    """Test {module} fixing functionality."""

    def test_basic_transformation(self, tmp_path):
        """Test basic transformation."""
        test_file = tmp_path / "test.md"
        content = """Input content here"""
        test_file.write_text(content, encoding="utf-8")

        result = {function_name}(test_file)
        assert result > 0  # or tuple unpacking

        output = test_file.read_text(encoding="utf-8")
        assert "expected" in output

    def test_no_changes_needed(self, tmp_path):
        """Test file with no issues."""
        test_file = tmp_path / "test.md"
        content = """Already correct content"""
        test_file.write_text(content, encoding="utf-8")

        result = {function_name}(test_file)
        assert result == 0  # No changes

    def test_unicode_preserved(self, tmp_path):
        """Test Unicode handling."""
        test_file = tmp_path / "test.md"
        content = """Content with → ✓ 中文"""
        test_file.write_text(content, encoding="utf-8")

        {function_name}(test_file)
        output = test_file.read_text(encoding="utf-8")

        assert "→" in output
        assert "✓" in output
        assert "中文" in output

    def test_empty_file(self, tmp_path):
        """Test empty file handling."""
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding="utf-8")

        result = {function_name}(test_file)
        assert result == 0
```

---

## Testing Workflow

### Step-by-Step Process

1. **Read the source file** to understand transformations:
```bash
cat docuchango/fixes/internal_links.py | head -50
```

2. **Copy similar test file** as template:
```bash
cp tests/test_broken_links.py tests/test_internal_links.py
```

3. **Adapt tests** to new module:
- Update imports
- Update test scenarios
- Adjust assertions

4. **Run tests** with coverage:
```bash
uv run pytest tests/test_internal_links.py -v \
  --cov=docuchango.fixes.internal_links \
  --cov-report=term-missing
```

5. **Iterate** until coverage is high:
- Check missing lines in coverage report
- Add tests for uncovered branches
- Focus on main() function last (often low value)

6. **Verify** no regressions:
```bash
uv run pytest tests/ -v
```

---

## Coverage Targets

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| internal_links.py | 0% | 65%+ | 🔥 High |
| mdx_syntax.py | 0% | 65%+ | 🔥 High |
| doc_links.py | 0% | 65%+ | 🔥 High |
| proto_imports.py | 0% | 60%+ | 🔥 High |
| migration_syntax.py | 0% | 60%+ | 🔥 High |
| mdx_code_blocks.py | 0% | 65%+ | 🔥 High |

**Note:** Target 60-65% for each module. The main() functions are often low-value (just CLI wrappers), so don't stress about 100%.

---

## Expected Outcome

**Before:** 49.53% coverage (224 tests)

**After Phase 1:** ~70% coverage (330+ tests)

**Time Investment:** 2-3 hours

**Commands to Verify:**
```bash
# Run all tests
uv run pytest --cov=docuchango --cov-report=term tests/

# Should see:
# - TOTAL: 70%+
# - ~330+ tests passing
# - All new modules with 60%+ coverage
```

---

## Tips for Speed

1. **Reuse patterns**: Copy from similar test files
2. **Skip main()**: Focus on core logic functions first
3. **Use tmp_path**: Built-in pytest fixture for temp files
4. **Parallel work**: Write tests for multiple modules simultaneously
5. **Auto-format**: `uv run ruff format tests/` after each file
6. **TDD**: Write test → run → fail → implement → pass → refactor

---

## Common Pitfalls

❌ **Don't:**
- Test main() functions extensively (low ROI)
- Aim for 100% coverage (diminishing returns)
- Write brittle tests (depend on exact output formatting)
- Test implementation details

✅ **Do:**
- Test core transformation logic
- Test edge cases (empty, Unicode, multiple)
- Test error handling
- Keep tests simple and readable
- Use descriptive names

---

## Measurement

Track progress with:
```bash
# Quick coverage check
uv run pytest --cov=docuchango --cov-report=term tests/ | grep TOTAL

# Detailed report
uv run pytest --cov=docuchango --cov-report=html tests/
open htmlcov/index.html
```

---

## Next Steps After Quick Wins

Once you hit 70% coverage:

1. **Celebrate!** 🎉 You've doubled coverage
2. **Review the HTML report** to identify remaining gaps
3. **Move to Phase 2:** validator.py deep dive (see COVERAGE_ROADMAP.md)
4. **Consider diminishing returns:** 70% is already excellent coverage

**Remember:** Perfect is the enemy of good. 70% coverage with quality tests beats 90% coverage with brittle tests.
