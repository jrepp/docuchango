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

Unknown lowercase token names are rejected. Missing required files, invalid
config, and rendering errors are reported before files are written. Use the YAML
tokens without additional quotes. Edit the generated rules and prompt directly,
or maintain a custom bundle to reuse them across projects. Bootstrap never
automatically migrates existing documentation.
