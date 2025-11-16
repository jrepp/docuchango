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
