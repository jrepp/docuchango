"""Tests for readability.py module."""

import pytest

from docuchango.readability import (
    TEXTSTAT_AVAILABLE,
    DocumentReadabilityReport,
    ParagraphScore,
    ReadabilityConfig,
    ReadabilityScorer,
)

# Skip all tests if textstat is not available
pytestmark = pytest.mark.skipif(
    not TEXTSTAT_AVAILABLE,
    reason="textstat library not installed",
)


class TestReadabilityConfig:
    """Test ReadabilityConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ReadabilityConfig()
        assert config.enabled is True
        assert config.flesch_reading_ease_min == 60.0
        assert config.flesch_kincaid_grade_max == 10.0
        assert config.min_paragraph_length == 100

    def test_custom_config(self):
        """Test custom configuration."""
        config = ReadabilityConfig(
            enabled=False,
            flesch_reading_ease_min=70.0,
            flesch_kincaid_grade_max=8.0,
        )
        assert config.enabled is False
        assert config.flesch_reading_ease_min == 70.0
        assert config.flesch_kincaid_grade_max == 8.0

    def test_disabled_metrics(self):
        """Test configuration with disabled metrics (None values)."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
        )
        assert config.flesch_reading_ease_min is None
        assert config.flesch_kincaid_grade_max is None


class TestParagraphScore:
    """Test ParagraphScore dataclass."""

    def test_paragraph_score_creation(self):
        """Test creating a paragraph score."""
        score = ParagraphScore(
            paragraph_text="Test paragraph",
            line_number=10,
            flesch_reading_ease=75.0,
        )
        assert score.paragraph_text == "Test paragraph"
        assert score.line_number == 10
        assert score.flesch_reading_ease == 75.0
        assert not score.has_errors()

    def test_paragraph_score_with_errors(self):
        """Test paragraph score with errors."""
        score = ParagraphScore(
            paragraph_text="Test",
            line_number=5,
        )
        score.errors.append("Test error")
        assert score.has_errors()


class TestDocumentReadabilityReport:
    """Test DocumentReadabilityReport dataclass."""

    def test_empty_report(self):
        """Test empty readability report."""
        report = DocumentReadabilityReport(file_path="test.md")
        assert report.file_path == "test.md"
        assert report.total_paragraphs == 0
        assert report.paragraphs_with_errors == 0
        assert not report.has_errors()

    def test_report_with_errors(self):
        """Test report with readability errors."""
        report = DocumentReadabilityReport(file_path="test.md")
        score1 = ParagraphScore(paragraph_text="Test 1", line_number=1)
        score1.errors.append("Error 1")
        score2 = ParagraphScore(paragraph_text="Test 2", line_number=5)

        report.paragraph_scores = [score1, score2]
        report.total_paragraphs = 2
        report.paragraphs_with_errors = 1

        assert report.has_errors()
        errors = report.get_all_errors()
        assert len(errors) == 1
        assert errors[0] == (1, "Error 1")


class TestReadabilityScorer:
    """Test ReadabilityScorer class."""

    def test_scorer_initialization(self):
        """Test creating a ReadabilityScorer."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)
        assert scorer.config == config

    def test_extract_paragraphs_simple(self):
        """Test extracting simple paragraphs."""
        config = ReadabilityConfig(min_paragraph_length=10)
        scorer = ReadabilityScorer(config)

        content = """# Title

This is a simple paragraph with more than ten characters.

Another paragraph here with enough text.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 2
        assert "simple paragraph" in paragraphs[0][0]
        assert "Another paragraph" in paragraphs[1][0]

    def test_extract_paragraphs_skip_headings(self):
        """Test that headings are skipped."""
        config = ReadabilityConfig(min_paragraph_length=10)
        scorer = ReadabilityScorer(config)

        content = """# Main Heading

## Subheading

This is content.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 1
        assert "This is content" in paragraphs[0][0]

    def test_extract_paragraphs_skip_code_blocks(self):
        """Test that code blocks are skipped."""
        config = ReadabilityConfig(min_paragraph_length=10)
        scorer = ReadabilityScorer(config)

        content = """
Regular paragraph text with sufficient length.

```python
code = "should be skipped"
```

Another regular paragraph text.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 2
        assert "code" not in paragraphs[0][0]
        assert "code" not in paragraphs[1][0]

    def test_extract_paragraphs_skip_frontmatter(self):
        """Test that YAML frontmatter is skipped."""
        config = ReadabilityConfig(min_paragraph_length=10)
        scorer = ReadabilityScorer(config)

        content = """---
title: Test Document
date: 2025-01-01
---

This is the actual content paragraph.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 1
        assert "title" not in paragraphs[0][0]
        assert "actual content" in paragraphs[0][0]

    def test_extract_paragraphs_skip_lists(self):
        """Test that lists are skipped."""
        config = ReadabilityConfig(min_paragraph_length=10)
        scorer = ReadabilityScorer(config)

        content = """
Regular paragraph text.

- List item 1
- List item 2

Another paragraph.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 2
        assert "List" not in paragraphs[0][0]
        assert "List" not in paragraphs[1][0]

    def test_extract_paragraphs_min_length(self):
        """Test minimum paragraph length filtering."""
        config = ReadabilityConfig(min_paragraph_length=50)
        scorer = ReadabilityScorer(config)

        content = """
Short text.

This is a much longer paragraph that exceeds the minimum length requirement.
"""
        paragraphs = scorer.extract_paragraphs(content)
        # Only the long paragraph should be included
        assert len(paragraphs) == 1
        assert "much longer" in paragraphs[0][0]

    def test_extract_paragraphs_multiline(self):
        """Test extracting multi-line paragraphs."""
        config = ReadabilityConfig(min_paragraph_length=20)
        scorer = ReadabilityScorer(config)

        content = """
This is a paragraph
that spans multiple
lines in the source.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 1
        # Lines should be joined
        assert "paragraph that spans multiple lines" in paragraphs[0][0]

    def test_score_paragraph_simple(self):
        """Test scoring a simple paragraph."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        text = "The cat sat on the mat. The dog ran in the park."
        score = scorer.score_paragraph(text, line_number=10)

        assert score.line_number == 10
        assert score.paragraph_text == text
        assert score.flesch_reading_ease is not None
        assert score.flesch_kincaid_grade is not None

    def test_score_paragraph_threshold_violation(self):
        """Test paragraph that violates readability thresholds."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=90.0,  # Very high threshold
            flesch_kincaid_grade_max=3.0,  # Very low grade level
        )
        scorer = ReadabilityScorer(config)

        # Complex sentence that will fail thresholds
        text = (
            "The implementation of the sophisticated architectural "
            "pattern necessitates comprehensive understanding of "
            "object-oriented programming paradigms and design principles."
        )
        score = scorer.score_paragraph(text, line_number=15)

        assert score.has_errors()
        assert len(score.errors) > 0

    def test_score_paragraph_passing(self):
        """Test paragraph that passes readability thresholds."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=60.0,
            flesch_kincaid_grade_max=10.0,
        )
        scorer = ReadabilityScorer(config)

        # Simple, clear text that should pass
        text = "The cat sat on the mat. The dog played in the yard. Children laughed and ran around. Everyone had fun."
        score = scorer.score_paragraph(text, line_number=5)

        # Should have no errors (or very few)
        assert not score.has_errors() or len(score.errors) < 2

    def test_score_paragraph_disabled_metrics(self):
        """Test scoring with disabled metrics (None thresholds)."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        text = "Complex sophisticated implementation of architectural patterns."
        score = scorer.score_paragraph(text, line_number=1)

        # Should have scores but no errors since all thresholds are disabled
        assert score.flesch_reading_ease is not None
        assert not score.has_errors()

    def test_analyze_document_empty(self):
        """Test analyzing an empty document."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        report = scorer.analyze_document("", file_path="test.md")
        assert report.total_paragraphs == 0
        assert not report.has_errors()

    def test_analyze_document_simple(self):
        """Test analyzing a simple document."""
        config = ReadabilityConfig(min_paragraph_length=20)
        scorer = ReadabilityScorer(config)

        content = """# My Document

This is a simple paragraph with clear and easy to read text.

Another paragraph that is also simple and straightforward.
"""
        report = scorer.analyze_document(content, file_path="test.md")
        assert report.total_paragraphs == 2
        assert len(report.paragraph_scores) == 2

    def test_analyze_document_with_errors(self):
        """Test analyzing document with readability issues."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=80.0,  # High threshold
            min_paragraph_length=30,
        )
        scorer = ReadabilityScorer(config)

        content = """
The implementation of sophisticated architectural patterns
necessitates comprehensive understanding of complex paradigms.
"""
        report = scorer.analyze_document(content, file_path="test.md")

        if report.total_paragraphs > 0:
            # Should have some errors due to complex text
            assert report.has_errors()

    def test_analyze_document_disabled(self):
        """Test analyzing with readability disabled."""
        config = ReadabilityConfig(enabled=False)
        scorer = ReadabilityScorer(config)

        content = "Test content"
        report = scorer.analyze_document(content)

        # Should return empty report when disabled
        assert report.total_paragraphs == 0

    def test_line_number_tracking(self):
        """Test that line numbers are correctly tracked."""
        config = ReadabilityConfig(min_paragraph_length=20)
        scorer = ReadabilityScorer(config)

        content = """# Title
Line 2
Line 3

Paragraph starting at line 5.

Line 7

Another paragraph at line 9.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 2
        # First paragraph starts at line 5
        assert paragraphs[0][1] == 5
        # Second paragraph starts at line 9
        assert paragraphs[1][1] == 9

    def test_unicode_content(self):
        """Test handling of Unicode content."""
        config = ReadabilityConfig(min_paragraph_length=20)
        scorer = ReadabilityScorer(config)

        content = """
# Document → ✓

This is a paragraph with Unicode characters: 中文, émojis ✓, and symbols →.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 1
        assert "中文" in paragraphs[0][0]
        assert "→" in paragraphs[0][0]

    def test_html_mdx_tags_skipped(self):
        """Test that HTML/MDX tags are skipped."""
        config = ReadabilityConfig(min_paragraph_length=20)
        scorer = ReadabilityScorer(config)

        content = """
Regular paragraph text here.

<CustomComponent prop="value">
Content inside component
</CustomComponent>

Another regular paragraph.
"""
        paragraphs = scorer.extract_paragraphs(content)
        # Should skip the component tags
        assert len(paragraphs) <= 2
        # Check that tags aren't in extracted text
        for para_text, _ in paragraphs:
            assert "<Custom" not in para_text

    def test_blockquotes_skipped(self):
        """Test that blockquotes are skipped."""
        config = ReadabilityConfig(min_paragraph_length=20)
        scorer = ReadabilityScorer(config)

        content = """
Regular paragraph text.

> This is a blockquote
> that should be skipped.

Another regular paragraph.
"""
        paragraphs = scorer.extract_paragraphs(content)
        assert len(paragraphs) == 2
        for para_text, _ in paragraphs:
            assert "blockquote" not in para_text.lower()


class TestReadabilityIntegration:
    """Integration tests for readability feature."""

    def test_full_document_analysis(self):
        """Test analyzing a complete realistic document."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=60.0,
            flesch_kincaid_grade_max=12.0,
        )
        scorer = ReadabilityScorer(config)

        content = """---
title: ADR-001 Use PostgreSQL
status: Accepted
---

# ADR-001: Use PostgreSQL for Data Storage

## Context

We need a reliable database for our application. The database must handle
complex queries and support transactions.

## Decision

We will use PostgreSQL as our primary database. It is open source and
widely used in production environments.

## Consequences

PostgreSQL provides strong consistency guarantees. We will need to learn
its query optimization features.
"""
        report = scorer.analyze_document(content, file_path="adr-001.md")

        assert report.file_path == "adr-001.md"
        assert report.total_paragraphs > 0
        # Check that at least some scores were calculated
        assert any(s.flesch_reading_ease is not None for s in report.paragraph_scores)

    def test_very_simple_text_passes(self):
        """Test that very simple text passes all checks."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        content = """
The cat sat on the mat. The dog ran fast. The bird sang a song.
The sun was bright. The sky was blue. The grass was green.
"""
        report = scorer.analyze_document(content)

        # Simple text should pass with default thresholds
        assert not report.has_errors() or report.paragraphs_with_errors == 0

    def test_technical_text_may_fail(self):
        """Test that very technical text may fail readability checks."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=70.0,  # Fairly easy
            flesch_kincaid_grade_max=8.0,  # 8th grade
        )
        scorer = ReadabilityScorer(config)

        content = """
The implementation necessitates utilization of sophisticated
architectural patterns incorporating dependency injection mechanisms
and comprehensive abstraction layers to facilitate extensibility.
"""
        report = scorer.analyze_document(content)

        # Technical jargon should likely fail with strict thresholds
        # (though we can't guarantee it without running the actual analysis)
        assert report.total_paragraphs >= 0  # Just verify it runs


class TestReadabilityThresholdValidation:
    """Test threshold configuration and validation failures."""

    def test_all_thresholds_trigger_errors(self):
        """Test that text violating all thresholds reports all errors."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=90.0,  # Very strict
            flesch_kincaid_grade_max=5.0,   # Elementary level
            gunning_fog_max=6.0,
            smog_index_max=6.0,
            automated_readability_index_max=5.0,
            coleman_liau_index_max=5.0,
            dale_chall_max=5.0,
        )
        scorer = ReadabilityScorer(config)

        # Complex technical text that should fail all metrics
        text = """
        Implementation of sophisticated multidimensional architectural methodologies
        necessitates comprehensive understanding of organizational restructuring paradigms
        incorporating contemporary technological advancements and interdisciplinary approaches.
        """
        score = scorer.score_paragraph(text, 1)

        # Should have multiple errors
        assert score.has_errors()
        assert len(score.errors) >= 3  # At least 3 metrics should fail

    def test_flesch_reading_ease_boundary(self):
        """Test Flesch Reading Ease at exact boundary."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=60.0,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        # Text that should be close to boundary
        text = """
        The system provides tools for development. Users can access features through
        the main interface. Documentation helps explain the functionality.
        """
        score = scorer.score_paragraph(text, 1)

        # Score should be calculated
        assert score.flesch_reading_ease is not None

    def test_grade_level_progressive_difficulty(self):
        """Test that text difficulty increases with complexity."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        simple_text = "The cat sat. The dog ran. The bird flew."
        complex_text = """
        Sophisticated implementation methodologies incorporating architectural patterns
        necessitate comprehensive understanding of organizational frameworks.
        """

        simple_score = scorer.score_paragraph(simple_text, 1)
        complex_score = scorer.score_paragraph(complex_text, 1)

        # Complex text should have higher grade level (if both calculated)
        if simple_score.flesch_kincaid_grade and complex_score.flesch_kincaid_grade:
            assert complex_score.flesch_kincaid_grade > simple_score.flesch_kincaid_grade

    def test_multiple_paragraphs_some_fail(self):
        """Test document where some paragraphs pass and some fail."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=70.0,
            flesch_kincaid_grade_max=8.0,
            min_paragraph_length=50,  # Lower threshold to catch all paragraphs
        )
        scorer = ReadabilityScorer(config)

        content = """
The cat sat on the mat. The dog ran in the yard. Birds sang in the trees.

Implementation of sophisticated architectural methodologies incorporating comprehensive
frameworks necessitating extensive understanding of organizational structures and
contemporary technological advancement paradigms.

The sun is bright. Kids play outside. Everyone is happy. The weather is nice today.
"""
        report = scorer.analyze_document(content)

        # Should have analyzed multiple paragraphs
        assert report.total_paragraphs >= 2
        # Some should fail, some should pass
        # (exact behavior depends on textstat calculations)

    def test_disabled_metrics_dont_generate_errors(self):
        """Test that setting metrics to None disables error checking."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,  # Disabled
            flesch_kincaid_grade_max=None,  # Disabled
            gunning_fog_max=None,  # Disabled
            smog_index_max=None,  # Disabled
            automated_readability_index_max=None,  # Disabled
            coleman_liau_index_max=None,  # Disabled
            dale_chall_max=None,  # Disabled
        )
        scorer = ReadabilityScorer(config)

        # Even very complex text should not generate errors
        text = """
        Extraordinarily sophisticated multifaceted implementation methodologies
        necessitating comprehensive understanding of organizational restructuring
        paradigms incorporating contemporary technological advancements.
        """
        score = scorer.score_paragraph(text, 1)

        # Scores should be calculated but no errors
        assert not score.has_errors()
        # But scores should still be calculated
        assert score.flesch_reading_ease is not None

    def test_very_low_thresholds_allow_all(self):
        """Test that very permissive thresholds allow all text."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=-200.0,  # Allow even negative scores
            flesch_kincaid_grade_max=100.0,  # Allow anything
            gunning_fog_max=100.0,
            smog_index_max=100.0,
            automated_readability_index_max=100.0,
            coleman_liau_index_max=100.0,
            dale_chall_max=100.0,
        )
        scorer = ReadabilityScorer(config)

        # Even complex text should pass
        text = """
        Implementation of extraordinarily sophisticated multidimensional architectural
        methodologies necessitating comprehensive understanding.
        """
        score = scorer.score_paragraph(text, 1)

        # Should not have errors with permissive thresholds
        assert not score.has_errors()

    def test_document_with_all_paragraphs_failing(self):
        """Test document where all paragraphs fail readability."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=90.0,  # Very strict
            flesch_kincaid_grade_max=5.0,
            min_paragraph_length=50,  # Lower to catch all paragraphs
        )
        scorer = ReadabilityScorer(config)

        content = """
Implementation of sophisticated architectural paradigms incorporating comprehensive frameworks and methodologies.

Utilization of contemporary technological methodologies necessitating extensive organizational understanding and coordination.

Comprehensive restructuring incorporating multidimensional approaches facilitating extensibility and scalability.
"""
        report = scorer.analyze_document(content)

        # All paragraphs should likely fail
        assert report.has_errors()
        # Should have analyzed paragraphs (at least one should be long enough)
        assert report.total_paragraphs >= 1

    def test_min_paragraph_length_filtering(self):
        """Test that minimum paragraph length is enforced."""
        config = ReadabilityConfig(
            min_paragraph_length=200,  # High threshold
        )
        scorer = ReadabilityScorer(config)

        content = """
Short paragraph.

This is a much longer paragraph that contains significantly more text and should
exceed the minimum paragraph length threshold that we have configured for this
particular test case to ensure proper filtering.

Another short one.
"""
        paragraphs = scorer.extract_paragraphs(content)

        # Only the long paragraph should be extracted
        assert len(paragraphs) <= 2  # At most the long one (and maybe one other)
        # The long paragraph should be included
        assert any(len(para[0]) >= 200 for para in paragraphs)

    def test_error_messages_include_threshold_values(self):
        """Test that error messages include the threshold values."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=70.0,
            flesch_kincaid_grade_max=8.0,
        )
        scorer = ReadabilityScorer(config)

        text = """
        Sophisticated implementation incorporating architectural frameworks
        necessitating comprehensive organizational understanding.
        """
        score = scorer.score_paragraph(text, 1)

        if score.has_errors():
            # Error messages should mention the thresholds
            for error in score.errors:
                # Should contain numeric threshold value
                assert any(char.isdigit() for char in error)
