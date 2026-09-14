# Validation reference

Everything `docuchango validate` checks, grouped by area. Each area lists
what is detected, what is repaired automatically when you run without
`--dry-run`, and what is reported for a person to fix.

## Frontmatter

**Detected**

- Missing YAML frontmatter block
- Missing required fields (`id`, `title`, `created`, `tags`, `project_id`, `doc_uuid`, plus per-type fields such as `status`, `deciders`, `author`, `target_release`)
- Wrong field types or formats
- Status values not valid for the document type
- Dates that are not ISO 8601 (`YYYY-MM-DD`)
- Malformed UUIDs
- `id` that does not match the filename
- `id` that does not match the number in the title
- Duplicate `id` or `doc_uuid` across documents
- Binary or non-UTF-8 files in a document folder

**Fixed automatically**

- Generates a frontmatter block with sensible defaults when one is missing
- Adds missing required fields
- Maps common status variants and misspellings to the valid value for the type
- Converts dates in slash, dot and long-month formats to ISO 8601
- Normalizes tags to a sorted, de-duplicated, lowercase-with-dashes list
- Trims whitespace and removes empty or null values
- Adds `created` from git history and migrates a legacy `date` field

**Left to you**

- Type or format errors that have no safe automatic value
- Per-type fields such as `deciders` or `author`
- Malformed UUIDs
- `id` and filename or title mismatches
- Duplicate ids or UUIDs

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

**Fixed automatically**

- Rewrites broken internal links when the target can be found elsewhere
- Converts cross-plugin links to absolute GitHub URLs
- Normalizes link formats

## MDX compatibility

**Detected**

- Unescaped `<` or `>` before a number, which MDX reads as JSX
- Other characters that break MDX parsing
- MDX or JSX compilation errors

**Fixed automatically**

- Escapes `<` and `>` as `&lt;` and `&gt;`
- Corrects common JSX-incompatible Markdown

## Formatting

**Detected**

- Trailing whitespace
- More than two consecutive blank lines
- Inconsistent line endings

**Fixed automatically**

- Removes trailing whitespace
- Collapses runs of blank lines

## Filenames

**Detected**

- Names that do not match `type-NNN-slug.md` or the configured pattern
- Uppercase characters in filenames
- Gaps or inconsistency in ADR, RFC and memo numbering

Filename problems are always left to you, because renaming a file can break
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

With `--dry-run` the exit code reflects the issues found, so a CI job fails
on problems without rewriting files.
