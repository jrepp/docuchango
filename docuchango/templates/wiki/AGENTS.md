---
title: Wiki authoring rules
project_id: {{project_id_yaml}}
doc_uuid: {{doc_uuid}}
created: '{{date}}'
tags: [documentation, wiki]
---

# Wiki authoring rules

- Read the wiki home and relevant system pages before changing a system.
- Keep shared knowledge in `docs-cms/pages/` and system knowledge beside the code.
- Register system documentation folders in the root wiki config. Use relative
  Markdown links to connect the home, system overviews, and related pages.
- Use descriptive filenames and titles without external numbering or `id` fields.
- Start pages from `templates/page.md`; generate a new UUID for every new page.
- Update existing pages when knowledge changes. Record proposals as proposals;
  do not describe an inferred decision as approved.
- Keep navigation current when moving a page, including links back to the home.
- Validate from the repository root and report unresolved findings.
