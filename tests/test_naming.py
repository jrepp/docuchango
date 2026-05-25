"""Tests for docuchango.naming module.

Covers all naming standard functionality including:
- Built-in naming standards
- Custom naming standards
- Validation functions
- Resolution functions
"""

from __future__ import annotations

import pytest

from docuchango.naming import (
    ALL_BUILTIN_NAMES,
    BUILTIN_NAMING_STANDARDS,
    describe_standard,
    resolve_naming_standard,
    validate_name,
    validate_name_with_standard,
)


class TestBuiltinNamingStandards:
    """Tests for BUILTIN_NAMING_STANDARDS constant."""

    def test_all_expected_standards_present(self):
        """Verify all expected naming standards are defined."""
        expected = {
            "nnn-name",
            "year-month-day-name",
            "kebab-case",
            "snake_case",
            "camelCase",
            "PascalCase",
            "lowercase",
            "uppercase",
        }
        assert set(BUILTIN_NAMING_STANDARDS.keys()) == expected

    def test_all_patterns_are_valid_regex(self):
        """Verify all built-in patterns are valid regex strings."""
        import re

        for name, pattern in BUILTIN_NAMING_STANDARDS.items():
            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"Invalid regex in '{name}': {e}")

    def test_all_patterns_start_with_anchor(self):
        """Verify all built-in patterns start with ^ anchor."""
        for name, pattern in BUILTIN_NAMING_STANDARDS.items():
            assert pattern.startswith("^"), f"Pattern '{name}' missing ^ anchor"

    def test_all_patterns_end_with_md_extension(self):
        """Verify all built-in patterns require .md extension."""
        for name, pattern in BUILTIN_NAMING_STANDARDS.items():
            assert r".md$" in pattern, f"Pattern '{name}' missing .md$ suffix"


class TestAllBuiltinNames:
    """Tests for ALL_BUILTIN_NAMES constant."""

    def test_is_sorted_list(self):
        """Verify ALL_BUILTIN_NAMES is a sorted list of all standard names."""
        assert sorted(BUILTIN_NAMING_STANDARDS.keys()) == ALL_BUILTIN_NAMES

    def test_length_matches_keys(self):
        """Verify length matches number of built-in standards."""
        assert len(ALL_BUILTIN_NAMES) == len(BUILTIN_NAMING_STANDARDS)


class TestValidateName:
    """Tests for validate_name function."""

    def test_valid_kebab_case(self):
        """Valid kebab-case names should pass."""
        assert validate_name("my-document.md", r"^[a-z0-9]+(-[a-z0-9]+)*\.md$") is True

    def test_valid_single_word(self):
        """Single word filenames should pass."""
        assert validate_name("document.md", r"^[a-z0-9]+\.md$") is True

    def test_invalid_with_uppercase(self):
        """Uppercase should fail for lowercase pattern."""
        assert validate_name("MyDocument.md", r"^[a-z0-9]+\.md$") is False

    def test_invalid_with_underscores(self):
        """Underscores should fail for kebab-case pattern."""
        assert validate_name("my_document.md", r"^[a-z0-9]+(-[a-z0-9]+)*\.md$") is False

    def test_without_anchor_still_works(self):
        """Pattern without ^ anchor should still work (auto-anchored)."""
        assert validate_name("document.md", r"[a-z]+\.md$") is True

    def test_pattern_without_anchor_not_added_when_present(self):
        """Pattern starting with ^ should not get double anchor."""
        assert validate_name("document.md", r"^[a-z]+\.md$") is True

    def test_invalid_wrong_extension(self):
        """Wrong file extension should fail."""
        assert validate_name("document.txt", r"^[a-z0-9]+\.md$") is False

    def test_invalid_empty_name(self):
        """.md alone should not match pattern requiring chars."""
        assert validate_name(".md", r"^[a-z0-9]+\.md$") is False

    def test_valid_nnn_name(self):
        """NNN-name format should match."""
        assert validate_name("001-intro.md", r"^(\d{3})-(.+)\.md$") is True

    def test_invalid_nnn_name_wrong_digits(self):
        """NNN with wrong number of digits should fail."""
        assert validate_name("01-intro.md", r"^(\d{3})-(.+)\.md$") is False

    def test_valid_date_name(self):
        """Date-prefixed name should match."""
        assert validate_name("2025-05-25-intro.md", r"^\d{4}-\d{2}-\d{2}-(.+)\.md$") is True

    def test_invalid_date_name(self):
        """Invalid date format should not match."""
        assert validate_name("25-05-2025-intro.md", r"^\d{4}-\d{2}-\d{2}-(.+)\.md$") is False

    def test_valid_camel_case(self):
        """camelCase names should match."""
        assert validate_name("myDocument.md", r"^[a-z][a-zA-Z0-9]*\.md$") is True

    def test_invalid_camel_case_starts_upper(self):
        """PascalCase should not match camelCase pattern."""
        assert validate_name("MyDocument.md", r"^[a-z][a-zA-Z0-9]*\.md$") is False

    def test_valid_pascal_case(self):
        """PascalCase names should match."""
        assert validate_name("MyDocument.md", r"^[A-Z][a-zA-Z0-9]*\.md$") is True

    def test_invalid_pascal_case_starts_lower(self):
        """camelCase should not match PascalCase pattern."""
        assert validate_name("myDocument.md", r"^[A-Z][a-zA-Z0-9]*\.md$") is False


class TestValidateNameWithStandard:
    """Tests for validate_name_with_standard function."""

    def test_builtin_standard_kebab_case(self):
        """Valid kebab-case with named standard."""
        assert validate_name_with_standard("my-document.md", "kebab-case") is True

    def test_builtin_standard_snake_case(self):
        """Valid snake_case with named standard."""
        assert validate_name_with_standard("my_document.md", "snake_case") is True

    def test_builtin_standard_nnn_name(self):
        """Valid NNN-name with named standard."""
        assert validate_name_with_standard("001-intro.md", "nnn-name") is True

    def test_builtin_standard_year_month_day(self):
        """Valid date-format name with named standard."""
        assert validate_name_with_standard("2025-05-25-intro.md", "year-month-day-name") is True

    def test_builtin_standard_camel_case(self):
        """Valid camelCase with named standard."""
        assert validate_name_with_standard("myDocument.md", "camelCase") is True

    def test_builtin_standard_pascal_case(self):
        """Valid PascalCase with named standard."""
        assert validate_name_with_standard("MyDocument.md", "PascalCase") is True

    def test_builtin_standard_lowercase(self):
        """Valid lowercase with named standard."""
        assert validate_name_with_standard("mydocument.md", "lowercase") is True

    def test_builtin_standard_uppercase(self):
        """Valid UPPERCASE with named standard."""
        assert validate_name_with_standard("MYDOCUMENT.md", "uppercase") is True

    def test_invalid_for_builtin_standard(self):
        """Invalid name for given standard should return False."""
        assert validate_name_with_standard("my_document.md", "kebab-case") is False

    def test_custom_standard_match(self):
        """Custom standard should work when provided."""
        custom = {"custom": r"^custom-.+\.md$"}
        assert validate_name_with_standard("custom-doc.md", "custom", custom) is True

    def test_custom_standard_no_match(self):
        """Custom standard should not match non-matching name."""
        custom = {"custom": r"^custom-.+\.md$"}
        assert validate_name_with_standard("other-doc.md", "custom", custom) is False

    def test_raw_regex_pattern(self):
        """Raw regex pattern starting with ^ should work."""
        assert validate_name_with_standard("test-doc.md", r"^test-.+\.md$") is True

    def test_unknown_standard_raises(self):
        """Unknown standard name should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown naming standard"):
            validate_name_with_standard("doc.md", "unknown-standard")

    def test_unknown_standard_error_message_contains_available(self):
        """Error message should list available standards."""
        with pytest.raises(ValueError) as exc_info:
            validate_name_with_standard("doc.md", "nonexistent")
        assert "Available:" in str(exc_info.value)


class TestResolveNamingStandard:
    """Tests for resolve_naming_standard function."""

    def test_resolve_builtin_kebab_case(self):
        """Resolve kebab-case should return pattern."""
        result = resolve_naming_standard("kebab-case", None)
        assert result == r"^[a-z0-9]+(-[a-z0-9]+)*\.md$"

    def test_resolve_builtin_snake_case(self):
        """Resolve snake_case should return pattern."""
        result = resolve_naming_standard("snake_case", None)
        assert result == r"^[a-z0-9]+(_[a-z0-9]+)*\.md$"

    def test_resolve_builtin_nnn_name(self):
        """Resolve nnn-name should return pattern."""
        result = resolve_naming_standard("nnn-name", None)
        assert result == r"^(\d{3})-(.+)\.md$"

    def test_resolve_builtin_year_month_day(self):
        """Resolve year-month-day-name should return pattern."""
        result = resolve_naming_standard("year-month-day-name", None)
        assert result == r"^\d{4}-\d{2}-\d{2}-(.+)\.md$"

    def test_resolve_builtin_camel_case(self):
        """Resolve camelCase should return pattern."""
        result = resolve_naming_standard("camelCase", None)
        assert result == r"^[a-z][a-zA-Z0-9]*\.md$"

    def test_resolve_builtin_pascal_case(self):
        """Resolve PascalCase should return pattern."""
        result = resolve_naming_standard("PascalCase", None)
        assert result == r"^[A-Z][a-zA-Z0-9]*\.md$"

    def test_resolve_builtin_lowercase(self):
        """Resolve lowercase should return pattern."""
        result = resolve_naming_standard("lowercase", None)
        assert result == r"^[a-z0-9]+\.md$"

    def test_resolve_builtin_uppercase(self):
        """Resolve uppercase should return pattern."""
        result = resolve_naming_standard("uppercase", None)
        assert result == r"^[A-Z0-9]+\.md$"

    def test_resolve_custom_standard(self):
        """Resolve custom standard should return its pattern."""
        custom = {"my-custom": r"^my-.+\.md$"}
        result = resolve_naming_standard("my-custom", custom)
        assert result == r"^my-.+\.md$"

    def test_resolve_custom_overrides_builtin(self):
        """Custom standard with same name as builtin should override."""
        custom = {"kebab-case": r"^custom-kebab-.+\.md$"}
        result = resolve_naming_standard("kebab-case", custom)
        assert result == r"^custom-kebab-.+\.md$"

    def test_resolve_raw_pattern(self):
        """Raw pattern starting with ^ should be returned as-is."""
        result = resolve_naming_standard(r"^test-.+\.md$", None)
        assert result == r"^test-.+\.md$"

    def test_resolve_none_returns_none(self):
        """None input should return None."""
        result = resolve_naming_standard(None, None)
        assert result is None

    def test_resolve_empty_string_returns_none(self):
        """Empty string input should return None."""
        result = resolve_naming_standard("", None)
        assert result is None

    def test_resolve_unknown_returns_none(self):
        """Unknown standard name should return None (not raise)."""
        result = resolve_naming_standard("nonexistent-standard", None)
        assert result is None

    def test_resolve_with_custom_not_provided(self):
        """Custom standards dict provided but standard not in it should return None."""
        result = resolve_naming_standard("missing-standard", {})
        assert result is None


class TestDescribeStandard:
    """Tests for describe_standard function."""

    def test_describe_kebab_case(self):
        """Describe kebab-case should return human-readable string."""
        result = describe_standard("kebab-case", None)
        assert "kebab-case" in result
        assert "my-document-name.md" in result

    def test_describe_snake_case(self):
        """Describe snake_case should return human-readable string."""
        result = describe_standard("snake_case", None)
        assert "snake_case" in result
        assert "my_document_name.md" in result

    def test_describe_camel_case(self):
        """Describe camelCase should return human-readable string."""
        result = describe_standard("camelCase", None)
        assert "camelCase" in result
        assert "myDocumentName.md" in result

    def test_describe_pascal_case(self):
        """Describe PascalCase should return human-readable string."""
        result = describe_standard("PascalCase", None)
        assert "PascalCase" in result
        assert "MyDocumentName.md" in result

    def test_describe_lowercase(self):
        """Describe lowercase should return human-readable string."""
        result = describe_standard("lowercase", None)
        assert "lowercase" in result
        assert "mydocumentname.md" in result

    def test_describe_uppercase(self):
        """Describe uppercase should return human-readable string."""
        result = describe_standard("uppercase", None)
        assert "UPPERCASE" in result
        assert "MYDOCUMENTNAME.md" in result

    def test_describe_nnn_name(self):
        """Describe nnn-name should return human-readable string."""
        result = describe_standard("nnn-name", None)
        assert "NNN-name" in result
        assert "001-intro.md" in result

    def test_describe_year_month_day_name(self):
        """Describe year-month-day-name should return human-readable string."""
        result = describe_standard("year-month-day-name", None)
        assert "YYYY-MM-DD" in result
        assert "2025-05-25-intro.md" in result

    def test_describe_custom_standard(self):
        """Describe custom standard should show pattern."""
        custom = {"my-custom": r"^custom-.+\.md$"}
        result = describe_standard("my-custom", custom)
        assert "my-custom" in result
        assert r"^custom-.+\.md$" in result

    def test_describe_raw_pattern(self):
        """Describe raw pattern should indicate custom pattern."""
        result = describe_standard(r"^my-.+\.md$", None)
        assert "Custom pattern" in result
        assert r"^my-.+\.md$" in result

    def test_describe_unknown(self):
        """Describe unknown standard should indicate unknown."""
        result = describe_standard("nonexistent", None)
        assert "Unknown standard" in result


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_validation_workflow(self):
        """Test complete workflow: resolve standard, then validate."""
        pattern = resolve_naming_standard("kebab-case", None)
        assert pattern is not None
        assert validate_name("my-document-name.md", pattern) is True

    def test_custom_standard_full_workflow(self):
        """Test workflow with custom standards."""
        custom = {"my-standard": r"^my-.+\.md$"}
        pattern = resolve_naming_standard("my-standard", custom)
        assert pattern is not None
        assert validate_name("my-document.md", pattern) is True

    def test_invalid_name_with_correct_standard(self):
        """Test that invalid names are caught even with correct standard."""
        pattern = resolve_naming_standard("kebab-case", None)
        assert pattern is not None
        assert validate_name("my_document_name.md", pattern) is False

    def test_validation_excludes_non_md_files(self):
        """Test that non-.md files are rejected."""
        for _name, pattern in BUILTIN_NAMING_STANDARDS.items():
            assert validate_name("document.txt", pattern) is False

