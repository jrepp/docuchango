---
author: Engineering Team
created: '2026-05-30'
doc_uuid: 07a83898-94f0-4c55-a190-f900c6d7250f
id: memo-001
project_id: docuchango
tags:
- frontmatter
- normalization
- validation
title: Frontmatter Auto-Fix Priorities
---

# Memo-001: Frontmatter Auto-Fix Priorities

## Summary

Docuchango should prioritize frontmatter fixes that are deterministic, reversible, and low risk. The highest-value work is normalizing tags, adding safe missing fields, trimming whitespace, and ordering fields consistently.

## High-Confidence Fixes

Implement these first because they have clear rules and low semantic risk:

- Normalize tags from strings or mixed arrays into lowercase, dash-separated arrays.
- Remove duplicate tags and sort them alphabetically.
- Generate `doc_uuid` when missing.
- Set missing `project_id` from project configuration.
- Add an empty `tags` array when tags are absent.
- Trim leading and trailing whitespace from frontmatter string values.
- Reorder frontmatter fields to match template order for cleaner diffs.

## Medium-Confidence Fixes

These are useful but should emit explicit warnings because they can affect downstream queries or review diffs:

- Convert boolean strings such as `"true"` and `"false"` to booleans.
- Remove optional fields with empty strings or null values.
- Convert numeric strings to numbers while preserving semantic versions.
- Normalize `author` and `deciders` formats where schemas permit arrays.
- Detect duplicate YAML keys and retain the value that YAML parsing would keep.
- Normalize related-document references into lowercase arrays after checking that referenced documents exist.

## Detection-Only Cases

These require human review and should not be automatically rewritten:

- Title and ID mismatches where the content appears to describe a different document.
- Status values that may be outdated based on project history.
- Missing descriptions or summaries that require judgment about quality.
- Inconsistent terminology that should be resolved through a glossary or taxonomy.
- Invalid YAML, encoding issues, and merge-conflict markers.

## Implementation Order

Phase 1 should focus on safe fixes: invalid status values, invalid date formats, missing frontmatter blocks, tag normalization, missing required fields, whitespace trimming, and field ordering.

Phase 2 should add medium-confidence conversions: boolean strings, empty value normalization, numeric strings, and author or decider normalization.

Phase 3 should add duplicate-field detection, related-reference checks, and status-consistency suggestions.
