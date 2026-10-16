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
