# Wiki bootstrap

Opt in when setting up a repository:

```bash
docuchango bootstrap --wiki --project-id my-app --project-name "My App"
```

The default destination is `./docs-cms`. `--path` changes it, and `--force`
overwrites files supplied by the bundle while preserving other files.
Without `--wiki`, `bootstrap` still displays guides. `init` still creates the
numbered ADR/RFC/memo/PRD layout.

```text
docs-cms/
  docs-project.yaml
  docs-project.schema.json
  README.md                     # Wiki home and navigation
  AGENTS.md                     # Editable authoring rules
  pages/getting-started.md       # Shared knowledge
  templates/page.md             # Unnumbered page template
  templates/INITIALIZE.md        # Prompt for extending the wiki
services/auth/docs/
  authentication.md             # Added during repository-specific setup
```

Bootstrap writes the bundle; it does not execute the initialization prompt or
invent system documentation. Give the generated prompt to an agent to inspect
the repository, choose system folders, write grounded pages, and update navigation.

## Overlay an existing RFC/ADR layout

```bash
docuchango bootstrap --wiki --overlay
# Give docs-cms/wiki/templates/INITIALIZE.md to your agent.
docuchango validate --dry-run --skip-build
```

`--path` selects the existing docs-cms directory. Overlay requires a valid
`docs-project.yaml`, inherits its project ID and name, and creates a wiki under
`wiki/`. It registers `wiki/docs-project.yaml` in the parent's `subprojects`.
Existing numbered pages, templates, home pages, and agent instructions keep
their original bytes. Existing configuration values and subprojects are retained;
the parent YAML is reserialized, so comments and formatting may change.
Legacy folder bindings and custom `doc_types` continue to validate as before.

```text
docs-cms/
  docs-project.yaml             # Existing config plus wiki subproject
  rfcs/                        # Existing proposals
  adr/                         # Existing decisions
  templates/                   # Existing numbered templates
  wiki/
    docs-project.yaml           # Generic wiki validation
    README.md                  # Task-to-code navigation
    AGENTS.md                  # Focus and context budgets
    pages/getting-started.md
    templates/page.md
    templates/INITIALIZE.md
```

Add a short link to `docs-cms/wiki/README.md` and its authoring rules from your
repository's existing instructions and documentation home. The initialization
prompt guides that edit; bootstrap preserves those files. Wiki pages explain the
current code route for a task, linking to RFCs/ADRs for rationale and status.
They do not replace decision records or turn proposals into approved decisions.

System folders registered in the overlay config need one extra `../`, for example
`../../services/auth/docs`. Enable external paths in the **wiki** config when
registering those folders. Root validation follows the registered wiki subproject
and validates both documentation styles. Avoid overlapping scan folders.

An existing nonempty `wiki/` or an already registered overlay is rejected before
writing files. Edit that wiki directly to extend it. Overlay does not allow
`--force` or project identity overrides. `--template-dir` can supply the same
replaceable bundle used for a new wiki.

## Keep agent context focused

Use the wiki as a short route from a task to the code and checks needed to do it:

1. Read repository instructions and the wiki's task map.
2. Open only the relevant page, then its linked entry points and tests.
3. Consult linked RFCs/ADRs when the change touches their constraints.
4. Run the page's verification command and update stale navigation with the code.

Each page should answer one question or cover one change task, with source links,
key symbols, tests, a verification command, and constraints. Aim for **500 words
or fewer per page** and **under 100 lines of always-loaded agent instructions**.
Split independent topics before growing a page; explain necessary exceptions in
review. Keep the home a short task map instead of an exhaustive directory tree.

Link to authoritative code and decisions rather than copying them. Keep session
transcripts, progress logs, pasted source, and speculative architecture out of
durable context. Update an existing page before adding another and remove stale
instructions. The generated rules and prompt include these guardrails. They are
authoring and review guidance; `validate` does not enforce these size budgets.

## Extend the wiki into project folders

Register each system's documentation folder in `docs-cms/docs-project.yaml`:

```yaml
structure:
  doc_types:
    wiki:
      schema: generic
      folders: [pages, ../services/auth/docs, ../packages/client/docs]
      naming_standard: kebab-case
      scan_subfolders: true
      require_frontmatter: true
      report_numbering_gaps: false
security:
  allow_external_paths: true
```

Paths are relative to the config, and scanning includes nested Markdown pages.
Register distinct documentation folders, not the repository root or overlapping
folders. The external-path setting permits leaving the config directory; it also
permits leaving the repository, so keep the registered paths inside the checkout.
The built-in bundle leaves it disabled until you register colocated folders.

Link pages with standard relative Markdown links. From
`services/auth/docs/authentication.md`, the home link is
`../../../docs-cms/README.md`. Double-bracket wiki link syntax is not supported.
README landing pages are excluded from document checks; put substantive content
in named pages. An `AGENTS.md` inside `docs-cms` does not automatically govern
sibling folders; reference its rules from repository-level guidance as needed.

Use names such as `authentication.md`, with unnumbered titles and no `id` field.
Pages use the existing generic schema: `title`, `project_id`, and a UUID v4
`doc_uuid` are required. The UUID is internal metadata, not an external sequence.
Copy the page template and generate a fresh UUID for every new page.

Run `docuchango validate --dry-run --skip-build` from the repository root.
A plain `validate` applies repairs. Custom destinations must be discoverable:
the repository root's `docs-project.yaml`, `docs-cms/docs-project.yaml`, or
`docs/docs-project.yaml`, or a configured subproject.

## Replace the template bundle

```bash
docuchango bootstrap --wiki --template-dir ./my-wiki-bundle
```

The directory replaces the entire built-in bundle. Copy the bundled
`docuchango/templates/wiki/` directory as a starting point. All files must be
UTF-8 text. Relative paths are preserved; symlinks are rejected. These files
are required:

- `docs-project.yaml`: configuration, checked against the existing schema.
- `README.md`: home page and navigation.
- `AGENTS.md`: authoring rules.
- `templates/INITIALIZE.md`: repository initialization prompt.
- `templates/page.md`: page template.

Add starter pages as needed and register their folders in the config. The current
config JSON schema is always supplied by Docuchango. Keep non-page instructions
under `templates/`, outside the configured scan folders; root Markdown files
other than README are also validated and need generic frontmatter.

Rendering substitutes these exact tokens once, without executing code:

| Token | Value |
|-------|-------|
| `{{project_id}}` | Project ID as text |
| `{{project_name}}` | Project name as text |
| `{{project_id_yaml}}` | Quoted project ID for a YAML value |
| `{{project_name_yaml}}` | Quoted project name for a YAML value |
| `{{doc_uuid}}` | Fresh UUID v4 per file |
| `{{date}}` | Current date in ISO format |
| `{{version}}` | Installed Docuchango version |
| `{{system_docs_example}}` | Example system folder relative to the config, adjusted for overlay depth |

Unknown lowercase token names are rejected. Missing required files, invalid
config, and rendering errors are reported before files are written. Use the YAML
tokens without additional quotes. Edit the generated rules and prompt directly,
or maintain a custom bundle to reuse them across projects. Bootstrap never
automatically migrates existing documentation.
