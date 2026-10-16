# Initialize the project wiki

Inspect this repository and extend the wiki rooted beside this templates folder.
Read its README, docs-project.yaml, and AGENTS.md first. Follow the repository's
existing instructions and preserve existing documents.

1. Identify the main systems from code, build files, and existing documentation.
   Do not infer architecture from folder names alone.
2. Keep shared concepts under the wiki's pages folder. For each system needing
   documentation, choose a docs folder next to that system's code.
3. Register those folders in structure.doc_types.wiki.folders using paths relative
   to docs-project.yaml. Enable security.allow_external_paths when needed to reach
   system folders outside the wiki root. Keep all selected folders inside the
   repository, and avoid broad or overlapping scan roots.
4. Create concise overview pages using templates/page.md, each with a fresh UUID.
   Use descriptive filenames and titles; never add NNN sequences or id fields.
   Ground claims in inspected code and flag unknowns rather than inventing details.
5. Link system overviews from the wiki home and link them back to the home. Use
   standard relative Markdown links, not double-bracket wiki links.
6. Apply the wiki authoring rules to system pages. If repository-level agent
   instructions need an update to reference those rules, preserve existing guidance.
7. Run docuchango validate --dry-run --skip-build from the repository root. Resolve
   issues within scope and summarize pages created, folders registered, and any
   remaining manual issues.

Do not migrate or renumber existing numbered documents as part of initialization.
