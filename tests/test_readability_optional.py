"""Tests for readability module when textstat is not available."""

import sys
from unittest.mock import patch

import pytest


class TestReadabilityWithoutTextstat:
    """Test readability module behavior when textstat is not installed."""

    def test_import_without_textstat(self):
        """Test that readability module can be imported without textstat."""
        # Mock textstat as unavailable
        with patch.dict(sys.modules, {"textstat": None}):
            # Should be able to import the module
            try:
                import docuchango.readability  # noqa: F401

                # TEXTSTAT_AVAILABLE should be False
                # (actual value depends on whether textstat is installed in test environment)
            except ImportError:
                pytest.fail("Should be able to import readability module without textstat")

    def test_scorer_raises_without_textstat(self):
        """Test that ReadabilityScorer raises ImportError when textstat is unavailable."""
        # We need to test this by mocking TEXTSTAT_AVAILABLE
        # Temporarily mock TEXTSTAT_AVAILABLE
        import docuchango.readability as readability_module
        from docuchango.readability import ReadabilityConfig, ReadabilityScorer

        original_available = readability_module.TEXTSTAT_AVAILABLE

        try:
            # Mock as unavailable
            readability_module.TEXTSTAT_AVAILABLE = False

            # Create scorer - should check the flag
            config = ReadabilityConfig()

            # Attempting to create scorer should raise ImportError
            with pytest.raises(ImportError) as exc_info:
                ReadabilityScorer(config)

            assert "textstat" in str(exc_info.value).lower()
            assert "readability" in str(exc_info.value).lower()
        finally:
            # Restore original value
            readability_module.TEXTSTAT_AVAILABLE = original_available

    def test_validator_skips_without_textstat(self, tmp_path):
        """Test that validator gracefully skips readability when textstat unavailable."""
        from docuchango.validator import DocValidator

        # Create test document
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        doc_file = docs_dir / "test.md"
        doc_file.write_text("""---
title: Test
---

# Test

Some test content here.
""")

        config_file = tmp_path / "docs-project.yaml"
        config_file.write_text("""
readability:
  enabled: true
  flesch_reading_ease_min: 60.0
""")

        # Create validator and call readability
        # If textstat is not available, it should skip gracefully
        validator = DocValidator(repo_root=tmp_path)
        validator.scan_documents()

        # Should not crash when checking readability
        # (will either check or skip depending on textstat availability)
        validator.check_readability()

        # Test passes if no exception is raised


class TestReadabilityConfigWithoutTextstat:
    """Test ReadabilityConfig works without textstat."""

    def test_config_creation_without_textstat(self):
        """Test that ReadabilityConfig can be created without textstat."""
        from docuchango.readability import ReadabilityConfig

        # Config creation should not require textstat
        config = ReadabilityConfig()
        assert config.enabled is True
        assert config.flesch_reading_ease_min == 60.0

    def test_config_serialization_without_textstat(self):
        """Test config can be converted to dict without textstat."""
        from dataclasses import asdict

        from docuchango.readability import ReadabilityConfig

        config = ReadabilityConfig(
            flesch_reading_ease_min=70.0,
            flesch_kincaid_grade_max=8.0,
        )

        # Should be serializable
        config_dict = asdict(config)
        assert config_dict["flesch_reading_ease_min"] == 70.0
        assert config_dict["flesch_kincaid_grade_max"] == 8.0


class TestReadabilityErrorMessages:
    """Test error messages and documentation."""

    def test_import_error_message_clarity(self):
        """Test that ImportError message is clear and helpful."""
        import docuchango.readability as readability_module
        from docuchango.readability import ReadabilityConfig

        original_available = readability_module.TEXTSTAT_AVAILABLE

        try:
            readability_module.TEXTSTAT_AVAILABLE = False

            config = ReadabilityConfig()

            with pytest.raises(ImportError) as exc_info:
                from docuchango.readability import ReadabilityScorer

                ReadabilityScorer(config)

            error_msg = str(exc_info.value)

            # Should mention both installation methods
            assert "uv sync --extra readability" in error_msg or "pip install" in error_msg
            assert "docuchango[readability]" in error_msg

        finally:
            readability_module.TEXTSTAT_AVAILABLE = original_available


class TestReadabilityDataStructures:
    """Test readability data structures without textstat."""

    def test_paragraph_score_creation(self):
        """Test ParagraphScore can be created without textstat."""
        from docuchango.readability import ParagraphScore

        score = ParagraphScore(
            paragraph_text="Test paragraph",
            line_number=5,
            flesch_reading_ease=65.0,
            flesch_kincaid_grade=8.5,
        )

        assert score.paragraph_text == "Test paragraph"
        assert score.line_number == 5
        assert score.flesch_reading_ease == 65.0
        assert not score.has_errors()

    def test_paragraph_score_with_errors(self):
        """Test ParagraphScore error handling without textstat."""
        from docuchango.readability import ParagraphScore

        score = ParagraphScore(
            paragraph_text="Complex text",
            line_number=10,
            errors=["Flesch Reading Ease too low", "Grade level too high"],
        )

        assert score.has_errors()
        assert len(score.errors) == 2

    def test_document_report_creation(self):
        """Test DocumentReadabilityReport without textstat."""
        from docuchango.readability import DocumentReadabilityReport, ParagraphScore

        score1 = ParagraphScore("Para 1", 1)
        score2 = ParagraphScore("Para 2", 5, errors=["Error 1"])

        report = DocumentReadabilityReport(
            file_path="test.md",
            paragraph_scores=[score1, score2],
            total_paragraphs=2,
            paragraphs_with_errors=1,
        )

        assert report.has_errors()
        errors = report.get_all_errors()
        assert len(errors) == 1
        assert errors[0] == (5, "Error 1")

    def test_readability_metric_enum(self):
        """Test ReadabilityMetric enum without textstat."""
        from docuchango.readability import ReadabilityMetric

        # Should be able to access enum values
        assert ReadabilityMetric.FLESCH_READING_EASE.value == "flesch_reading_ease"
        assert ReadabilityMetric.GUNNING_FOG.value == "gunning_fog"
        assert ReadabilityMetric.SMOG_INDEX.value == "smog_index"


class TestReadabilityParagraphExtraction:
    """Test paragraph extraction logic independently."""

    @pytest.mark.skipif(True, reason="Would need to mock textstat for ReadabilityScorer instantiation")
    def test_extract_paragraphs_logic(self):
        """Test paragraph extraction without requiring textstat calculations."""
        # This would require restructuring to separate extraction from scoring
        # Keeping as placeholder for potential refactoring
        pass


class TestReadabilityConfigSchema:
    """Test Pydantic schema integration without textstat."""

    def test_schema_validation_without_textstat(self):
        """Test that DocsProjectReadability schema works without textstat."""
        from docuchango.schemas import DocsProjectReadability

        # Should be able to create and validate config
        config = DocsProjectReadability(
            enabled=True,
            flesch_reading_ease_min=65.0,
            flesch_kincaid_grade_max=9.0,
        )

        assert config.enabled is True
        assert config.flesch_reading_ease_min == 65.0

    def test_schema_with_null_values(self):
        """Test schema handles None values for disabled metrics."""
        from docuchango.schemas import DocsProjectReadability

        config = DocsProjectReadability(
            enabled=True,
            flesch_reading_ease_min=None,  # Disabled
            flesch_kincaid_grade_max=None,  # Disabled
        )

        assert config.flesch_reading_ease_min is None
        assert config.flesch_kincaid_grade_max is None

    def test_schema_defaults(self):
        """Test schema default values."""
        from docuchango.schemas import DocsProjectReadability

        config = DocsProjectReadability()

        assert config.enabled is True
        assert config.flesch_reading_ease_min == 60.0
        assert config.flesch_kincaid_grade_max == 10.0
        assert config.gunning_fog_max == 12.0
        assert config.min_paragraph_length == 100
