# Publishing docuchango to PyPI

Releases are automated. You do not bump versions, tag, or run `uv build` by
hand. You write [Conventional Commits](https://www.conventionalcommits.org/),
merge to `main`, and press one button when you want a stable release.

## Overview

| Trigger | Channel | Example tag | PyPI version | GitHub release |
|---------|---------|-------------|--------------|----------------|
| push to `main` | release candidate | `v1.19.0-rc.1` | `1.19.0rc1` | pre-release |
| Actions → Release → Run workflow | stable | `v1.19.0` | `1.19.0` | latest |

There is one branch. Every merge to `main` that contains a releasable commit
publishes a release candidate. A stable release is a deliberate manual step
that re-releases the current rc series under the clean version number.

On every run, `.github/workflows/release.yml`:

1. Runs `python-semantic-release`, which reads the conventional commits since
   the last release, bumps `project.version` in `pyproject.toml`, updates
   `CHANGELOG.md`, commits `chore(release): X.Y.Z`, and tags.
2. Creates the GitHub release. The notes are the changelog section for the
   version, followed by GitHub's generated "What's Changed" list of merged PRs.
   For a stable release the notes roll up every rc section since the previous
   stable release.
3. Builds the sdist and wheel with `uv build`, checks them with `twine`, and
   publishes to PyPI with **trusted publishing** (OIDC, no tokens).
4. Builds PyApp binaries for Linux, macOS (arm64) and Windows.
5. Signs the sdist and wheel with **Sigstore** and attaches the distributions,
   signature bundles, and binaries to the GitHub release.

If no commit since the last release warrants a bump (only `docs:`, `chore:`,
`ci:` etc.), the workflow exits without releasing.

Version bumps follow `pyproject.toml` `[tool.semantic_release]`:

- `feat:` → minor
- `fix:`, `perf:` → patch
- `BREAKING CHANGE:` footer or `!` → major

## Release candidates (every merge to `main`)

Merge a PR to `main`. If it contains a `feat:`, `fix:` or `perf:` commit, the
[Release workflow](https://github.com/jrepp/docuchango/actions/workflows/release.yml)
publishes the next rc: `v1.19.0-rc.1`, `v1.19.0-rc.2`, and so on. After a
stable release the series restarts from the new base, so a `fix:` after
`v1.19.0` produces `v1.19.1-rc.1`.

### Landing a PR without publishing anything

Use a non-releasing commit type: `docs`, `chore`, `ci`, `refactor`, `test`,
`build`, `style`. Semantic-release ignores them and no version is cut. The
changes still ship with the next rc that a `feat:` or `fix:` triggers.

### Why real PyPI and not TestPyPI

Release candidates go to **PyPI itself**. PEP 440 resolvers (pip, uv, poetry)
ignore pre-releases unless a consumer explicitly opts in, so `1.19.0rc1` is
invisible to every existing `docuchango>=X` pin and to unpinned `uvx --from
docuchango` invocations. Consumers get a real installable wheel from the real
index with real dependency resolution. TestPyPI needs `--extra-index-url`
tricks and cannot be expressed cleanly in a `uv.lock`.

### Testing an rc downstream

Consumers opt in with an explicit pre-release pin or a resolver flag:

```bash
# One-off CLI run
uvx --from "docuchango==1.19.0rc1" docuchango validate

# uv project (does not touch uv.lock unless you sync)
uv run --with "docuchango>=1.19.0rc1" docuchango validate

# Allow pre-releases when resolving a project
uv sync --prerelease=allow

# pip
pip install --pre "docuchango>=1.19.0rc1"
```

Put this in a non-blocking CI job in the downstream repo so it reports without
gating merges.

## Stable releases (promote)

When the current rc is good:

1. Open [Actions → Release](https://github.com/jrepp/docuchango/actions/workflows/release.yml).
2. **Run workflow**, branch `main`, leave **Promote to stable** ticked, run.

Or from the CLI:

```bash
gh workflow run release.yml --ref main -f promote=true
gh run watch
```

The same commits are released as `v1.19.0`, marked **latest** on GitHub, and
published to PyPI as `1.19.0`. Running promote when nothing new has landed
since the last stable release is a no-op.

Verify:

```bash
uv tool run --from docuchango docuchango --version
gh release view v1.19.0 --json assets --jq '.assets[].name'
```

### How promote works

Semantic-release chooses the channel by the name of the branch it runs on.
`pyproject.toml` maps `main` to the rc channel and a branch named `stable` to
the full-release channel. The promote run checks out `main`'s HEAD under the
local name `stable`, runs semantic-release there, and pushes the resulting
release commit and tag back to `main`. No `stable` branch exists on the
remote.

## One-time setup

### PyPI trusted publisher

Configured at https://pypi.org/manage/project/docuchango/settings/publishing/:

- **Owner**: `jrepp`
- **Repository**: `docuchango`
- **Workflow name**: `release.yml`
- **Environment**: `pypi`

For manual re-publishing (see below) to work, `publish.yml` with environment
`pypi` must also be registered as a publisher. Add it if it is not listed.
TestPyPI has its publisher registered with workflow `publish.yml` and
environment `testpypi`.

### GitHub environments

Settings → Environments:

- `pypi`: used by `release.yml` on `main` (push and manual dispatch) and by
  `publish.yml` manual dispatch. Restricting deployment branches to `main` is
  fine.
- `testpypi`: unrestricted, used only by manual dispatch.

## Manual publishing (`publish.yml`)

`.github/workflows/publish.yml` is a manual-dispatch workflow for two cases:

1. **Smoke-test packaging on TestPyPI** from any branch. Actions → "Publish to
   PyPI (manual)" → Run workflow → environment `testpypi`. Then:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ docuchango
   ```
2. **Re-publish a tag to PyPI** if the automated publish step failed after the
   tag was pushed. Run the workflow against the tag with environment `pypi`.

It cannot be triggered by GitHub releases: releases are created by
`release.yml` using `GITHUB_TOKEN`, and events produced by `GITHUB_TOKEN` never
trigger other workflows.

## Local build check

```bash
uv build
uv tool run twine check dist/*
unzip -l dist/docuchango-*.whl   # docs/, templates/, examples/ must be present
```

## Troubleshooting

**Workflow ran but nothing was released.** No commit since the last tag had a
`feat`/`fix`/`perf`/breaking type. Check `git log $(git describe --tags
--abbrev=0)..HEAD --oneline`.

**`No release will be made, X.Y.Z has already been released!` but there is no
such release.** A tag for that version exists on a commit that is not on
`main`. This happened in May 2026 when two merges landed seconds apart: the
first run's tag was pushed but its branch push was rejected, and every run
afterwards refused to release. Find it with
`git ls-remote --tags origin | grep vX.Y.Z`, confirm nothing was published
(`gh release view vX.Y.Z`, PyPI), and delete the tag:
`git push origin --delete refs/tags/vX.Y.Z`. The release push is now
`--atomic`, so a rejected push no longer leaves a tag behind.

**`branch 'x' isn't in any release groups`.** Only `main` (rc) and the local
promote name `stable` are configured in `[tool.semantic_release.branches.*]`.
Do not point the release workflow at other branches.

**`InvalidDistribution: '2.5' is not a valid metadata version`.** The
`pypa/gh-action-pypi-publish` version in use bundles a `twine` older than
7.0.0, which cannot upload wheels built by current `hatchling`. Bump the
action; PyPI itself accepts metadata 2.5.

**Trusted publishing rejected.** The publisher on PyPI must name the workflow
file that ran (`release.yml` or `publish.yml`) and the environment (`pypi`).
Check the "Publish to PyPI" step log for the claims PyPI saw.

**Release exists but has no assets.** The `build-pyapp-binaries` or
`release-assets` job failed after the PyPI publish. Re-run the failed jobs
from the Actions UI; the asset upload uses `--clobber` and is idempotent.

**Version already exists on PyPI.** A tag was pushed but the workflow was
re-run. Nothing to do; PyPI is immutable. The next release gets a new version.

## Verifying signatures

```bash
gh release download v1.19.0 --pattern 'docuchango-1.19.0*'
uv tool run sigstore verify github \
  --cert-identity "https://github.com/jrepp/docuchango/.github/workflows/release.yml@refs/heads/main" \
  --bundle docuchango-1.19.0-py3-none-any.whl.sigstore.json \
  docuchango-1.19.0-py3-none-any.whl
```

Both rc and stable releases run on `main`, so the identity is the same for
either.

## References

- [python-semantic-release](https://python-semantic-release.readthedocs.io/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [Sigstore Python](https://github.com/sigstore/sigstore-python)
- [PyApp](https://ofek.dev/pyapp/)
