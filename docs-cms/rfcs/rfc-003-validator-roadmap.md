---
author: Jacob Repp
created: 2026-09-14
doc_uuid: f7651c24-83ba-429e-9511-33e0ea9ca6bf
id: rfc-003
project_id: docuchango
status: Proposed
tags: [findings, roadmap, validation]
title: Validator Roadmap and Finding Registry
---

# RFC-003: Validator Roadmap and Finding Registry

## Summary

Give every check that `docuchango validate` performs, or is planned to
perform, a stable finding ID, and keep the full list in one registry in this
document. The registry is the source of truth for what is implemented, what
is planned, and whether a finding is repaired automatically or only
reported. Agents and people implementing a validator update its row here,
use the ID in error messages and tests, and mirror the change in
`docs/VALIDATION_REFERENCE.md`.

## Motivation

The review of the onboarding refresh (PR #74) found a dozen places where the
documentation described checks the validator does not perform: a
`project_id` match against the config, date format enforcement, line-ending
checks, numbering-gap detection, and automatic link and MDX rewriting during
`validate`. Each of these is reasonable to build, and several already have a
fixer module in `docuchango/fixes/` that `validate` never calls. Without a
registry there is no place to say "this is planned, not built", so the docs
drift toward promising them.

A finding ID also gives users something greppable and stable to cite in
issues, CI logs and suppression config, independent of the wording of the
message.

## Detailed Design

### Finding ID format

`<AREA>-<NNN>`. The area prefix matches the sections of
`docs/VALIDATION_REFERENCE.md`. Numbers `001` to `009` are reserved for
checks that exist today; planned checks start at `010` so the registry can
be read at a glance. IDs are never reused or renumbered once a check ships.

| Prefix | Area |
|--------|------|
| `FM` | Frontmatter and schema |
| `ID` | Identifiers and filenames |
| `LNK` | Links |
| `MDX` | MDX compatibility |
| `FMT` | Markdown formatting |
| `CB` | Code blocks |
| `IDX` | Document indexes |
| `RD` | Readability |
| `BLD` | Docusaurus build |

### Registry

Status is one of `Implemented`, `Planned` or `Rejected`. Mode is `fix` when
`validate` repairs the finding without `--dry-run`, `report` when it is only
reported, and `fix/report` when some cases are repaired and the rest
reported.

| ID | Check | Status | Mode | Where |
|----|-------|--------|------|-------|
| FM-001 | Missing YAML frontmatter block | Implemented | report | `DocValidator.scan_documents` |
| FM-002 | Frontmatter fails the per-type Pydantic schema (required fields, types, status values) | Implemented | fix/report | `scan_documents`, `schemas.py` (`Literal` types and `VALID_*_STATUSES`), `fixes/frontmatter.py` (`VALID_STATUSES` and `STATUS_MAPPINGS`) |
| FM-003 | Malformed `doc_uuid` | Implemented | report | `schemas.py` validators |
| FM-004 | Duplicate `doc_uuid` across documents | Implemented | report | `check_uuids` |
| FM-005 | Missing `tags`, `project_id` or `doc_uuid` filled in | Implemented | fix | `fixes/whitespace.py` `ensure_required_fields` |
| FM-006 | Recognized non-ISO date formats normalized | Implemented | fix | `fixes/frontmatter.py` |
| FM-010 | `project_id` does not match `project.id` of the governing config | Planned | fix/report | see below |
| FM-011 | `created` or `updated` is not an ISO 8601 date or datetime | Planned | report | see below |
| ID-001 | Top-level filename does not match the configured pattern (files in subfolders are support material and are not scanned, unless `structure.scan_subfolders` or a per-type override enables ID-011) | Implemented | report | `check_ids`, `_scan_document_folder` |
| ID-002 | `id` does not match the filename; an ADR amendment `adr-NNN-amendment-MM-*` is expected to carry id `adr-NNN-aMM` | Implemented | report | `check_ids`, `_scan_document_folder` |
| ID-003 | `id` does not match the number in the title | Implemented | report | `check_ids` |
| ID-004 | Duplicate `id` across documents | Implemented | report | `check_ids` |
| ID-010 | Gap or non-contiguous numbering within a document type | Planned | report | see below |
| ID-011 | Validate numbered documents nested in subfolders of a document folder, opt-in via `structure.scan_subfolders` (and per-type via `structure.doc_types.<type>.scan_subfolders`) | Implemented | report | `scan_documents`, `_build_scan_entries`, `_scan_document_folder`, `schemas.py` (`DocsProjectStructure.scan_subfolders`, `DocTypeConfig.scan_subfolders`) |
| LNK-001 | Broken internal link, including bare relative, suffix-less and directory targets | Implemented | report | `validate_links`, `_resolve_link_target` |
| LNK-002 | Link that resolves outside the repository root, reported once per link with line number and target | Implemented | report | `check_cross_plugin_links` |
| LNK-010 | Rewrite a broken internal link when the target exists elsewhere | Planned | fix | see below |
| LNK-011 | Rewrite cross-plugin links to absolute repository URLs | Planned | fix | see below |
| MDX-001 | `<` that opens a JSX-shaped tag which is not a valid HTML element, PascalCase component, self-closing tag or CommonMark autolink (bare prose placeholders such as `<token>`). Comparisons such as `<5ms` or `a < b` are not findings | Implemented | report | `check_mdx_compatibility`, `_is_safe_mdx_tag`, `_mask_code` |
| MDX-002 | MDX compilation error | Implemented | report | `check_mdx_compilation` |
| MDX-010 | Escape `<` and `>` and repair common JSX-incompatible Markdown | Planned | fix | see below |
| MDX-011 | Mask 4-space indented code blocks before the prose checks (only fenced blocks and inline spans are masked today) | Planned | report | see below |
| FMT-001 | Trailing whitespace | Implemented | fix | `check_formatting`, `fixes/code_blocks.py` |
| FMT-002 | More than two consecutive blank lines | Implemented | report | `check_formatting` |
| FMT-010 | CRLF or mixed line endings | Planned | fix | see below |
| FMT-011 | Collapse runs of blank lines | Planned | fix | see below |
| CB-001 | Code fence without a language, or unclosed fence | Implemented | fix/report | `check_code_blocks`, `fixes/code_blocks.py` |
| IDX-001 | Document index missing, unlinked, or missing bucket headings | Implemented | report | `check_document_indexes` |
| RD-001 | Paragraph outside the configured readability thresholds | Implemented | report | `check_readability` |
| BLD-001 | TypeScript config error | Implemented | report | `check_typescript_config` |
| BLD-002 | Docusaurus build error | Implemented | report | `check_docusaurus_build` |

**ID-011 Nested documents (shipped).** Documents inside subfolders of a
document folder (`adr/archive/`, `rfcs/2024/`) were treated as support
material and not scanned at all, so a duplicate `doc_uuid`, a mismatched `id`
or a broken link in one of them was never reported. `structure.scan_subfolders`
(default `false`, preserving the old behavior) now opts a whole layout into
scanning nested files with the same id/uuid/link/filename rules as top-level
files, matched against the file name and not the subfolder path.
`structure.doc_types.<type>.scan_subfolders` overrides the structure default
for one document type. Report only.

### Planned validators

Each entry lists what it detects, what it may fix, and the constraint that
keeps it safe.

**FM-010 `project_id` match.** Compare each document's `project_id` with the
`project.id` of the config that governs its folder, honouring sub-project
configs so a monorepo is not flattened to one ID. Report the mismatch. Fix
only when the folder is governed by exactly one config and the current value
is empty or the `init` placeholder `my-project`; a different, non-placeholder
value may be intentional and stays a report. This is the check the old docs
promised and the one most likely to catch a copy-pasted template.

**FM-011 Date format.** Accept `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`, the
two forms the templates use. Anything else that FM-006 did not recognize is
reported with the value seen. No new fixing: FM-006 already rewrites the
formats it can identify with confidence.

**ID-010 Numbering gaps.** For each type, sort the numeric parts of the IDs
and report the missing numbers between the lowest and highest. Report only,
and mention `docuchango bulk compress-ids` in the message. Gaps are common
and often deliberate after a deleted proposal, so this should be opt-in via
`structure.doc_types.<type>.report_numbering_gaps: true` and default to off.

**MDX-011 Indented code blocks.** `_mask_code` masks fenced blocks and
inline spans before the prose checks run, but not 4-space indented code
blocks, so a `<token>` placeholder inside one is reported. Correct handling
needs list-continuation context, because a 4-space indent inside a list
item is a paragraph, not code.

**LNK-010 Internal link rewrite.** Wire `fixes/internal_links.py` into the
Phase 1 fix loop of `validate`. When a link is broken and exactly one
document in the scanned set has the same filename, rewrite the link to the
correct relative path. Two or more candidates stay a report (LNK-001) with
the candidates listed. The module's `main()` currently resolves `docs-cms`
relative to the installed package, so the entry point takes the validator's
scanned paths instead.

**LNK-011 Cross-plugin link rewrite.** Wire `fixes/cross_plugin_links.py`
into Phase 1. Needs a repository base URL, so add `project.repository_url`
to `docs-project.yaml`; when it is absent the check stays a report (LNK-002).

**MDX-010 MDX escapes.** Wire `fixes/mdx_syntax.py` into Phase 1 for the
patterns `check_mdx_compatibility` already detects. Content inside code
fences and inline code is never touched.

**FMT-010 Line endings.** Detect `\r\n` anywhere in a document and rewrite
the file to `\n`. Fix by default: the rewrite is lossless and every other
fixer already assumes `\n`.

**FMT-011 Blank-line collapse.** Reduce runs of three or more blank lines to
two, outside code fences. This turns the existing FMT-002 report into a fix.

### Error message format

New checks prefix their message with the finding ID:

```text
FMT-010: Line 12: CRLF line ending
```

Existing checks adopt the prefix when their message is next touched, so
no single change rewrites every test fixture at once. Once every check
carries an ID, `docs-project.yaml` can grow a `validation.ignore` list of
IDs, which is the intended suppression mechanism and is out of scope here.

### Adding a validator

1. Pick the next free number in the area and add the row here as `Planned`
   if it is not already listed.
2. Detection goes in a `check_*` method on `DocValidator`; repair goes in a
   module under `docuchango/fixes/` that returns what it changed.
3. Wire the fixer into Phase 1 of `validate` in `cli.py` and the check into
   Phase 2, in the order the table above lists them.
4. Prefix messages with the ID. Add tests under `tests/` named for the ID.
5. Update `docs/VALIDATION_REFERENCE.md` and flip the row to `Implemented`
   in the same change.

### Regression fixtures

Step 4 has a fixed shape. `tests/fixtures/findings/<FINDING-ID>-<slug>/` holds
a miniature repository that reproduces one finding, plus an `expected.yaml`
recording the messages `validate` should print, whether the finding is
repaired, and the exit codes with and without `--dry-run`.
`tests/test_findings.py` discovers every such directory and runs the real
Click command against a copy under `tmp_path`.

Write the fixture before the check. While the row here says `Planned`, the
harness collects the detection test as a strict `xfail`, so the suite stays
green; the moment the check starts reporting the finding, the `xfail` turns
into a failure, which is the reminder to flip the row to `Implemented`. In the
other direction, `test_every_implemented_id_has_a_fixture` fails when an
`Implemented` row has no fixture, unless its ID is listed in the annotated
`KNOWN_GAPS` set for checks a Markdown-only fixture cannot reach, such as the
Docusaurus build ones.

`tests/fixtures/findings/README.md` has the `expected.yaml` reference and the
commands for adding a case.

## Drawbacks

A registry is one more thing to keep in sync, and an unmaintained one is
worse than none because it looks authoritative. The mitigation is the
per-row `Where` column: a test can assert that every `Implemented` row names
a symbol that exists, and every `Planned` row does not.

Prefixing messages changes output that users may already grep for in CI.
The staggered adoption limits this to one check at a time.

## Alternatives

**Track planned checks as GitHub issues only.** Issues are not visible to an
agent reading `docs-cms/`, and they do not give a stable ID that survives
into the error message.

**Numeric IDs without an area prefix.** Shorter, but the prefix is what lets
a reader jump from a CI log line to the right section of the validation
reference.

## Adoption Strategy

No user action is required. `docs/VALIDATION_REFERENCE.md` links here for
the list of planned checks, and `AGENTS.md` tells agents working on this
repository to update the registry when a validator lands.

## Unresolved Questions

- Whether FM-010 should also fix a non-placeholder mismatch when the user
  passes an explicit flag such as `--set-project-id`.
- Whether ID-010 belongs in `validate` at all, or only as a `bulk` report.

## Future Possibilities

- A `validation.ignore` list of finding IDs in `docs-project.yaml`.
- A `--format json` output for `validate` keyed by finding ID for CI
  annotations.