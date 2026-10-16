# {{project_name}} wiki

Start with [Getting started](pages/getting-started.md).

This folder is the wiki home and configuration root. Keep shared concepts in
`pages/`. Keep system documentation beside its code, such as
`services/auth/docs/overview.md`, and link to it from here using relative paths.

To extend the wiki, add `../services/auth/docs` to
`structure.doc_types.wiki.folders` in `docs-project.yaml` and set
`security.allow_external_paths: true`. Paths are relative to the config file.
Only register intended documentation folders; do not register the whole repository
or overlapping folders. This setting permits paths outside the config directory,
including outside the repository, so review each registered path.

Use descriptive names such as `authentication.md` or `recovery.md`. There are
no numbered filenames, document IDs, or numbered title prefixes. Metadata uses
an internal UUID, which is not a visible document number.

Copy [the page template](templates/page.md), set its title and replace its
`doc_uuid` with a fresh UUID for each page. Link new pages from the wiki home
or a system overview, and link system overviews back to this home.

[Agent rules](AGENTS.md) and [the initialization prompt](templates/INITIALIZE.md)
are editable parts of this bundle. Bootstrap writes the prompt; give it to your
agent to map the repository and extend the wiki. It does not run the prompt.
Rules in this folder do not automatically govern sibling system folders: have
repository-level agent instructions reference them where appropriate.

Run from the repository root:

```bash
docuchango validate --dry-run --skip-build
```

A plain `docuchango validate` applies repairs. For a custom wiki root, pass the
repository root with `--repo-root` and ensure its config is discoverable (standard
locations are `docs-project.yaml`, `docs-cms/docs-project.yaml`, and
`docs/docs-project.yaml`). README landing pages are excluded from document checks;
keep substantive content in named pages. Wiki pages with frontmatter must include
`title`, `project_id`, and `doc_uuid`.
