# Document Readability Analysis

DocuChango now includes optional document readability analysis using the textstat library. This feature analyzes each paragraph of readable text and reports when they fall below configured readability thresholds.

## Installation

Install with readability support:

```bash
pip install docuchango[readability]
# or with uv
uv sync --extra readability
```

The readability feature is **optional**. If textstat is not installed, validation will skip readability checks without failing.

## Quick Start

Add readability configuration to your `docs-project.yaml`:

```yaml
readability:
  enabled: true
  flesch_reading_ease_min: 60.0  # 0-100, higher = easier
  flesch_kincaid_grade_max: 10.0  # Maximum US grade level
  gunning_fog_max: 12.0
  smog_index_max: 12.0
  automated_readability_index_max: 10.0
  coleman_liau_index_max: 10.0
  dale_chall_max: 9.0
  min_paragraph_length: 100  # Minimum characters to analyze
```

Run validation:

```bash
docuchango validate --verbose
```

## Supported Metrics

- **Flesch Reading Ease** (0-100): Higher scores = easier to read
  - 90-100: Very Easy (5th grade)
  - 80-90: Easy (6th grade)
  - 70-80: Fairly Easy (7th grade)
  - 60-70: Standard (8th-9th grade) ← Default threshold
  - 50-60: Fairly Difficult (10th-12th grade)
  - 30-50: Difficult (College)
  - 0-30: Very Difficult (College graduate)

- **Flesch-Kincaid Grade Level**: US grade level required (e.g., 10.0 = 10th grade)
- **Gunning FOG Index**: Years of formal education needed
- **SMOG Index**: Grade level (requires 3+ sentences)
- **Automated Readability Index (ARI)**: Grade level approximation
- **Coleman-Liau Index**: Character-based grade level
- **Dale-Chall Score**: Grade level using common words

## Configuration Examples

### Technical Documentation (Default)
Good for developer documentation, RFCs, ADRs:

```yaml
readability:
  enabled: true
  flesch_reading_ease_min: 60.0
  flesch_kincaid_grade_max: 10.0
```

### Consumer Documentation (Easier)
For user guides, help documentation:

```yaml
readability:
  enabled: true
  flesch_reading_ease_min: 70.0  # Fairly easy
  flesch_kincaid_grade_max: 8.0   # 8th grade
```

### Disable Specific Metrics
```yaml
readability:
  enabled: true
  flesch_reading_ease_min: 60.0
  flesch_kincaid_grade_max: null  # Disabled
  gunning_fog_max: null           # Disabled
```

### Disable Entirely
```yaml
readability:
  enabled: false
```

## What Gets Analyzed

The scorer **includes**:
- Regular paragraph text
- Multi-line paragraphs

The scorer **excludes**:
- Code blocks (fenced with ``` or indented)
- YAML frontmatter (--- delimited)
- Headings (# markers)
- Lists (-, *, + markers)
- Blockquotes (> marker)
- HTML/MDX tags
- Paragraphs shorter than `min_paragraph_length`

## Error Reporting

Errors show the exact line number and which threshold was violated:

```
📖 Checking readability...
   ✗ adr-001.md:45: Flesch Reading Ease score 45.2 below minimum 60.0 (harder to read)
   ✗ adr-001.md:45: Flesch-Kincaid grade level 12.3 exceeds maximum 10.0
   ✓ rfc-002.md: 5 paragraphs analyzed, all readable
```

## Tips for Writing Readable Documentation

1. **Use shorter sentences**: Break complex ideas into multiple sentences
2. **Prefer simple words**: "use" instead of "utilize", "help" instead of "facilitate"
3. **Active voice**: "We implemented X" instead of "X was implemented"
4. **Concrete examples**: Show, don't just tell
5. **One idea per paragraph**: Keep paragraphs focused

## Technical Details

- Analyses only paragraphs meeting minimum length (default 100 chars)
- Gracefully skips when textstat not installed
- Line numbers track paragraph start location
- All metrics can be individually enabled/disabled
- Full Unicode support

## Development

Run tests (includes 30 readability-specific tests):

```bash
uv sync --extra dev
uv run pytest tests/test_readability.py -v
```

Note: Tests are automatically skipped if textstat is not installed.

## References

- [textstat library](https://pypi.org/project/textstat/)
- [Flesch Reading Ease](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)
- [Gunning FOG](https://en.wikipedia.org/wiki/Gunning_fog_index)
