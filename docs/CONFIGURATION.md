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
docuchango_version: "1.19.0"

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

`project.id` is the value every document's `project_id` field must match.
`document_folders` lists the folders that are scanned; anything outside them
is ignored.

## Several documentation roots

A monorepo can keep documents in more than one place. `docs_roots` lists the
directories to scan, relative to the config file:

```yaml
structure:
  docs_roots:
    - .
    - services/billing/docs
    - services/search/docs
```

Each root is scanned for the same `document_folders`.

## Sub-projects

Rather than one large root config, a parent can include configs that belong
to sub-projects or git submodules. Each entry is either a directory containing
a `docs-project.yaml` or the file itself:

```yaml
subprojects:
  - vendor/service-a
  - vendor/service-b/docs-project.yaml
```

Each sub-project is validated with its own config, its own `project.id`, and
its own rules.

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
| `schema` | `adr`, `rfc`, `memo`, `prd`, or `generic`. Generic requires only the common fields. |
| `folders` | Folders (relative to each docs root) holding this type. |
| `filename_pattern` | Regex a filename must match. |
| `enforce_filename_pattern` | Report a mismatch as an error (`true`) or ignore it (`false`). |
| `require_frontmatter` | Set `false` to allow plain Markdown files with no frontmatter block. |
| `naming_standard` | A named filename rule instead of `filename_pattern`; see below. |

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
required under time-bucket headings.

```yaml
indexes:
  - name: Shared Design Index
    path: docs/design-index.md
    targets:
      - docs/design/**/*.md
    require_all_targets: true    # every target must be linked
    require_entries: true        # the index cannot be empty
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

When the optional `textstat` dependency is installed, paragraphs longer than
`min_paragraph_length` are scored and reported against these thresholds.
Disable the whole check with `enabled: false`.

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

1. Run `docuchango init --path <your docs dir>` to get a config, schema and
   templates. It will not overwrite existing files unless you pass `--force`.
2. Map your existing folders with `doc_types`. Start with
   `enforce_filename_pattern: false` and `require_frontmatter: false` on
   folders that are not ready, then tighten one folder at a time.
3. Run `docuchango migrate --project-id <id> --dry-run` to see what legacy
   frontmatter would be upgraded, then run it for real.
4. Run `docuchango validate --dry-run`, fix or accept what remains, and add
   the CI check from the [README](../README.md#validate-in-ci).
