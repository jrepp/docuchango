---
title: Wiki authoring rules
project_id: {{project_id_yaml}}
doc_uuid: {{doc_uuid}}
created: '{{date}}'
tags: [documentation, wiki]
---

# Wiki authoring rules

- Read the wiki home, then only the pages relevant to the current task.
- Keep shared knowledge in this wiki's `pages/` and system knowledge beside the code.
- Register system documentation folders in the root wiki config. Use relative
  Markdown links to connect the home, system overviews, and related pages.
- Use descriptive filenames and titles without external numbering or `id` fields.
- Start pages from `templates/page.md`; generate a new UUID for every new page.
- Update existing pages when knowledge changes. Record proposals as proposals;
  do not describe an inferred decision as approved.
- Keep navigation current when moving a page, including links back to the home.
- Validate from the repository root and report unresolved findings.

## Keep context small

- Aim for at most 500 words per wiki page, answering one task or system question.
  Before exceeding that budget, split independent topics into linked pages.
  Explain an exception in review when splitting would hide necessary context.
- Keep always-loaded repository instructions under 100 lines where practical.
  Put task-specific detail in linked pages and read those pages on demand.
- Keep the home page a short task-to-page map. Do not load or summarize the whole
  wiki or decision archive for every task; follow relevant links only.
- Give each task route its entry points, key symbols, relevant tests, verification
  command, and constraints. Link to inspected source files and authoritative
  RFCs/ADRs; preserve their status and do not duplicate their full explanations.
- Keep proposed changes in RFCs and decisions in ADRs. Wiki routes describe current
  code and link to those records for rationale, including unresolved proposals.
- Exclude session transcripts, progress logs, pasted source files, exhaustive file
  trees, and speculative architecture. Keep only reusable facts needed for action.
- Update an existing page before adding another. Remove stale instructions and
  repair links when code moves. Review scope, size, and evidence with each edit.

These budgets are authoring and review guardrails, not validator-enforced limits.
