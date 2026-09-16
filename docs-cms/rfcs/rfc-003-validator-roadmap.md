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
| `SCAN` | Scan coverage |
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
| SCAN-001 | The run scanned no documents at all, so nothing was validated (wrong `--repo-root`, missing `docs-project.yaml`, uninitialized `docs-cms/`). `--allow-empty` accepts the empty scan and exits 0 | Implemented | report | `cli.validate`, `_empty_scan_message` |
| FM-001 | Missing YAML frontmatter block | Implemented | fix/report | `DocValidator.scan_documents`, `fixes/frontmatter.py` (`add_missing_frontmatter`, `resolve_doc_type`) |
| FM-002 | Frontmatter fails the per-type Pydantic schema (required fields, types, status values) | Implemented | fix/report | `scan_documents`, `schemas.py` (`Literal` types and `VALID_*_STATUSES`), `fixes/frontmatter.py` (`VALID_STATUSES`, `STATUS_MAPPINGS` and `resolve_doc_type`) |
| FM-003 | Malformed `doc_uuid` | Implemented | report | `schemas.py` validators |
| FM-004 | Duplicate `doc_uuid` across documents | Implemented | report | `check_uuids` |
| FM-005 | Missing `tags`, `project_id` or `doc_uuid` filled in | Implemented | fix | `fixes/whitespace.py` `ensure_required_fields` |
| FM-006 | Recognized non-ISO date formats normalized | Implemented | fix | `fixes/frontmatter.py` |
| FM-010 | `project_id` does not match the `project.id` of the config that governs the document's folder | Implemented | fix/report | `check_project_ids`, `_config_context_for_path`, `cli._discover_doc_claims`, `fixes/frontmatter.py` (`_fix_project_id_metadata`, `PROJECT_ID_PLACEHOLDER`) |
| FM-011 | `created` or `updated` is not `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` | Implemented | report | `check_date_formats`, `is_accepted_date_format`, `frontmatter_date_source`, `Document.date_source` |
| ID-001 | Top-level filename does not match the configured pattern (files in subfolders are support material and are not scanned, unless `structure.scan_subfolders` or a per-type override enables ID-011) | Implemented | report | `check_ids`, `_scan_document_folder` |
| ID-002 | `id` does not match the filename; an ADR amendment `adr-NNN-amendment-MM-*` is expected to carry id `adr-NNN-aMM` | Implemented | report | `check_ids`, `_scan_document_folder` |
| ID-003 | `id` does not match the number in the title | Implemented | report | `check_ids` |
| ID-004 | Duplicate `id` across documents | Implemented | report | `check_ids` |
| ID-010 | Gap or non-contiguous numbering within a document type, opt-in per type via `structure.doc_types.<type>.report_numbering_gaps` | Implemented | report | `check_numbering_gaps`, `_numbering_gap_types`, `_format_number_ranges`, `_config_context_for_path`, `schemas.py` (`DocTypeConfig.report_numbering_gaps`) |
| ID-011 | Validate numbered documents nested in subfolders of a document folder, opt-in via `structure.scan_subfolders` (and per-type via `structure.doc_types.<type>.scan_subfolders`) | Implemented | report | `scan_documents`, `_build_scan_entries`, `_scan_document_folder`, `schemas.py` (`DocsProjectStructure.scan_subfolders`, `DocTypeConfig.scan_subfolders`) |
| LNK-001 | Broken internal link, including bare relative, suffix-less and directory targets. LNK-010 repairs the single-candidate case in Phase 1, so what reaches the report is a target no scanned document carries, or an ambiguous one, whose candidates the message lists | Implemented | report | `validate_links`, `_validate_internal_link`, `_link_candidates`, `links.py` (`resolve_internal_link`, `link_candidates`) |
| LNK-002 | Link that resolves outside the repository root, reported once per link with line number and target. LNK-011 repairs it in Phase 1 when the target exists on disk and the governing config sets `project.repository_url`, so what reaches the report is a target that does not exist or a project with no repository URL | Implemented | report | `check_cross_plugin_links`, `links.py` (`resolve_repository_escape`) |
| LNK-010 | Rewrite a broken internal link when the target exists elsewhere | Implemented | fix | `cli.validate` (Phase 1), `fixes/internal_links.py` (`build_index`, `fix_internal_links`, `fix_links_in_tree`), `links.py`, `markdown.py` (`mask_code`) |
| LNK-011 | Rewrite cross-plugin links to absolute repository URLs | Implemented | fix | `cli.validate` (Phase 1), `cli._repository_urls_from_claims`, `fixes/cross_plugin_links.py` (`fix_cross_plugin_links`, `fix_cross_plugin_links_in_tree`), `links.py` (`resolve_repository_escape`, `repository_file_url`), `schemas.py` (`DocsProjectInfo.repository_url`), `validator._repository_url_for` |
| MDX-001 | `<` that opens a JSX-shaped tag which is not a valid HTML element, PascalCase component, self-closing tag or CommonMark autolink (bare prose placeholders such as `<token>`). Comparisons such as `<5ms` or `a < b` are not findings; MDX-010 is the repair | Implemented | report | `check_mdx_compatibility`, `markdown.py` (`mdx_tags`, `is_safe_mdx_tag`, `mask_code`, `mdx_finding_message`) |
| MDX-002 | MDX compilation error | Implemented | report | `check_mdx_compilation` |
| MDX-010 | Escape `<` and `>` and repair common JSX-incompatible Markdown | Implemented | fix | `markdown.py` (`escape_mdx_tags`, `mdx_tags`, `mdx_fix_message`), `fixes/mdx_syntax.py` (`fix_mdx_issues`, `fix_mdx_syntax`), `cli.validate` |
| MDX-011 | Mask 4-space indented code blocks before the prose checks (only fenced blocks and inline spans are masked today) | Planned | report | see below |
| FMT-001 | Trailing whitespace | Implemented | fix | `check_formatting`, `fixes/code_blocks.py` |
| FMT-002 | More than two consecutive blank lines, outside code fences and frontmatter; FMT-011 is the repair | Implemented | report | `check_formatting`, `markdown.py` (`blank_line_runs`, `blank_line_finding_message`) |
| FMT-010 | CRLF or mixed line endings | Implemented | fix | `check_formatting`, `text_io.py` (`find_carriage_returns`, `carriage_return_lines`, `write_text`), `fixes/frontmatter.py`, `fixes/whitespace.py` |
| FMT-011 | Collapse runs of blank lines | Implemented | fix | `markdown.py` (`collapse_blank_lines`, `fence_mask`, `frontmatter_span`), `fixes/frontmatter.py`, `fixes/whitespace.py` |
| FMT-012 | UTF-8 byte-order mark before the frontmatter | Implemented | fix | `check_formatting`, `text_io.py`, `fixes/frontmatter.py`, `fixes/whitespace.py` |
| CB-001 | Code fence without a language, or unclosed fence | Implemented | fix/report | `check_code_blocks`, `fixes/code_blocks.py` |
| IDX-001 | Document index missing, unlinked, or missing bucket headings | Implemented | report | `check_document_indexes` |
| RD-001 | Paragraph outside the readability thresholds of the (sub-)project that owns the document | Implemented | report | `check_readability`, `_readability_config_for`, `_config_context_for_path` |
| BLD-001 | TypeScript config error | Implemented | report | `check_typescript_config` |
| BLD-002 | Docusaurus build error | Implemented | report | `check_docusaurus_build` |

**SCAN-001 Empty scan (shipped).** `validate` exited 0 and printed
`All documents valid` whenever discovery turned up nothing, so a typo in
`--repo-root`, a checkout without the documentation tree, or a repository
that never ran `docuchango init` passed CI without validating a single
document (issue #87). A run that validated nothing now reports SCAN-001 and
exits 1, naming the likeliest cause: no `docs-project.yaml` was found, the
one found could not be loaded, or its document folders are empty. The check
looks at both the CLI's own discovery and `DocValidator.documents`, because
the validator also picks up plain Markdown at the configured `docs_roots`
that `_discover_doc_files` does not walk. `--allow-empty` restores the
exit-0 behaviour for a repository that legitimately has no documents yet,
and says so in the summary instead of claiming a clean validation. Neither
`--dry-run` nor `--skip-build` suppresses it. Report only: there is nothing
to repair.

**ID-011 Nested documents (shipped).** Documents inside subfolders of a
document folder (`adr/archive/`, `rfcs/2024/`) were treated as support
material and not scanned at all, so a duplicate `doc_uuid`, a mismatched `id`
or a broken link in one of them was never reported. `structure.scan_subfolders`
(default `false`, preserving the old behavior) now opts a whole layout into
scanning nested files with the same id/uuid/link/filename rules as top-level
files, matched against the file name and not the subfolder path.
`structure.doc_types.<type>.scan_subfolders` overrides the structure default
for one document type. Report only.

**FMT-012 UTF-8 byte-order mark (shipped).** `python-frontmatter` wants the
opening `---` at byte zero, so a BOM in front of it made a perfectly good
document look like it had no frontmatter at all: every Phase 1 fixer bailed
out with "No frontmatter found" and Phase 2 reported FM-001 for a document
that has frontmatter. Every document and config read now goes through
`docuchango/text_io.py`, which drops a leading BOM the way `utf-8-sig` does,
and every write stays plain UTF-8. `check_formatting` reports
`FMT-012: UTF-8 byte-order mark at start of file` from the bytes on disk,
which is what a `--dry-run` shows; a fixing run removes the mark in Phase 1
and reports `FMT-012: Removed UTF-8 byte-order mark`. The BOM is the only
thing removed: when no other fix applies, the original text is rewritten
verbatim rather than re-serialized.

**FMT-010 Line endings (shipped).** A CRLF document was invisible to every
check. `Path.read_text` and `open()` in text mode use universal newlines, so
`\r\n` is translated to `\n` before any check sees the string, and a document
that Windows or a copy-paste had converted passed `validate` silently while
every downstream fixer quietly assumed `\n`. `find_carriage_returns` in
`docuchango/text_io.py` reads the bytes on disk the way `has_bom` does and
returns the 1-based line number and kind of every non-LF terminator;
`check_formatting` reports one `FMT-010: Line N: CRLF line ending` per
offending line, matching how FMT-001 reports trailing whitespace rather than
summarizing a range. A bare `\r` is reported too, as `CR line ending`, and
normalized alongside `\r\n`: a half-converted file is not a state worth
preserving, and Python already treats a lone `\r` as a line terminator, so the
line numbers agree with the rest of the checks. The repair is a rewrite and
nothing more - the text read has already normalized the terminators, so any
write at all fixes the file. Phase 1 reports
`FMT-010: Converted CRLF line endings to LF` (or `CR and CRLF`, naming what it
found). The fix runs in `fix_frontmatter_metadata`, the first Phase 1 fixer, so
the rest of the run sees LF content. Writes in the fixers go through
`text_io.write_text`, which pins `newline=""`: `Path.write_text` translates
`\n` to `os.linesep` and would put the carriage returns straight back on
Windows. The atomic snapshot is taken as bytes before Phase 1, so a withheld
run restores a CRLF file byte for byte.

**FMT-011 Blank-line collapse (shipped).** FMT-002 has reported a run of more
than two blank lines since the first release and nothing ever collapsed one, so
the finding was pure noise on a document nobody was going to hand-edit. FMT-011
reduces any run of three or more blank lines to two, and FMT-002 stays the
report, which is what a `--dry-run` shows.

The two are now the same code. `docuchango/markdown.py` holds `fence_mask` and
`frontmatter_span` - the fence and frontmatter scanners that
`DocValidator._mask_code` used to keep to itself - and builds `blank_line_runs`
on top of them; `check_formatting` reports one
`FMT-002: Line N: More than 2 consecutive blank lines` per line past the second
of each run, and `collapse_blank_lines` rewrites exactly the runs that function
returns. Sharing the scan is not tidiness: under the default atomic run, a fix
the check still reports rolls the whole run back, so a fixer that disagreed with
its check by one line would withhold every fix in the tree.

A blank line inside a code fence is content - a deliberate gap in a shell
transcript, a blank line in a Python sample - and is neither reported nor
collapsed; backtick and tilde fences are both tracked, with the same
same-character/at-least-as-long closing rule the prose masking uses. Blank lines
inside the frontmatter block are skipped for the same reason: they may be part
of a YAML block scalar. The collapse runs in `fix_frontmatter_metadata` before
the document is parsed, so the line numbers in the messages are the ones FMT-002
reported for the file on disk, and both write paths - the re-serialized one and
the verbatim `rewrite_only` one that FMT-010 and FMT-012 added - carry the
repair. `fix_whitespace_and_fields` does the same. Phase 1 reports one
`FMT-011: Collapsed 5 blank lines to 2 at line 15` per run rather than a
per-file summary, matching how FMT-001 and FMT-002 name the line.

Trailing blank lines at end of file are collapsed like any other run, and are
not otherwise touched: `frontmatter.dumps` already strips the body's trailing
whitespace whenever any metadata fix re-serializes a document, and FMT-011 does
not fight that.

FMT-002 is also the first existing check to take the ID prefix its message was
promised in the "Error message format" section below: it had to be touched
anyway to stop counting blank lines inside fences, and the fixture messages
moved with it.

**RD-001 Sub-project readability (shipped).** `check_readability` read the
root config only, so a sub-project could not enable, disable or tune
readability even though its schema, folder and index rules were honored.
Settings are now resolved per document: `_config_context_for_path` maps a
file to the deepest config whose directory or `docs_roots` contain it, and
`_readability_config_for` returns that config's `readability` block, or the
nearest declared block up the `subprojects` chain when it has none. The block
is taken whole and never merged key by key, so a sub-project that declares
one gets schema defaults for the keys it omits. Documents that resolve to
different settings are scored by separate scorers in one pass. Report only.

**FM-010 `project_id` match (shipped).** Every schema requires `project_id`,
but nothing compared it to the project it names, so a document copied from
another repository or straight from a template kept pointing at the wrong
project and validated clean. `check_project_ids` now compares each document's
`project_id` with the `project.id` of the config that governs its folder,
resolved with the same `_config_context_for_path` that RD-001 uses, so a
monorepo is not flattened to one ID and a sub-project document is measured
against its own config. A mismatch is reported as
`FM-010: project_id 'x' does not match project.id 'y' in <config>`. A document
whose frontmatter has no `project_id` key at all is skipped, because FM-002
and FM-005 already own that, and so is a document no config governs.

Phase 1 repairs the two cases that are never deliberate: an empty value and
the `init` placeholder `my-project`. It does so only when exactly one config
claims the file, which `cli._discover_doc_claims` records alongside the
schema; when two configs claim the same folder there is no single governing
ID to write and the finding stays a report. A different, non-placeholder value
may be intentional, so it is never rewritten - that is the check's whole
safety margin. The rewrite goes through `fix_frontmatter_metadata`, ahead of
`ensure_required_fields` so a document missing `project_id` entirely gets the
real ID instead of the placeholder, and `add_missing_frontmatter` seeds the
generated block with the same value so a repaired document needs no second
pass.

**ID-010 Numbering gaps (shipped).** For each type, the numeric parts of the
ids are sorted and the numbers missing between the lowest and highest are
reported, with `docuchango bulk compress-ids` named as the remedy - that is
the command that renumbers a type into a contiguous sequence and rewrites the
references. Gaps are common and often deliberate after a withdrawn proposal,
so the check is opt-in per type via
`structure.doc_types.<type>.report_numbering_gaps: true` and defaults to off.
The opt-in is keyed by the schema the `doc_types` entry binds, so two entries
that bind the same schema share one sequence and enabling the flag on either
reports that whole sequence. No structure-level default was added: unlike
`scan_subfolders`, which changes what is scanned for every type at once, a
numbering policy is a per-type decision, and a legacy layout with no
`doc_types` map has nothing to attach it to.

Sequences are grouped per (governing config, id prefix), resolved with the
same `_config_context_for_path` that RD-001 and FM-010 use, so a monorepo's
two `adr/` folders are two independent sequences rather than one with holes
in it. An id is part of a sequence only when it is exactly `<prefix>-<number>`:
an ADR amendment id (`adr-043-a1`) hangs off its parent and is not a number of
its own. Missing numbers are printed as a compact range list
(`missing 3, 5-7`), and the finding is reported once per type against
`DocValidator.errors` rather than against any one document, because no single
file is at fault - the CLI shows it at the repository root, the same place a
`SCAN-001` or a blocked config path lands. Report only.

**FM-011 Date format (shipped).** `created` is typed
`datetime | date | str` in every schema and `updated` is in no schema at all,
so a date in any shape whatsoever passed FM-002, and FM-006 rewrote only the
formats it recognized and said nothing about the rest. `check_date_formats`
now accepts exactly the two forms the bundled templates use - `YYYY-MM-DD` and
`YYYY-MM-DDTHH:MM:SSZ` - and reports everything else as
`FM-011: Frontmatter field 'created': '2024-1-5' is not YYYY-MM-DD or
YYYY-MM-DDTHH:MM:SSZ`, naming the field and the value as written. The shape is
matched with a regex and the digits are then parsed, so a well-shaped but
impossible `2024-13-45` is reported too. Report only: FM-006 already rewrites
what can be rewritten with confidence, and guessing whether `01/02/2024` is
January or February is exactly what it refuses to do.

The check reads the scalars out of the document source with `yaml.compose`
rather than off the parsed metadata, because the parse erases the distinction
the check is about. YAML resolves an unquoted `2024-01-05` to a
`datetime.date` and both `2024-01-05T10:00:00Z` and `2024-01-05T10:00:00+00:00`
to the same aware `datetime`, so only the source text can tell the accepted
`Z` form from the offset form. A UTC offset is not accepted: this RFC names
`Z`, and `Z` is what `fixes/timestamps.py` writes wherever docuchango
generates a timestamp itself. Quoting makes no difference - `'2026-05-30'`
and `2026-05-30` are the same value and both pass.

Two inputs are skipped so nothing is said twice. A field that is absent, and a
field written `created:` with no value at all, which YAML resolves to `None`:
FM-002 owns a missing or null `created`, and FM-005 fills one in. An explicit
empty string is reported, as `(empty)`, because the schema accepts it. A value
YAML never parses at all - an unquoted `created: 2024-13-45`, which PyYAML
raises on - never reaches this check either; the document fails to parse and is
reported as such.

Phase 1 runs before the checks, so a format FM-006 recognizes is already ISO
8601 by the time Phase 2 looks and FM-011 stays silent; a `--dry-run` reports
both FM-006's proposed rewrite and the FM-011 finding, since nothing has been
written, which is how FMT-012 presents the same pairing. A format FM-006
cannot identify is an FM-011 report in either mode.

**LNK-011 Cross-plugin link rewrite (shipped).** `fixes/cross_plugin_links.py`
predates the validator and `validate` never called it, so an LNK-002 finding -
a relative link that climbs out of the repository root into a sibling checkout
or another Docusaurus plugin - was a report whose advice ("use an absolute
GitHub URL for external references") the user had to follow by hand. Phase 1
now writes that URL, when the config that governs the linking document says
which repository this is.

`project.repository_url` is the base under which the repository's file tree is
served, and the rewrite is `<repository_url>/<path from the repository root to
the target>`: a trailing slash is stripped from the configured URL, the
target's path relative to `--repo-root` is appended in POSIX form, and the
anchor or query is kept as written. No forge-specific segment such as
`/blob/main/` is inserted. That is the least surprising rule of the ones
available: a user who wants the GitHub blob view writes
`https://github.com/org/repo/blob/main` in the config, a user on a different
forge, a different branch or a plain file server writes that instead, and
neither is a code change. The value is validated at config-load time as an
absolute `http(s)://` URL with a host, because an SSH clone URL or a bare
hostname pasted there would otherwise produce links that resolve nowhere.

An LNK-002 target is by definition outside `--repo-root`, so its relative path
begins with `../`, and those segments are consumed from the end of the
configured URL's path the way a browser resolves them. That is what makes the
rule work for the case that produces these findings in the first place: a run
pointed at one checkout, or one package, of a larger tree. With
`--repo-root site` and
`repository_url: https://github.com/org/repo/blob/main/site`, a link to
`../../../shared/reference/glossary.md` becomes
`https://github.com/org/repo/blob/main/shared/reference/glossary.md`. When the
`../` segments outrun the configured URL's path, the URL is not deep enough to
say where the target lives, and the link stays a report rather than becoming a
guess.

Two constraints keep the fix safe under the default atomic run, where a fix the
check still reports withholds every fix in the tree. The target must exist on
disk: a link that escapes the repository *and* points at nothing is a typo, and
freezing a typo into a well-formed absolute URL would hide it behind a 404 no
check in this repository can see again. And which links escape at all is
decided by `links.resolve_repository_escape`, shared with
`check_cross_plugin_links`, so the fixer cannot rewrite a link the check is
happy with. The fixer matches inline links one line at a time, as LNK-010 does,
while the check also matches a link whose label and target straddle a newline;
the fixer's set is therefore a subset of the check's, which is the safe
direction. Code masking is `markdown.mask_code`, shared with the check, so a
link inside a fence or an inline span is invisible to both.

The URL is resolved per document. `cli._discover_doc_claims` carries the
governing `project.repository_url` alongside the schema and project ID it
already carried for FM-010, and a sub-project that declares none inherits the
URL of the config that included it, up to the root: a monorepo is usually one
repository, and a sub-project checked out from a different one says so by
declaring its own. When two configs claim the same folder with different URLs
there is no single repository to rewrite against and the link stays a report,
the same rule FM-010's placeholder fix uses for a contested `project.id`.
`DocValidator._repository_url_for` resolves the same value through
`_config_context_for_path` for the report side, which is how LNK-002 knows to
add "setting project.repository_url ... lets LNK-011 rewrite this link for you"
to a finding whose target exists and whose project has no URL - and to leave
that sentence off a finding LNK-011 would decline anyway.

What the module used to do was rewrite `../rfcs/RFC-001-x.md` to the Docusaurus
route `/rfc/RFC-001-x` for three hard-coded folder names. Those links resolve
perfectly well on disk and are not LNK-002 findings at all, the routes were one
site's layout, and nothing checked that the route existed. The standalone entry
point survives as `python -m docuchango.fixes.cross_plugin_links --repo-root
<path>`, discovering documents and their URLs through the same `cli` helpers
`validate` uses.

LNK-002 also takes the `LNK-002:` message prefix here, per the "Error message
format" rule, since its wording had to be touched for the nudge anyway.

**LNK-010 Internal link rewrite (shipped).** `fixes/internal_links.py`
existed since before the validator and `validate` never called it, so every
broken link was a report even when the file the author meant was one folder
over. Phase 1 now runs it: when a link is broken and exactly one document in
the scanned set carries the target's filename, the link is rewritten to the
correct relative path from the linking document, POSIX separators, anchor and
query kept as written. Two or more candidates are a judgement call and stay a
report; LNK-001's message now names them, relative to the linking document, so
the author is choosing between paths rather than searching for them. Zero
candidates is the same report it always was.

The rule is filename identity and nothing cleverer. What the module used to do
was pattern rewriting for one migration - strip a `2025-10-13-` date prefix,
adjust `../` depth - which could not tell a link that already resolved from one
that did not, and happily rewrote a link to a file that existed in neither
form. Filename identity against the scanned set is checkable: a rewritten link
is guaranteed to resolve on the next pass, which is what makes the fix safe
under the default atomic run, where a fix the check still reports withholds
every fix in the tree.

That guarantee comes from sharing the code rather than from agreeing by hand.
`docuchango/links.py` now holds `LinkType`, the inline-link pattern,
`classify_link`, `link_path_target` and `resolve_link_target` that
`DocValidator` used to keep to itself, plus `resolve_internal_link`, which is
the one function both LNK-001 and LNK-010 resolve a target with:
site-root against the repository root, and `./x`, `../x` and the bare relative
`adr/x.md` against the linking document's folder, `.md` appended to a
suffix-less target, an existing directory left alone. `DocValidator._mask_code`
moved to `markdown.mask_code` next to `fence_mask`, so a link inside a code
fence or an inline span - sample Markdown in a how-to - is invisible to the
check and to the fix alike. Reference-style links and images are not checked by
LNK-001 and are not rewritten either; widening the fix past the report is
exactly the drift the shared module exists to prevent.

Three things are deliberately left alone. A target carrying a CommonMark link
title, the angle-bracket destination form or percent-escapes: re-encoding those
is guesswork. A candidate outside the repository root, which a sub-project with
`security.allow_external_paths` can produce - rewriting a link into an LNK-002
finding is not a repair. And a link that already resolves, so a second run is a
no-op.

The fixer runs after the per-file Phase 1 loop rather than inside it, because
it is the first fix that needs the whole scanned set: the candidate index is
built once from the discovered documents and then reused for every file. The
standalone entry point survives as `python -m docuchango.fixes.internal_links
--repo-root <path>`, discovering documents through `cli._discover_doc_files`
instead of resolving `docs-cms` relative to the installed package, which
pointed at site-packages for anything but a source checkout.

**MDX-010 MDX escapes (shipped).** MDX-001 has reported a bare `<token>` in
prose since the check was reworked in PR #71, and `fixes/mdx_syntax.py` sat in
the tree unwired the whole time - fixing something else entirely. Its regex
backtick-wrapped `<10ms`, `<1 minute` and `<100%`, which is exactly the class
of text MDX-001 decided is *not* a finding: a `<` before a digit or a space is
a comparison and MDX never reads it as JSX. It also carried its own
`in_code_block` tracker that knew about backtick fences only, and gave up on
any line that mixed a backtick with a `<`. So the fixer repaired what was not
broken, missed every actual finding, and disagreed with the check about where
code is. All three are gone: the `<digit` rewriting, the ReDoS-bounded unit
pattern it needed, and the standalone `main()` that resolved `docs-cms`
relative to the installed package.

What replaces it is the same shape FMT-002/FMT-011 took. `markdown.py` now
holds `mask_code`, `is_safe_mdx_tag` and the tag-candidate pattern that
`DocValidator` used to keep to itself, and builds `mdx_tags` on top of them;
`check_mdx_compatibility` reports one `MDX-001` per tag that function returns
and `escape_mdx_tags` rewrites exactly those tags. The fixer is a wrapper over
that function, so it repairs what the check reports, no more and no less. As
with FMT-011, sharing the scan is not tidiness: under the default atomic run a
fixer that disagreed with its check by one candidate would withhold every fix
in the tree.

The repair is `<` to `&lt;` and `>` to `&gt;` across the candidate, which the
`[^<>]*` bound makes unambiguous: the only `<` is the opening one and the only
`>` is the closing one, and nothing in between is rewritten. `&` is left alone,
which is what makes a second run a no-op - `&lt;token&gt;` has no `<` left to
match. Phase 1 reports one
`MDX-010: Line 19: Escaped '<token>' in prose as '&lt;token&gt;'` per
candidate, and MDX-001 stays the report, which is what a `--dry-run` shows.

Nothing MDX-001 tolerates is touched: content inside fenced blocks (backtick
and tilde), inside inline code spans including multi-line ones, and inside the
frontmatter block is masked before the scan; comparisons, known HTML elements,
PascalCase components, explicitly self-closing tags and CommonMark autolinks
are dropped by `is_safe_mdx_tag`. The fixer widens and narrows MDX-001's
judgment by exactly nothing, because it does not have its own.

It runs after `fix_code_blocks` in Phase 1, because what counts as prose
depends on the fences: CB-001's repair closes an unclosed fence and strips the
stray info string off a closing one, and masking a document whose fences are
still broken would treat everything after the break as code. The cost is that
an MDX-010 line number is the line in the partly repaired file, which can
differ from the line MDX-001 reported for the file on disk when the same run
also inserted a blank line around a fence. Correct masking is worth more than a
message that agrees with a dry run of a different document. MDX-011 is
untouched and stays `Planned`: an indented code block is still masked as prose
by both the check and the fix, so a `<token>` in one is reported and escaped
together, which is at least consistent.

### Planned validators

Each entry lists what it detects, what it may fix, and the constraint that
keeps it safe.

**MDX-011 Indented code blocks.** `markdown.mask_code` masks fenced blocks and
inline spans before the prose checks run, but not 4-space indented code
blocks, so a `<token>` placeholder inside one is reported - and, since
MDX-010, escaped as well. Correct handling needs list-continuation context,
because a 4-space indent inside a list item is a paragraph, not code.

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
   module under `docuchango/fixes/` that returns what it changed. `DocValidator`
   only reports - Phase 1 of `validate` in `cli.py` is the single path that
   writes to disk, so the two can never drift.
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
- Whether ID-010 belongs in `validate` at all, or only as a `bulk` report. It
  shipped in `validate`, opt-in and off by default, which keeps the question
  open rather than settling it: a repository that never turns the flag on
  pays nothing for it.

## Future Possibilities

- A `validation.ignore` list of finding IDs in `docs-project.yaml`.
- A `--format json` output for `validate` keyed by finding ID for CI
  annotations.