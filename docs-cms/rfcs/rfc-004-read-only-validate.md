---
author: Engineering Team
created: 2026-10-09
doc_uuid: 575159fe-a7d0-4641-a96f-01ece25f720f
id: rfc-004
project_id: docuchango
status: Proposed
tags: [cli, compatibility, validation]
title: Read-Only Validate by Default
---

# RFC-004: Read-Only Validate by Default

## Summary

`docuchango validate` repairs documents unless `--dry-run` is passed. This RFC
asks whether checking and repairing should be separated so that a command
named `validate` never writes to the working tree by default. It lists the
options and a migration path that does not break existing users. Nothing here
is decided: the status stays `Proposed` until the maintainer chooses an
option.

## Motivation

The verb "validate" reads as a check. Most linters and validators only write
when a flag such as `--fix` or `--write` asks them to. People and agents
running `docuchango validate` in a pre-push hook or an editor task do not
expect it to rewrite their files.

The Prism repository is a real example. Its pre-push guard called
`docuchango validate` from `PATH`. The repairs in that run rewrote
`docs-cms/`, and two of them were bugs:

- FM-007 inserted `created` after a `status:` line in a fenced code block,
  and after a body bullet that began `Work status:`. It added another line on
  each run.
- FM-008 removed the final newline of every file whose tags it sorted.

Both bugs are fixed, and the regression fixtures cover them. A fixer will
still have a bug sooner or later. When the repair runs by default, that bug
lands in the user's tree, often without anyone reading the diff. Prism
switched its hook to its own read-only validator to avoid this.

The current design has two safeguards:

- `--dry-run` reports what would change and writes nothing. The README already
  tells CI users to pass it.
- A fixing run is atomic by default. If any issue remains after Phase 1, every
  fix is withheld and the tree stays as it was.

The atomic run does not help when the fixes themselves are wrong. A run whose
fixes clear every issue writes them all, even when one fix corrupted the body
of a document.

## Current Behavior

| Invocation | Writes to the tree |
|------------|--------------------|
| `docuchango validate` | Yes, when Phase 1 clears every issue (atomic) |
| `docuchango validate --no-atomic` | Yes, even when issues remain |
| `docuchango validate --dry-run` | No |
| `dcc-validate` | Same as `docuchango validate` |

## Options

### Option A: Keep the current default

Leave the behavior alone and document it in the CLI help and the validation
reference.

- Pro: no migration for anyone.
- Con: the name still promises a check, and the next fixer bug will reach
  users the same way.

### Option B: Add explicit flags now, keep the default

Add `--check` as an alias for `--dry-run`, and add `--fix` as an explicit
form of today's default. A plain `validate` keeps fixing.

- Pro: purely additive. Scripts and docs can state their intent today and are
  ready if the default ever changes.
- Con: changes nothing for people who do not read the release notes.

### Option C: Deprecate the implicit fix, then flip the default in 2.0

1. In a minor release, ship Option B. When `validate` writes without an
   explicit `--fix`, print a one-line deprecation notice to stderr. The notice
   says the default changes in 2.0 and names `--fix`. Exit codes and output on
   stdout do not change.
2. In 2.0, a plain `validate` is read-only, the same as `--check` or
   `--dry-run` today. `--fix` keeps the current behavior. The changelog
   carries a `BREAKING CHANGE` footer.

- Pro: the name matches the behavior, and users get at least one release of
  warning.
- Con: a major version bump. Anyone who relies on the implicit fix, such as
  local scripts or `uvx docuchango validate` in a README, must add `--fix`.

### Option D: Separate commands

Add `docuchango check` (read-only) and `docuchango fix` (repairs, then
checks). `validate` stays as it is and becomes a documented alias for `fix`,
possibly deprecated later.

- Pro: no flag to forget, and no change to existing `validate` callers.
- Con: two names for the same thing during the transition, and the commands
  in every doc and agent guide need updating.

### Option E: Per-project setting

Add a key such as `validation.fix_by_default` to `docs-project.yaml`. It
defaults to `true` today, and a project sets `false` to make a plain
`validate` read-only.

- Pro: a project like Prism can opt out without waiting for 2.0.
- Con: the same command does different things in different repositories,
  which is the surprise this RFC is trying to remove. It also adds another
  config key to document and validate.

## Recommendation

Option B now, followed by Option C if the maintainer agrees to a 2.0. Option B
is additive and safe in any release. Option C gives the name the meaning
users already assume, with a deprecation window. Option D is a reasonable
alternative if the maintainer prefers new verbs to a flag. Option E is the
weakest choice, because the default then depends on the repository.

This RFC does not change behavior. It is the record of the question and the
options. The decision, and any `Accepted` status, belongs to the maintainer.

## Compatibility

- Today, `--dry-run` is the read-only mode, and it must keep working under
  every option above.
- Under Option C, a CI job that already passes `--dry-run` is unaffected.
  Only callers that rely on the implicit fix change.
- The `fix` and `report` modes in the RFC-003 finding registry describe what
  a fixing run repairs. They stay valid under every option, because only the
  default invocation changes.

## Unresolved Questions

- Should `dcc-validate` follow `validate`, or become the stable name for the
  fixing behavior?
- Should the 2.0 default also skip the Docusaurus build, which writes build
  output even on a read-only run?
- Is one minor release a long enough deprecation window, given how often
  docuchango ships release candidates?
