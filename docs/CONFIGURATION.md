# Configuring docuchango

All configuration lives in `docs-project.yaml` at the root of a docs project.
`docuchango init` writes one with every option present as a comment, and a
`docs-project.schema.json` next to it so editors can validate and autocomplete
the file. The same schema is published at
`https://jrepp.github.io/docuchango/schemas/docs-project.schema.json`.

The default file works for a single `docs-cms/` folder with the four standard
document types. This page covers everything beyond that.

## Minimal file

```yaml
# yaml-language-server: $schema=./docs-project.schema.json
version: "1"
docuchango_version: "1.19.0"  # written automatically by 'docuchango init';
                               # it records the version that generated this
                               # file, not one you need to match by hand

project:
  id: my-app
  name: My App
  description: Documentation for My App

structure:
  adr_dir: adr
  rfc_dir: rfcs
  memo_dir: memos
  prd_dir: prd
  template_dir: templates
  document_folders: [adr, rfcs, memos, prd]
```

`project.id` is the value to copy into each document's `project_id` field.
The match is a convention: `project_id` is required on every document, but
docuchango never compares it against `project.id`. `document_folders` lists
the typed folders (ADR, RFC, memo, PRD) that are scanned; it is not the whole
story, though - a top-level `*.md` file directly under a configured docs root
(anything other than `README.md` or `docs-project.yaml`) is still scanned as
a generic document, whether or not its folder is listed.

## Several documentation roots

A monorepo can keep documents in more than one place. `docs_roots` lists the
directories to scan, relative to the config file. It only takes effect for
the standard document folders together with `doc_types` below: with the
plain `adr_dir`/`rfc_dir`/`memo_dir`/`prd_dir` layout, those folders resolve
against the config's own directory, and `docs_roots` is ignored.

```yaml
structure:
  docs_roots:
    - .
    - services/billing/docs
    - services/search/docs
  doc_types:
    adr:
      schema: adr
      folders: [adr]
    rfc:
      schema: rfc
      folders: [rfcs]
```

Each root is scanned for the same `doc_types` folders. To scan roots that
should not share one set of folders and rules, use `subprojects` instead.

## Scanning nested subfolders

By default, only files directly inside a document folder (`adr/`, `rfcs/`,
`memos/`, `prd/`, or a `doc_types` folder) are treated as numbered documents.
A file nested one level deeper, such as `adr/archive/adr-005-old.md` or
`rfcs/2024/rfc-012-legacy.md`, is treated as support material: it is not
checked against the filename pattern, its `id` and `doc_uuid` are not
checked, and its links are not validated.

Set `structure.scan_subfolders: true` to scan nested files with the same
rules as top-level files. The filename pattern and the expected `id` are
still matched against the file name only, not the subfolder path, so
`adr/archive/adr-005-old.md` is still expected to carry `id: adr-005`.

```yaml
structure:
  scan_subfolders: true
```

The default is `false`, which keeps the historical behavior. A `doc_types`
entry can override the structure-level default for just that type with its
own `scan_subfolders: true` or `scan_subfolders: false`:

```yaml
structure:
  scan_subfolders: false
  doc_types:
    adr:
      schema: adr
      folders: [adr]
      scan_subfolders: true  # only ADRs scan their subfolders
```

## Sub-projects

Rather than one large root config, a parent can include configs that belong
to sub-projects or git submodules. Each entry is either a directory containing
a `docs-project.yaml` or the file itself:

```yaml
subprojects:
  - vendor/service-a
  - vendor/service-b/docs-project.yaml
```

Each sub-project is validated with its own config, its own `project.id`, its
own document structure and index rules, and its own `readability` block. A
sub-project that does not declare `readability` inherits it from the config
that included it, up to the root (see [Readability](#readability)).

## Path containment

Paths in a config cannot escape the directory that owns it. If the config is
at `docs/docs-project.yaml`, then `docs_roots`, folders, indexes and
sub-project references cannot use `../` to reach outside `docs/`. This stops a
sub-project's config from pulling in files it does not own.

Use `subprojects` from a parent config when you need to include other roots.
Only if a legacy layout genuinely needs to cross the boundary:

```yaml
security:
  allow_external_paths: true
```

## Mixed document types and schemas

`doc_types` gives each kind of document its own schema, folders, filename
rule and frontmatter policy. When it is set, it replaces `adr_dir`,
`rfc_dir`, `memo_dir` and `prd_dir`.

```yaml
structure:
  docs_roots: [docs]
  doc_types:
    adr:
      schema: adr
      folders: [adr]
      filename_pattern: "^(adr)-(\\d{3})-(.+)\\.md$"
      enforce_filename_pattern: true
    prfaq:
      schema: generic
      folders: [prfaq]
      filename_pattern: "^prfaq-.+\\.md$"
      enforce_filename_pattern: true
    design-notes:
      schema: generic
      folders: [design]
      filename_pattern: ".+\\.md$"
      enforce_filename_pattern: false
      require_frontmatter: false
```

| Key | Meaning |
|-----|---------|
| `schema` | `adr`, `rfc`, `memo`, `prd`, or `generic`. `generic` requires only `title`, `project_id` and `doc_uuid`; `id` and `tags` are optional and there is no `created` or `status`. The fixers follow it too: a generated frontmatter block has the shape of this schema and status variants are mapped with this type's vocabulary, whatever the folder is named. |
| `folders` | Folders (relative to each docs root) holding this type. |
| `filename_pattern` | Regex a filename must match. |
| `enforce_filename_pattern` | Report a mismatch as an error (`true`) or ignore it (`false`). |
| `require_frontmatter` | Set `false` to allow plain Markdown files with no frontmatter block - but only for `schema: generic`. An `adr`, `rfc`, `memo` or `prd` lane still reports a missing block regardless of this setting. |
| `naming_standard` | A named filename rule instead of `filename_pattern`; see below. |
| `scan_subfolders` | Overrides `structure.scan_subfolders` for this type. Leave unset to use the structure-level default. |

## Naming standards

Instead of a raw regex, a doc type can name a standard:

```yaml
structure:
  doc_types:
    guides:
      schema: generic
      folders: [guides]
      naming_standard: kebab-case
    runbooks:
      schema: generic
      folders: [ops/runbooks]
      naming_standard: snake_case
```

Built-in standards:

| Standard | Pattern | Example |
|----------|---------|---------|
| `nnn-name` | `^\d{3}-(.+)\.md$` | `001-intro.md` |
| `year-month-day-name` | `^\d{4}-\d{2}-\d{2}-(.+)\.md$` | `2026-05-25-intro.md` |
| `kebab-case` | `^[a-z0-9]+(-[a-z0-9]+)*\.md$` | `my-document-name.md` |
| `snake_case` | `^[a-z0-9]+(_[a-z0-9]+)*\.md$` | `my_document_name.md` |
| `camelCase` | `^[a-z][a-zA-Z0-9]*\.md$` | `myDocumentName.md` |
| `PascalCase` | `^[A-Z][a-zA-Z0-9]*\.md$` | `MyDocumentName.md` |
| `lowercase` | `^[a-z0-9]+\.md$` | `mydocumentname.md` |
| `uppercase` | `^[A-Z0-9]+\.md$` | `MYDOCUMENTNAME.md` |

Define your own, or override a built-in, under `naming_standards`:

```yaml
structure:
  naming_standards:
    date-prefix: "^\\d{6}-.+\\.md$"
  doc_types:
    reports:
      schema: generic
      folders: [reports]
      naming_standard: date-prefix
```

## Index files

An index is a Markdown file that is supposed to link to a set of other files,
such as a design index or release notes. Index rules are stricter than normal
validation: targets can be required, extra links forbidden, and entries can be
required under time-bucket headings. `path` and `targets` are resolved
relative to the `docs-project.yaml` that declares them - typically
`docs-cms/`, so with the layout used throughout this page these examples
would live under `docs-cms/docs/...`; adjust the paths (for example
`design/**/*.md`) to match whatever you are actually indexing.

```yaml
indexes:
  - name: Shared Design Index
    path: docs/design-index.md
    targets:
      - docs/design/**/*.md
    require_all_targets: true    # every target must be linked
    require_entries: true        # requires at least one link, but only once
                                  # a target actually matches something - an
                                  # empty target glob is not an error
    allow_extra_links: true      # links to non-targets are fine

  - name: Weekly Release Notes
    path: docs/release-index.md
    targets:
      - docs/release-notes/*.md
    time_bucket:
      cadence: weekly            # weekly, monthly, quarterly, yearly, milestone
      field: created             # frontmatter field that places a target
      heading_level: 2
      heading_pattern: "^\\d{4}-W\\d{2}$"

  - name: Milestone Changelog
    path: docs/milestone-changelog.md
    targets:
      - docs/plans/*.md
    time_bucket:
      cadence: milestone
      milestone_field: milestone
      heading_level: 2
```

## Readability

When the optional `textstat` dependency is installed, paragraphs at least
`min_paragraph_length` characters long are scored and reported against these
thresholds. Disable the whole check with `enabled: false`.

Settings are resolved per document from the config that owns it, so in a
monorepo each sub-project can enable, disable or tune readability on its own.
The precedence is:

1. The `readability` block of the config that owns the document - the deepest
   config whose directory or `docs_roots` contain the file.
2. Otherwise the block of the nearest config up the `subprojects` chain that
   declares one, ending at the root config.

The block is taken as a whole, never merged key by key. A sub-project that
declares `readability: {enabled: true}` gets the schema defaults for every
threshold it leaves out, not the root's values. To inherit the root's
thresholds, leave the block out of the sub-project config entirely.

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

## Metadata

Free-form information about the docs project. Nothing here is validated
beyond its shape.

```yaml
metadata:
  created: "2026-09-14"
  maintainers:
    - Platform Team
  purpose: Architecture decisions, proposals, memos and requirements for My App
```

## Adopting docuchango in an existing repository

1. Run `docuchango init --path <a new, empty directory>` to get a config,
   schema and templates, then move them next to your existing documents.
   `init` refuses to write into a directory that already has files in it, and
   `--force` makes it overwrite the files it generates, so pointing it at a
   populated docs folder is not a safe way to add the config in place.
2. Map your existing folders with `doc_types`. Start with
   `enforce_filename_pattern: false` on folders that are not ready, and
   `schema: generic` with `require_frontmatter: false` for folders that are
   not yet in ADR/RFC/memo/PRD shape at all (that combination is the only one
   that accepts plain Markdown); then tighten one folder at a time.
3. Run `docuchango migrate --project-id <id> --dry-run` to see what legacy
   frontmatter would be upgraded, then run it for real.
4. Run `docuchango validate --dry-run`, fix or accept what remains, and add
   the CI check from the [README](../README.md#validate-in-ci).
