# Validation reference

Everything `docuchango validate` checks, grouped by area. Each area lists
what is detected, what is repaired automatically when you run without
`--dry-run`, and what is reported for a person to fix.

A fixing run is atomic by default. If any issue remains once fixing
finishes, every fix from that run is withheld and the tree is left exactly
as it was before the run started. The report still lists what would have
changed, so "repaired automatically" below means what the run would write if
nothing else were wrong, not a guarantee that this run wrote it. Pass
`--no-atomic` to keep partial fixes on disk even when other issues remain.

Checks that are planned but not yet built, and the finding ID assigned to
every check, are tracked in the
[validator roadmap](../docs-cms/rfcs/rfc-003-validator-roadmap.md).

## Scan coverage

**Detected**

- `SCAN-001`: the run found no documents at all, so nothing was validated

A scan that turns up zero documents is reported as an issue and exits 1. It
is almost always a wrong `--repo-root`, a checkout that does not contain the
documentation tree, or a repository that never ran `docuchango init` - not a
clean bill of health. The message names the likeliest cause: no
`docs-project.yaml` was found at the repository root, in `docs-cms/` or in
`docs/`; the one that was found could not be loaded; or the document folders
it configures contain no Markdown files.

Neither `--dry-run` nor `--skip-build` suppresses the check.

**Left to you**

- Point `--repo-root` at the repository that holds the documentation, create
  the tree with `docuchango init`, or pass `--allow-empty` when a repository
  legitimately has no documents yet. An allowed empty scan exits 0 and says
  `No documents found; empty scan allowed by --allow-empty` rather than
  claiming a clean validation.

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

The `id`/`doc_uuid` mismatch and duplicate checks above apply only to the
standard `adr`, `rfc`, `memo` and `prd` schemas; a `generic` document is not
checked for either.

**Fixed automatically**

- Generates a frontmatter block with sensible defaults when one is missing
- Adds a missing `tags`, `project_id` or `doc_uuid` to an existing block
- Maps common status variants and misspellings to the valid value for the type
- Converts dates in slash, dot and long-month formats (`2026/09/14`,
  `14.09.2026`, `September 14, 2026`) to ISO 8601
- Normalizes tags to a sorted, de-duplicated, lowercase-with-dashes list
- Trims whitespace and removes empty or null values
- Adds `created` from git history, but only when a frontmatter block already
  exists and is missing that field; a document with no frontmatter at all
  gets today's date when its block is generated. Also migrates a legacy
  `date` field to `created`

Generating a missing frontmatter block and mapping status variants both infer
the document type from the standard `adr/`, `rfcs/`, `memos/` and `prd/`
folder names. A custom `doc_types` folder with a different name is not
recognized: a missing block is reported instead of generated, and an invalid
status is reported instead of mapped.

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

None of these fixes run in `--dry-run`: the fixer that applies them is
skipped entirely for a dry run, so each one is reported as a plain "Detected"
issue above instead of a previewed fix, then silently fixed on the real run.

## Links

**Detected**

- Internal links to files that do not exist
- Relative paths (`./x`, `../x`) that do not resolve
- Bare relative paths (`adr/adr-012-trust.md`, `other-doc`) that do not
  resolve against the linking document's folder; a suffix-less target is
  also tried with `.md`, and a link to an existing folder (`../adr/`) is
  valid as written
- Cross-references to ADRs or RFCs that do not exist
- Links that resolve outside the repository root, reported one per link with
  its line number and target. A link that points elsewhere *inside* the
  repository, such as `../../internal/notes.md` or the repository `README.md`,
  is legitimate and is not reported

**Left to you**

Link findings are reported, never rewritten: `docuchango validate` checks
links but does not touch them, because the right target is a judgement call.
Fix them by hand, or with your own tooling, and validate again.

## MDX compatibility

**Detected**

- A `<` that starts something MDX reads as a JSX tag but that is not a valid
  element: a bare placeholder in prose such as `<token>`, `<agentName>` or
  `<time-out>`
- MDX or JSX compilation errors

A `<` or `>` is only a tag when a letter follows immediately, so comparisons
(`<5ms`, `>90%`, `a < b`, `< threshold`) are not reported. Known HTML
elements (`<br/>`, `<sup>`, `<div class="x">`), PascalCase JSX components
(`<Outlet />`), self-closing tags and CommonMark autolinks
(`<https://example.com>`, `<team@example.com>`) are all valid and are not
reported either. Code fences, inline code spans and the frontmatter block are
excluded from the check.

**Left to you**

MDX findings are reported only. Escape `<` and `>` as `&lt;` and `&gt;`, or
wrap the text in backticks, then validate again.

## Formatting

**Detected**

- Trailing whitespace
- More than two consecutive blank lines

**Fixed automatically**

- Removes trailing whitespace outside code blocks, on a real run - like code
  fence fixes (above), this is not previewed in `--dry-run`: a trailing-space
  line shows up as a plain issue there, then disappears silently on the real
  run

**Left to you**

- Runs of more than two blank lines, which are reported but not collapsed
  (collapsing them is planned - see the
  [validator roadmap](../docs-cms/rfcs/rfc-003-validator-roadmap.md), FMT-011)

## Filenames

**Detected**

- Names that do not match `type-NNN-slug.md` or the configured pattern,
  unless `enforce_filename_pattern: false` is set for that folder

By default, only files directly inside a document folder are treated as
documents. A file in a subfolder (`prd/testing/notes.md`,
`memos/private/draft.md`) is support material: it is skipped, not validated
and not renamed. Set `structure.scan_subfolders: true` (or the per-type
`structure.doc_types.<type>.scan_subfolders` override) to scan nested files
with the same rules as top-level ones; the filename pattern and expected id
are still matched against the file name, not the subfolder path. See
[Configuring docuchango](CONFIGURATION.md#scanning-nested-subfolders). An ADR
amendment (`adr-043-amendment-01-cap.md`) is expected to carry the amendment
id `adr-043-a1`, in a subfolder or not.

There is no gap or sequence check: a jump from `adr-004` to `adr-009` is not
reported. Filename problems are always left to you, because renaming can break
links elsewhere. `docuchango bulk compress-ids` can renumber documents and
update references in one step.

## Index files

When `indexes` are configured, an index file is checked for:

- Every target linked when `require_all_targets` is set
- At least one entry when `require_entries` is set and its `targets` glob
  matches at least one file - an index whose targets glob matches nothing is
  allowed to be empty even with `require_entries: true`
- No links outside the target set unless `allow_extra_links` is set
- Each target listed under the correct time-bucket or milestone heading

Index findings are reported, not fixed.

## Readability

When `textstat` is installed and `readability.enabled` is true, paragraphs at
least as long as the configured minimum are scored. Paragraphs outside the
thresholds are reported with the metric that failed. Nothing is rewritten.

Settings are resolved per document from the config that owns it, so in a
monorepo with `subprojects` a sub-project can enable, disable or tune
readability on its own. A config that does not declare a `readability` block
inherits the nearest one up the `subprojects` chain, ending at the root
config. A declared block is used whole and is never merged key by key with its
parent's.

## Docusaurus build

Unless you pass `--skip-build`, docuchango also runs the project's Docusaurus
build when one is present and reports TypeScript, MDX and build errors. These
are reported for manual resolution. Use `--skip-build` in quick local runs
and in CI jobs that do not have Node installed.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Every document valid, or every issue fixed |
| 1 | Issues remain after the fixes for this run were applied (or, in `--dry-run`, simulated); under the default atomic run, the fixes this run would have made were withheld and the tree is untouched |
| 1 | Nothing was scanned at all (`SCAN-001`), unless `--allow-empty` is passed |
| 2 | The run itself failed: the validator could not be imported or raised, or the command line was wrong (a bad `--repo-root`, an unknown option) |

Treat 2 as "docuchango could not tell you anything", not as a documentation
problem. Exit code 1 does not always mean a person has to act: in
`--dry-run`, nothing is written, so a fixable problem whose fixer only runs
outside `--dry-run` (any code fence or trailing-whitespace fix, or a status
value that maps to a valid one) still counts as a remaining issue and exits
1, even though the plain `validate` form would clear it automatically. A
value the schema itself accepts without complaint, such as an unusual but
parseable `created` string, is proposed as a normalization without causing a
failing exit code either way. `--dry-run` never writes to the working tree,
so use it in CI to fail the build on whatever would still be wrong afterwards
- not as a guarantee that every fixable issue also fails the build.

Exit code 1 from a plain `validate` run also means nothing was written, as
long as the run stayed atomic (the default). If any issue remains after
fixing, `validate` restores every file its fixers touched during that run
before it reports, so a failing run cannot leave a half-fixed document in
your working tree. Run again once the reported issues are resolved and the
withheld fixes land with them, or pass `--no-atomic` to keep the partial
fixes on disk right away.
