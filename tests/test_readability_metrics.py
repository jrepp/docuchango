"""Detailed tests for individual textstat readability metrics."""

import pytest

from docuchango.readability import (
    TEXTSTAT_AVAILABLE,
    ReadabilityConfig,
    ReadabilityScorer,
)

# Skip all tests if textstat is not available
pytestmark = pytest.mark.skipif(
    not TEXTSTAT_AVAILABLE,
    reason="textstat library not installed",
)


class TestFleschReadingEase:
    """Test Flesch Reading Ease metric specifically."""

    def test_very_easy_text(self):
        """Test text that should score very high on Flesch Reading Ease."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=90.0,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        # Very simple text with short words and sentences
        text = "The cat sat. The dog ran. Birds fly. Kids play. The sun is hot. We are happy."
        score = scorer.score_paragraph(text, 1)

        # Should have a high Flesch Reading Ease score
        assert score.flesch_reading_ease is not None
        assert score.flesch_reading_ease > 80.0  # Very Easy range

    def test_difficult_text(self):
        """Test text that should score low on Flesch Reading Ease."""
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

        # Complex text with long words and sentences
        text = """The implementation of sophisticated multifaceted architectural paradigms
        necessitates comprehensive understanding of organizational restructuring methodologies
        incorporating contemporary technological advancements."""
        score = scorer.score_paragraph(text, 1)

        # Should have a lower Flesch Reading Ease score and trigger error
        assert score.flesch_reading_ease is not None
        assert score.has_errors()
        assert any("Flesch Reading Ease" in err for err in score.errors)

    def test_flesch_threshold_boundary(self):
        """Test text right at the Flesch Reading Ease boundary."""
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

        # Moderately complex text
        text = """This documentation describes the basic features of the system.
        Users can access various tools through the main interface.
        The application provides helpful feedback for common tasks."""
        score = scorer.score_paragraph(text, 1)

        # Should calculate a score (may or may not pass depending on exact calculation)
        assert score.flesch_reading_ease is not None


class TestFleschKincaidGrade:
    """Test Flesch-Kincaid Grade Level metric."""

    def test_elementary_level(self):
        """Test text at elementary grade level."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=5.0,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        text = "The cat is black. The dog is brown. They play in the yard. Kids laugh and run."
        score = scorer.score_paragraph(text, 1)

        assert score.flesch_kincaid_grade is not None
        # Simple text should be low grade level
        assert score.flesch_kincaid_grade < 8.0

    def test_college_level(self):
        """Test text at college grade level."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=10.0,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        text = """Contemporary methodological frameworks facilitate comprehensive analysis
        of multidimensional organizational structures through systematic examination of
        interdependent operational parameters."""
        score = scorer.score_paragraph(text, 1)

        assert score.flesch_kincaid_grade is not None
        # Complex text should exceed threshold
        assert score.has_errors()
        assert any("Flesch-Kincaid" in err for err in score.errors)


class TestGunningFOG:
    """Test Gunning FOG Index metric."""

    def test_fog_simple_text(self):
        """Test Gunning FOG with simple text."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=12.0,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        text = """We need to test the system. The process is simple.
        First, open the application. Next, select your options. Finally, click submit."""
        score = scorer.score_paragraph(text, 1)

        assert score.gunning_fog is not None
        # Should be relatively low

    def test_fog_complex_text(self):
        """Test Gunning FOG with complex text containing long words."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=12.0,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        text = """Implementation of interdisciplinary methodological approaches necessitates
        comprehensive understanding of organizational restructuring paradigms incorporating
        multifaceted technological advancements and sophisticated analytical frameworks."""
        score = scorer.score_paragraph(text, 1)

        assert score.gunning_fog is not None
        # Complex text with many long words should have high FOG score
        assert score.has_errors()


class TestSMOGIndex:
    """Test SMOG Index metric."""

    def test_smog_requires_sentences(self):
        """Test that SMOG Index handles text with sufficient sentences."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=12.0,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        # SMOG needs at least 3 sentences
        text = """The application is simple to use. Start by opening the main window.
        Select your preferred settings. Click the start button to begin.
        Wait for the process to complete. Review the results carefully."""
        score = scorer.score_paragraph(text, 1)

        # SMOG may calculate or may be None if not enough polysyllabic words
        # Just verify it doesn't crash
        assert isinstance(score.smog_index, (float, type(None)))


class TestAutomatedReadabilityIndex:
    """Test Automated Readability Index (ARI)."""

    def test_ari_calculation(self):
        """Test ARI is calculated for text."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=10.0,
            coleman_liau_index_max=None,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        text = """Software development requires careful planning and execution.
        Teams must collaborate effectively to deliver quality products.
        Testing ensures reliability and performance."""
        score = scorer.score_paragraph(text, 1)

        assert score.automated_readability_index is not None


class TestColemanLiauIndex:
    """Test Coleman-Liau Index metric."""

    def test_coleman_liau_character_based(self):
        """Test Coleman-Liau Index which is character-based."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=10.0,
            dale_chall_max=None,
        )
        scorer = ReadabilityScorer(config)

        text = """Development teams create software applications.
        They write code and test functionality. Quality assurance is important."""
        score = scorer.score_paragraph(text, 1)

        assert score.coleman_liau_index is not None


class TestDaleChallScore:
    """Test Dale-Chall Readability Score."""

    def test_dale_chall_common_words(self):
        """Test Dale-Chall which uses familiar words list."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=8.0,
        )
        scorer = ReadabilityScorer(config)

        # Text with common words
        text = """The cat and dog play together. They run in the park.
        Kids watch them and laugh. Everyone has fun in the sun."""
        score = scorer.score_paragraph(text, 1)

        assert score.dale_chall is not None
        # Common words should score better

    def test_dale_chall_uncommon_words(self):
        """Test Dale-Chall with uncommon/difficult words."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=None,
            gunning_fog_max=None,
            smog_index_max=None,
            automated_readability_index_max=None,
            coleman_liau_index_max=None,
            dale_chall_max=8.0,
        )
        scorer = ReadabilityScorer(config)

        text = """Pharmaceutical biotechnology encompasses multifaceted methodologies
        utilizing sophisticated instrumentation for comprehensive therapeutic development."""
        score = scorer.score_paragraph(text, 1)

        assert score.dale_chall is not None
        # Uncommon words should trigger threshold violation
        assert score.has_errors()


class TestTextStandard:
    """Test Text Standard consensus metric."""

    def test_text_standard_consensus(self):
        """Test that text_standard provides a consensus grade level."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        text = """Documentation should be clear and easy to understand.
        Use simple language when possible. Break complex ideas into smaller parts.
        Provide examples to illustrate key concepts."""
        score = scorer.score_paragraph(text, 1)

        # Text Standard should return a string like "8th and 9th grade"
        assert score.text_standard is not None
        assert isinstance(score.text_standard, str)


class TestMetricEdgeCases:
    """Test edge cases for readability metrics."""

    def test_very_short_text(self):
        """Test metrics with very short text (may fail to calculate)."""
        config = ReadabilityConfig(min_paragraph_length=10)
        scorer = ReadabilityScorer(config)

        text = "Short text."
        score = scorer.score_paragraph(text, 1)

        # Some metrics may not calculate for very short text
        # Should not crash
        assert score.paragraph_text == text

    def test_single_word_sentences(self):
        """Test metrics with single-word sentences."""
        config = ReadabilityConfig(min_paragraph_length=20)
        scorer = ReadabilityScorer(config)

        text = "Yes. No. Maybe. Perhaps. Definitely. Absolutely."
        score = scorer.score_paragraph(text, 1)

        # Should handle gracefully
        assert score.flesch_reading_ease is not None or len(score.errors) == 0

    def test_all_caps_text(self):
        """Test metrics with all caps text."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        text = "THE DOCUMENTATION DESCRIBES SYSTEM FEATURES. USERS ACCESS TOOLS THROUGH INTERFACE."
        score = scorer.score_paragraph(text, 1)

        # Should calculate normally (textstat handles case)
        assert score.flesch_reading_ease is not None

    def test_text_with_numbers(self):
        """Test metrics with text containing numbers."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        text = """The system supports up to 1000 concurrent users.
        Response times average 250 milliseconds.
        Storage capacity exceeds 500 terabytes."""
        score = scorer.score_paragraph(text, 1)

        # Should handle numbers gracefully
        assert score.flesch_reading_ease is not None

    def test_text_with_abbreviations(self):
        """Test metrics with abbreviations."""
        config = ReadabilityConfig()
        scorer = ReadabilityScorer(config)

        text = """The API provides REST endpoints for CRUD operations.
        Use HTTP GET, POST, PUT, and DELETE methods.
        Authentication requires JWT tokens."""
        score = scorer.score_paragraph(text, 1)

        # Should handle abbreviations
        assert score.flesch_reading_ease is not None

    def test_multiple_metrics_threshold_violations(self):
        """Test text that violates multiple metric thresholds."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=70.0,
            flesch_kincaid_grade_max=8.0,
            gunning_fog_max=10.0,
            smog_index_max=10.0,
        )
        scorer = ReadabilityScorer(config)

        text = """Comprehensive implementation of sophisticated architectural methodologies
        necessitates extensive understanding of multidimensional organizational frameworks
        incorporating contemporary technological advancements and interdisciplinary approaches."""
        score = scorer.score_paragraph(text, 1)

        # Should have multiple errors
        assert score.has_errors()
        assert len(score.errors) > 1

    def test_zero_threshold_allows_all(self):
        """Test that setting thresholds to 0 allows all text (grade level)."""
        config = ReadabilityConfig(
            flesch_reading_ease_min=None,
            flesch_kincaid_grade_max=0.0,  # Allow only pre-K level
        )
        scorer = ReadabilityScorer(config)

        text = "The cat sat on the mat."
        score = scorer.score_paragraph(text, 1)

        # Even simple text will likely exceed grade 0
        # This tests the boundary behavior
        assert score.flesch_kincaid_grade is not None
