---
author: Engineering Team
created: 2026-09-18
doc_uuid: d7c37fbf-d593-4476-a6bd-33bb17557837
id: memo-003
project_id: docuchango
tags: [automation, maintenance, releases]
title: Release Note Generation
---

# Memo-003: Release Note Generation

## Review of v1.19.0

The published stable notes concatenated the semantic-release changelog from
v1.18.1 through v1.19.0, then appended GitHub's generated PR list. The result
contained 19 RC headings, including empty sections, repeated category
headings, intermediate review commits, and a second account of the same work.
Maintenance appeared before features. Some squash-merged features appeared
only in the PR list, including atomic fixes, numbering-gap reports, and
cross-plugin link repair.

The stable range contains 36 merged PRs and two direct non-release commits
on the first-parent path. Those records are captured in
`tests/fixtures/releases/v1.19.0.json` so future generator changes can be
checked against the data that exposed the problem.

## Generation policy

The release workflow uses `scripts/release_notes.py` to render first-parent
Git history. A stable release compares the previous stable tag to the new
tag, including every RC in between. An RC compares the previous release tag
to its new tag. Stable bases must match a plain `vX.Y.Z` tag, excluding all
prerelease suffixes. The first release reads history up to its tag.

Each landed PR appears once, using its squash subject or the title in its
GitHub merge message, with a PR link. Direct commits keep commit links.
Version-bump commits are omitted. Conventional types select the section;
breaking changes and security precede features and fixes. Documentation,
dependencies, build/CI, tests, and maintenance are collapsible. Unclassified
changes remain visible. The generator does not rely on GitHub's generated
notes API, labels, or the changelog's inclusion of individual commits.

The workflow writes the same Markdown to the release and its job summary.
Missing tags or a non-ancestor base fail generation instead of publishing
misleading fallback text. The detailed semantic-release changelog remains
unchanged. See [Publishing](../../PUBLISHING.md) for preview commands.

## Editorial limits

Git summaries cannot infer user impact reliably. Use behavior-focused PR
titles and preserve breaking-change markers in landed commit messages.
First-parent history deliberately summarizes a merged branch using its merge
message; it does not publish every review commit or inspect branch bodies
for migration advice. Review stable releases for upgrade guidance.

The [rewritten v1.19.0 notes](../../docs/release-notes/v1.19.0.md) put atomic
fixing, empty-scan failures, metadata checks, and path containment first.
They distinguish automatic repairs from findings that require manual work
and clarify that the NLTK override affects repository resolution rather than
published package metadata.

## Verification

Regression tests cover all 36 PR links and both direct commits from the
reviewed release, grouping and deduplication, breaking changes, stable and
incremental RC ranges, initial releases, and missing or reversed tag ranges.
Temporary Git repositories exercise the generator's CLI and merge-history
handling without API credentials or network access.
