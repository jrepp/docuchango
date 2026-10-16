---
author: Engineering Team
created: 2026-10-16
doc_uuid: 6e341241-f3d7-414d-8eb0-f0c5eb638832
id: memo-004
project_id: docuchango
tags: [bootstrap, documentation, templates, wiki]
title: Opt-in Wiki Bootstrap
---

# Memo-004: Opt-in Wiki Bootstrap

## Requested behavior

Provide a reusable wiki style through `docuchango bootstrap --wiki`. The wiki
starts at `docs-cms/` and extends into documentation folders beside the systems
they describe. Pages use descriptive filenames and titles without external NNN
numbering. The repository's existing numbered documentation remains in place.

## Implementation

The wiki is a template bundle, not a new validator schema. It uses the existing
generic schema, kebab-case naming, and recursive folder scanning. Pages retain
internal UUID metadata and omit public document IDs. Shared pages live under
`pages/`; system documentation folders are registered explicitly in the config.

The bundle contains configuration, a home page, a starter page, a page template,
agent rules, and an initialization prompt. Bootstrap writes these files without
running the prompt. `--template-dir` replaces the bundle, so projects can supply
their own rules and initialization workflow without changing Python code.

The existing `security.allow_external_paths` setting is needed for folders outside
the config directory. It defaults to false in the bundle; the setup prompt explains
enabling it for registered system folders inside the repository. It does not
provide repository containment, so paths must be selected deliberately. Avoid
overlapping folders and repository-wide scans.

## Compatibility and verification

Plain `bootstrap` continues to print guides, and `init` keeps the numbered layout.
No validator behavior or finding registry entries change. The generic schema
still requires title, project ID, and UUID frontmatter. README landing pages
remain excluded from checks. Agent rules in the wiki directory need a reference
from repository-level guidance to apply to sibling system folders.

CLI integration tests cover bootstrap, validation of a page beside a system,
custom bundles, replacement behavior, invalid bundles, and incompatible flags.
See [the wiki guide](../../docs/WIKI.md) for the bundle contract and setup steps.

Filesystem acceptance tests in `tests/test_wiki_acceptance.py` launch separate
CLI processes against the wiki cases in `tests/fixtures/findings/`. These cases
also run in the existing finding regression harness. They cover nested system
pages, repeated basenames, cross-system links, code examples, scan boundaries,
invalid metadata, link repairs, CRLF normalization, and atomic withholding.
Repair cases specify exact expected file contents. Tests compare the entire
tree, revalidate the repaired content, and verify a second repair changes nothing.

## Existing layouts and focused context

The additional requirement is to extend existing RFC/ADR documentation with a
wiki overlay that gives agents direct routes through the code. Existing decision
records remain authoritative; wiki pages link to their rationale and status.

`bootstrap --wiki --overlay` adds `docs-cms/wiki/` as a registered subproject,
using the existing project's identity. This retains both legacy folder bindings
and custom document types without converting their validation rules. Existing
documents, templates, and instructions are preserved. The parent configuration
keeps its values and receives the subproject reference; YAML reserialization
can change formatting and remove comments. Existing overlays are rejected to
avoid replacing authored pages. The initialization prompt guides adding a short
navigation pointer to existing repository instructions.

The implementation uses authoring budgets of 500 words per wiki page and fewer
than 100 lines of always-loaded instructions. These are review guidance, with
exceptions explained in review, rather than new validator checks. A page covers
one task or question and links entry points, symbols, tests, verification commands,
and decision records. Agents load relevant pages on demand. Session transcripts,
copied source, exhaustive trees, and speculative claims do not belong in context.

Overlay integration tests cover legacy and custom layouts, continued RFC and wiki
validation, identity inheritance, preservation of existing files, conflicting
destinations, and repeat invocation without changes.

Bootstrap preflight rejects symlinks in destination components below the wiki
root, including links to unrelated files inside that root. Overlay pages beside
code retain the registering config's FM-010 project identity and RD-001
readability settings through scan-folder ownership, including when a service
subproject surrounds the folder. Blocked external paths do not claim ownership.
