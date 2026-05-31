---
author: Engineering Team
created: 2026-05-30
doc_uuid: 427be5ee-a803-48f7-8cf8-e4326edf4f63
id: rfc-002
project_id: docuchango
status: Implemented
tags: [documentation, readability, validation]
title: Readability Validation
---

# RFC-002: Readability Validation

## Summary

Docuchango supports optional readability validation for documentation prose. When enabled and the optional `textstat` dependency is installed, validation reports paragraphs that fall below configured readability thresholds.

## Motivation

Documentation quality is not only structural. Long, dense prose can pass schema and link checks while still being difficult for readers to use. Readability checks provide automated feedback without blocking projects that do not want this feature.

## Configuration

Enable readability in `docs-project.yaml`:

```yaml
readability:
  enabled: true
  flesch_reading_ease_min: 60.0
  flesch_kincaid_grade_max: 10.0
  gunning_fog_max: 12.0
  smog_index_max: 12.0
  automated_readability_index_max: 10.0
  coleman_liau_index_max: 10.0
  dale_chall_max: 9.0
  min_paragraph_length: 100
```

Install optional support with:

```bash
pip install docuchango[readability]
```

or during development:

```bash
uv sync --extra readability
```

If `textstat` is not installed, readability checks are skipped without failing validation.

## Metrics

Supported metrics include Flesch Reading Ease, Flesch-Kincaid Grade Level, Gunning Fog Index, SMOG Index, Automated Readability Index, Coleman-Liau Index, and Dale-Chall Score. Each metric can be enabled or disabled independently by setting the threshold to a number or `null`.

## Scope

Readability analysis includes regular paragraph text and multi-line paragraphs.

Readability analysis excludes frontmatter, headings, lists, blockquotes, code blocks, HTML or MDX tags, and paragraphs shorter than `min_paragraph_length`.

## Reporting

Validation should report the document path, line number, metric, observed score, and configured threshold so authors can revise the exact paragraph that needs attention.

## Authoring Guidance

Readable docs should use shorter sentences, simpler words, active voice, concrete examples, and focused paragraphs. Technical docs can tolerate more complexity than consumer help docs, so projects should tune thresholds by audience.

## Verification

Run readability-specific tests with:

```bash
uv run pytest tests/test_readability.py -v
```