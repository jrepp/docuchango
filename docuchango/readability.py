"""Readability scoring for documentation using textstat library.

This module analyzes markdown documents for readability using multiple established
readability metrics. It processes each paragraph of readable text and reports scores
that fall below configured thresholds.

Supported Metrics:
- Flesch Reading Ease: 0-100+ (higher = easier)
- Flesch-Kincaid Grade Level: US grade level required
- Gunning FOG Index: Years of formal education needed
- SMOG Index: Grade level required (requires 3+ sentences)
- Automated Readability Index (ARI): Grade level approximation
- Coleman-Liau Index: Grade level using character-based metrics
- Dale-Chall Readability Score: Grade level using common words
- Text Standard: Consensus grade level across tests

Usage:
    from docuchango.readability import ReadabilityScorer, ReadabilityConfig

    config = ReadabilityConfig(
        flesch_reading_ease_min=60.0,
        flesch_kincaid_grade_max=10.0
    )
    scorer = ReadabilityScorer(config)
    results = scorer.analyze_document(markdown_content)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

try:
    import textstat  # type: ignore[import-untyped]

    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    # Make textstat optional - readability features will be disabled if not available
    textstat = None  # type: ignore[assignment]


class ReadabilityMetric(Enum):
    """Available readability metrics."""

    FLESCH_READING_EASE = "flesch_reading_ease"
    FLESCH_KINCAID_GRADE = "flesch_kincaid_grade"
    GUNNING_FOG = "gunning_fog"
    SMOG_INDEX = "smog_index"
    AUTOMATED_READABILITY_INDEX = "automated_readability_index"
    COLEMAN_LIAU_INDEX = "coleman_liau_index"
    DALE_CHALL = "dale_chall"
    TEXT_STANDARD = "text_standard"


@dataclass
class ReadabilityConfig:
    """Configuration for readability thresholds.

    Thresholds determine when a paragraph fails readability checks.
    Set thresholds to None to disable that metric.

    Flesch Reading Ease ranges (higher = easier):
    - 90-100: Very Easy (5th grade)
    - 80-90: Easy (6th grade)
    - 70-80: Fairly Easy (7th grade)
    - 60-70: Standard (8th-9th grade)
    - 50-60: Fairly Difficult (10th-12th grade)
    - 30-50: Difficult (College)
    - 0-30: Very Difficult (College graduate)

    Grade-level metrics (Flesch-Kincaid, Gunning FOG, etc.):
    - Lower is easier (e.g., 8.0 = 8th grade level)
    - Technical documentation typically 10-12
    - General audience documentation should be 8-10
    """

    enabled: bool = True
    # Flesch Reading Ease: minimum score (higher = easier)
    flesch_reading_ease_min: Optional[float] = 60.0
    # Grade-level metrics: maximum grade level (lower = easier)
    flesch_kincaid_grade_max: Optional[float] = 10.0
    gunning_fog_max: Optional[float] = 12.0
    smog_index_max: Optional[float] = 12.0
    automated_readability_index_max: Optional[float] = 10.0
    coleman_liau_index_max: Optional[float] = 10.0
    dale_chall_max: Optional[float] = 9.0
    # Minimum paragraph length to analyze (in characters)
    min_paragraph_length: int = 100


@dataclass
class ParagraphScore:
    """Readability scores for a single paragraph."""

    paragraph_text: str
    line_number: int
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    gunning_fog: Optional[float] = None
    smog_index: Optional[float] = None
    automated_readability_index: Optional[float] = None
    coleman_liau_index: Optional[float] = None
    dale_chall: Optional[float] = None
    text_standard: Optional[str] = None
    errors: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if paragraph has any readability errors."""
        return len(self.errors) > 0


@dataclass
class DocumentReadabilityReport:
    """Complete readability analysis for a document."""

    file_path: str
    paragraph_scores: list[ParagraphScore] = field(default_factory=list)
    total_paragraphs: int = 0
    paragraphs_with_errors: int = 0

    def has_errors(self) -> bool:
        """Check if document has any readability errors."""
        return self.paragraphs_with_errors > 0

    def get_all_errors(self) -> list[tuple[int, str]]:
        """Get all errors as (line_number, error_message) tuples."""
        errors = []
        for score in self.paragraph_scores:
            for error in score.errors:
                errors.append((score.line_number, error))
        return errors


class ReadabilityScorer:
    """Analyzes document readability using multiple metrics."""

    def __init__(self, config: ReadabilityConfig):
        """Initialize scorer with configuration.

        Args:
            config: Readability configuration with thresholds
        """
        self.config = config
        if not TEXTSTAT_AVAILABLE:
            raise ImportError("textstat library is required for readability analysis. Install it with: uv sync")

    def extract_paragraphs(self, markdown_content: str) -> list[tuple[str, int]]:
        """Extract readable paragraphs from markdown content.

        Filters out:
        - Code blocks (fenced with ``` or indented)
        - Frontmatter (YAML between ---)
        - Headings
        - Lists (for now, can be configured later)
        - HTML/MDX tags

        Returns:
            List of (paragraph_text, line_number) tuples
        """
        lines = markdown_content.split("\n")
        paragraphs = []
        current_paragraph: list[str] = []
        current_paragraph_start_line = 0
        in_code_block = False
        in_frontmatter = False
        frontmatter_count = 0

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track frontmatter
            if stripped == "---":
                frontmatter_count += 1
                if frontmatter_count <= 2:
                    in_frontmatter = frontmatter_count == 1
                    continue

            if in_frontmatter:
                continue

            # Track code blocks
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                # Flush current paragraph when entering code block
                if in_code_block and current_paragraph:
                    para_text = " ".join(current_paragraph).strip()
                    if len(para_text) >= self.config.min_paragraph_length:
                        paragraphs.append((para_text, current_paragraph_start_line))
                    current_paragraph = []
                continue

            if in_code_block:
                continue

            # Skip headings, lists, empty lines, HTML comments
            if (
                stripped.startswith("#")
                or stripped.startswith("-")
                or stripped.startswith("*")
                or stripped.startswith("+")
                or stripped.startswith(">")  # blockquotes
                or stripped.startswith("<")  # HTML/MDX tags
                or stripped.startswith("<!--")
                or not stripped
            ):
                # Flush current paragraph
                if current_paragraph:
                    para_text = " ".join(current_paragraph).strip()
                    if len(para_text) >= self.config.min_paragraph_length:
                        paragraphs.append((para_text, current_paragraph_start_line))
                    current_paragraph = []
                continue

            # Start new paragraph if this is the first line
            if not current_paragraph:
                current_paragraph_start_line = i

            # Add line to current paragraph
            current_paragraph.append(stripped)

        # Flush final paragraph
        if current_paragraph:
            para_text = " ".join(current_paragraph).strip()
            if len(para_text) >= self.config.min_paragraph_length:
                paragraphs.append((para_text, current_paragraph_start_line))

        return paragraphs

    def score_paragraph(self, text: str, line_number: int) -> ParagraphScore:
        """Calculate readability scores for a single paragraph.

        Args:
            text: Paragraph text to analyze
            line_number: Line number where paragraph starts

        Returns:
            ParagraphScore with all metrics and threshold violations
        """
        score = ParagraphScore(paragraph_text=text, line_number=line_number)

        # Calculate all metrics
        try:
            score.flesch_reading_ease = textstat.flesch_reading_ease(text)
        except Exception:
            pass  # Metric may fail on very short text

        try:
            score.flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
        except Exception:
            pass

        try:
            score.gunning_fog = textstat.gunning_fog(text)
        except Exception:
            pass

        try:
            score.smog_index = textstat.smog_index(text)
        except Exception:
            pass

        try:
            score.automated_readability_index = textstat.automated_readability_index(text)
        except Exception:
            pass

        try:
            score.coleman_liau_index = textstat.coleman_liau_index(text)
        except Exception:
            pass

        try:
            score.dale_chall = textstat.dale_chall_readability_score(text)
        except Exception:
            pass

        try:
            score.text_standard = textstat.text_standard(text, float_output=False)
        except Exception:
            pass

        # Check thresholds
        if self.config.flesch_reading_ease_min is not None and score.flesch_reading_ease is not None:
            if score.flesch_reading_ease < self.config.flesch_reading_ease_min:
                score.errors.append(
                    f"Flesch Reading Ease score {score.flesch_reading_ease:.1f} "
                    f"below minimum {self.config.flesch_reading_ease_min} (harder to read)"
                )

        if self.config.flesch_kincaid_grade_max is not None and score.flesch_kincaid_grade is not None:
            if score.flesch_kincaid_grade > self.config.flesch_kincaid_grade_max:
                score.errors.append(
                    f"Flesch-Kincaid grade level {score.flesch_kincaid_grade:.1f} "
                    f"exceeds maximum {self.config.flesch_kincaid_grade_max}"
                )

        if self.config.gunning_fog_max is not None and score.gunning_fog is not None:
            if score.gunning_fog > self.config.gunning_fog_max:
                score.errors.append(
                    f"Gunning FOG index {score.gunning_fog:.1f} exceeds maximum {self.config.gunning_fog_max}"
                )

        if self.config.smog_index_max is not None and score.smog_index is not None:
            if score.smog_index > self.config.smog_index_max:
                score.errors.append(f"SMOG index {score.smog_index:.1f} exceeds maximum {self.config.smog_index_max}")

        if self.config.automated_readability_index_max is not None and score.automated_readability_index is not None:
            if score.automated_readability_index > self.config.automated_readability_index_max:
                score.errors.append(
                    f"Automated Readability Index {score.automated_readability_index:.1f} "
                    f"exceeds maximum {self.config.automated_readability_index_max}"
                )

        if self.config.coleman_liau_index_max is not None and score.coleman_liau_index is not None:
            if score.coleman_liau_index > self.config.coleman_liau_index_max:
                score.errors.append(
                    f"Coleman-Liau index {score.coleman_liau_index:.1f} "
                    f"exceeds maximum {self.config.coleman_liau_index_max}"
                )

        if self.config.dale_chall_max is not None and score.dale_chall is not None:
            if score.dale_chall > self.config.dale_chall_max:
                score.errors.append(
                    f"Dale-Chall score {score.dale_chall:.1f} exceeds maximum {self.config.dale_chall_max}"
                )

        return score

    def analyze_document(self, markdown_content: str, file_path: str = "") -> DocumentReadabilityReport:
        """Analyze complete document for readability.

        Args:
            markdown_content: Markdown document content
            file_path: Optional file path for reporting

        Returns:
            DocumentReadabilityReport with all paragraph scores
        """
        if not self.config.enabled:
            return DocumentReadabilityReport(file_path=file_path)

        report = DocumentReadabilityReport(file_path=file_path)
        paragraphs = self.extract_paragraphs(markdown_content)
        report.total_paragraphs = len(paragraphs)

        for para_text, line_num in paragraphs:
            score = self.score_paragraph(para_text, line_num)
            report.paragraph_scores.append(score)
            if score.has_errors():
                report.paragraphs_with_errors += 1

        return report
