# Validation reference

Everything `docuchango validate` checks, grouped by area. Each area lists
what is detected, what is repaired automatically when you run without
`--dry-run`, and what is reported for a person to fix.

Checks that are planned but not yet built, and the finding ID assigned to
every check, are tracked in the
[validator roadmap](../docs-cms/rfcs/rfc-003-validator-roadmap.md).

## Frontmatter

**Detected**

- Missing YAML frontmatter block
- Missing required fields for the selected schema: ADR, RFC, Memo and PRD require `title`, `created`, `id`, `project_id`, `doc_uuid` and their per-type fields; generic documents require only `title`, `project_id` and `doc_uuid`.
- Wrong field types or formats
- Status values not valid for the document type
- Malformed UUIDs
- `id` that does not match the filename
- `id` that does not match the number in the title
- Duplicate `id` or `doc_uuid` across documents
- Binary or non-UTF-8 files in a document folder

**Fixed automatically**

- Generates a frontmatter block with sensible defaults when one is missing
- Adds a missing `tags`, `project_id` or `doc_uuid` to an existing block
- Maps common status variants and misspellings to the valid value for the type
- Converts dates in slash, dot and long-month formats (`2026/09/14`,
  `14.09.2026`, `September 14, 2026`) to ISO 8601
- Normalizes tags to a sorted, de-duplicated, lowercase-with-dashes list
- Trims whitespace and removes empty or null values
- Adds `created` from git history and migrates a legacy `date` field

**Left to you**

- Type or format errors that have no safe automatic value
- Missing `title` or `id` in an existing frontmatter block
- Per-type fields such as `deciders` or `author`
- Malformed UUIDs
- `id` and filename or title mismatches
- Duplicate ids or UUIDs
- Dates in a format the fixer does not recognize: `created` accepts any
  string, so an unrecognized date is neither rewritten nor reported

## Code blocks

**Detected**

- Opening fence with no language
- Closing fence with text after it
- Unclosed code block
- Missing blank line before or after a fence

**Fixed automatically**

- Adds `text` to bare opening fences
- Strips text from closing fences
- Adds missing closing fences
- Inserts the missing blank lines

## Links

**Detected**

- Internal links to files that do not exist
- Relative paths (`./x`, `../x`) that do not resolve
- Cross-references to ADRs or RFCs that do not exist
- Links that climb several `../` levels across plugin boundaries

**Left to you**

Link findings are reported, never rewritten: `docuchango validate` checks
links but does not touch them, because the right target is a judgement call.
Fix them by hand, or with your own tooling, and validate again.

## MDX compatibility

**Detected**

- Unescaped `<` or `>` before a number, which MDX reads as JSX
- Other characters that break MDX parsing
- MDX or JSX compilation errors

**Left to you**

MDX findings are reported only. Escape `<` and `>` as `&lt;` and `&gt;`, or
wrap the text in backticks, then validate again.

## Formatting

**Detected**

- Trailing whitespace
- More than two consecutive blank lines

**Fixed automatically**

- Removes trailing whitespace outside code blocks

**Left to you**

- Runs of more than two blank lines, which are reported but not collapsed

## Filenames

**Detected**

- Names that do not match `type-NNN-slug.md` or the configured pattern,
  unless `enforce_filename_pattern: false` is set for that folder

There is no gap or sequence check: a jump from `adr-004` to `adr-009` is not
reported. Filename problems are always left to you, because renaming can break
links elsewhere. `docuchango bulk compress-ids` can renumber documents and
update references in one step.

## Index files

When `indexes` are configured, an index file is checked for:

- Every target linked when `require_all_targets` is set
- At least one entry when `require_entries` is set
- No links outside the target set unless `allow_extra_links` is set
- Each target listed under the correct time-bucket or milestone heading

Index findings are reported, not fixed.

## Readability

When `textstat` is installed and `readability.enabled` is true, paragraphs
longer than the configured minimum are scored. Paragraphs outside the
thresholds are reported with the metric that failed. Nothing is rewritten.

## Docusaurus build

Unless you pass `--skip-build`, docuchango also runs the project's Docusaurus
build when one is present and reports TypeScript, MDX and build errors. These
are reported for manual resolution. Use `--skip-build` in quick local runs
and in CI jobs that do not have Node installed.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Every document valid, or every issue fixed |
| 1 | Issues remain that need a person |
| 2 | The run itself failed: the validator could not be imported or raised, or the command line was wrong (a bad `--repo-root`, an unknown option) |

Treat 2 as "docuchango could not tell you anything", not as a documentation
problem. With `--dry-run` the exit code reflects the issues found, so a CI
job fails on problems without rewriting files.
