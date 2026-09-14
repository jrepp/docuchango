# Publishing docuchango to PyPI

Releases are fully automated. You do not bump versions, tag, or run `uv build`
by hand. You write [Conventional Commits](https://www.conventionalcommits.org/)
and push to a release branch.

## Overview

| Branch | Channel | Example tag | PyPI version | GitHub release |
|--------|---------|-------------|--------------|----------------|
| `main` | stable  | `v1.19.0`   | `1.19.0`     | latest         |
| `next` | release candidate | `v1.19.0-rc.1` | `1.19.0rc1` | pre-release |

On every push to either branch, `.github/workflows/release.yml`:

1. Runs `python-semantic-release`, which reads the conventional commits since
   the last release, bumps `project.version` in `pyproject.toml`, updates
   `CHANGELOG.md`, commits `chore(release): X.Y.Z`, and tags.
2. Creates the GitHub release from the changelog section
   (`--latest` on `main`, `--prerelease` on `next`).
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

## Stable releases (`main`)

Merge a PR to `main`. That is the whole process. Watch the
[Release workflow](https://github.com/jrepp/docuchango/actions/workflows/release.yml)
and verify:

```bash
uv tool run --from docuchango docuchango --version
gh release view v1.19.0 --json assets --jq '.assets[].name'
```

## Release candidates (`next`)

Use the `next` branch to ship a pre-release that downstream projects can test
before it becomes a stable release.

### Why real PyPI and not TestPyPI

Release candidates go to **PyPI itself**. PEP 440 resolvers (pip, uv, poetry)
ignore pre-releases unless a consumer explicitly opts in, so `1.19.0rc1` is
invisible to every existing `docuchango>=X` pin and to unpinned `uvx --from
docuchango` invocations. Consumers get a real installable wheel from the real
index with real dependency resolution. TestPyPI needs `--extra-index-url`
tricks and cannot be expressed cleanly in a `uv.lock`.

### Cutting an rc

```bash
# Start (or refresh) next from main
git checkout main && git pull
git checkout -B next main
# Merge or cherry-pick the work you want to test
git merge --no-ff feature/my-change
git push origin next
```

Every push to `next` that contains a `feat:`/`fix:` since the last stable
release produces the next rc: `v1.19.0-rc.1`, `v1.19.0-rc.2`, and so on.

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

### Promoting an rc to stable

Merge `next` into `main` (a PR is fine). Semantic-release on `main` computes
the stable version from the same commits (`1.19.0`), ignoring the rc tags and
the `chore(release)` commits. Then fast-forward `next` so it does not drift:

```bash
git checkout next && git merge --ff-only main && git push origin next
```

If `next` has diverged and cannot fast-forward, reset it: `git checkout -B next
main && git push --force-with-lease origin next`. Nothing on `next` is
precious; it is a staging branch.

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

- `pypi`: used by `release.yml` on `main` and `next`, and by `publish.yml`
  manual dispatch. Do **not** restrict deployment branches to `main` only, or
  `next` releases will fail to publish. Restricting to `main` and `next` is
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

**`branch 'x' isn't in any release groups`.** Only `main` and `next` are
configured in `[tool.semantic_release.branches.*]`. Do not point the release
workflow at other branches.

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

For an rc, the identity ends in `@refs/heads/next`.

## References

- [python-semantic-release](https://python-semantic-release.readthedocs.io/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [Sigstore Python](https://github.com/sigstore/sigstore-python)
- [PyApp](https://ofek.dev/pyapp/)
