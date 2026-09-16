# Finding regression fixtures

Each directory here is a miniature repository that reproduces exactly one
finding from the registry in
[`docs-cms/rfcs/rfc-003-validator-roadmap.md`](../../../docs-cms/rfcs/rfc-003-validator-roadmap.md),
together with an `expected.yaml` that records what `docuchango validate`
should say about it.

`tests/test_findings.py` discovers every directory, copies it under `tmp_path`,
and runs the real Click command against the copy twice: once with `--dry-run`
and once without. Nothing here is imported by hand; adding a case is dropping
in a directory.

## Layout

```text
tests/fixtures/findings/
  FM-002-invalid-status/
    expected.yaml
    docs-cms/
      docs-project.yaml      # optional
      adr/adr-002-invalid-status.md
```

The directory name is `<FINDING-ID>` with an optional `-slug` suffix, so one
finding can own several cases: `FM-002-invalid-status` and
`FM-002-missing-title` both map to `FM-002`. Directories whose name starts with
an underscore (`_baseline`) are support cases and are not keyed to a finding.

Everything below the case directory except `expected.yaml` is copied verbatim
and becomes the `--repo-root` that `validate` is pointed at. If the tree
contains no `docs-project.yaml`, the harness writes a default one declaring
`project.id: fixture-project` and the `adr`/`rfcs`/`memos` folders. Supply your
own when the finding depends on configuration, as `RD-001-unreadable-paragraph`
does.

A case can point `--repo-root` at a subdirectory of itself with `repo_root:` in
`expected.yaml`. The whole case directory is still copied, so the files outside
that subdirectory are on disk but outside the repository root - which is the
only way to write a case about the repository boundary itself, such as the
`LNK-011-*` pair, where LNK-002 needs a link that escapes the root and LNK-011
needs its target to exist.

## `expected.yaml`

```yaml
summary: One or two sentences on what the documents do wrong.

# Substrings that must appear in `validate --dry-run` output. Whitespace is
# normalized before matching, so Rich's console wrapping does not matter.
# Keep them free of absolute paths, UUIDs and dates so they stay stable.
messages:
  - "Frontmatter field 'status'"

# Does `validate` without --dry-run write the fix to disk, so the messages
# above are gone from the fixing run's output?
#   true  -> the messages above must be gone from the fixing run's output
#   false -> they must still be reported
#
# `fixed` means "written", not "fixable". `validate` is atomic by default: if
# any issue remains after fixing, every fix from that run is withheld and the
# tree is left untouched, even for findings the fixer knows how to repair. So
# a fixture that pairs one fixable finding with one `validate` cannot fix
# needs `fixed: false` under the default atomic run, because the fix is
# withheld, not written. Add `atomic: false` alongside `fixed: true` only when
# the case is specifically about the withheld fix landing once atomicity is
# turned off; that runs the fixing pass with --no-atomic instead.
fixed: false

# Run the fixing pass with `--no-atomic` instead of the default atomic run.
# Only useful together with `fixed: true` on a fixture that combines a
# fixable and an unfixable finding; leave it out otherwise.
atomic: true

# Substrings expected in the "Fixes applied" (or "Fixes withheld", under the
# default atomic run when issues remain) section. Only useful when
# `fixed: true`, or to check the withheld-fix wording when `fixed: false`.
fix_messages: []

# Substrings that must NOT appear in the --dry-run output. Use this to pin
# down a check that used to over-report.
forbidden: []

# Exit codes for `validate --dry-run` and for `validate`.
dry_run_exit_code: 1
exit_code: 1

# Subdirectory of the case that `--repo-root` points at. Defaults to ".", the
# whole case directory. Only useful for a finding about the repository
# boundary, where the case needs files on disk outside the repository root.
repo_root: "."

# Optional third-party modules the case needs. Missing ones skip the case.
requires: []
```

Three assertions run for every case: the `--dry-run` pass must report the
messages and leave the files byte-identical on disk, the fixing pass must match
`fixed`, and a second fixing pass must reach a fixed point.

## Adding a failing-document case

```bash
ID=FM-002                          # an ID from the RFC-003 registry
SLUG=missing-title
mkdir -p "tests/fixtures/findings/$ID-$SLUG/docs-cms/adr"
$EDITOR "tests/fixtures/findings/$ID-$SLUG/docs-cms/adr/adr-001-missing-title.md"
$EDITOR "tests/fixtures/findings/$ID-$SLUG/expected.yaml"
uv run pytest tests/test_findings.py -k "$ID" -q
```

To read the exact wording the validator produces before writing
`expected.yaml`:

```bash
uv run docuchango validate --repo-root "tests/fixtures/findings/$ID-$SLUG" --skip-build --dry-run
```

## Adding a new validator

1. Add the row to the registry table in `rfc-003-validator-roadmap.md` as
   `Planned`.
2. Add a fixture directory here with the `expected.yaml` you *want*. Because
   the registry row says `Planned`, the harness collects the detection test as
   a strict `xfail` and skips the repair tests, so the suite stays green.
3. Implement the check. The strict `xfail` turns into a failure the moment the
   finding starts being reported, which is the reminder to flip the registry
   row to `Implemented` and update `docs/VALIDATION_REFERENCE.md`. No edit to
   `expected.yaml` is needed — the mark is derived from the registry status.

`test_every_implemented_id_has_a_fixture` closes the loop from the other side:
an `Implemented` row with no fixture fails the suite unless its ID is listed in
`KNOWN_GAPS` in `tests/test_findings.py`, where each entry carries the reason
and points at the test that covers the check instead.

## `_baseline`

`_baseline/` is a healthy tree that must produce no findings and exit 0. It
guards against a new check that fires on every document and would otherwise
pass its own fixture.
