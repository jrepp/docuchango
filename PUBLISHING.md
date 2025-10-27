# Publishing docuchango to PyPI

This document describes how to publish docuchango to PyPI.

## Overview

The publishing workflow uses:
- **Trusted Publishing**: PyPI's OIDC-based authentication (no API tokens needed)
- **GitHub Actions**: Automated building and publishing
- **GitHub Releases**: Trigger mechanism for PyPI publishing
- **uv**: Fast package building
- **Sigstore**: Package signing for security

## Setup (One-time)

### 1. Configure PyPI Trusted Publishing

Before the first release, configure PyPI to trust this GitHub repository:

**For PyPI (production):**

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher with these settings:
   - **PyPI Project Name**: `docuchango`
   - **Owner**: `jrepp` (GitHub username/org)
   - **Repository name**: `docuchango`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

**For TestPyPI (testing):**

1. Go to https://test.pypi.org/manage/account/publishing/
2. Add a new publisher with the same settings but use environment name: `testpypi`

### 2. Configure GitHub Environments

Create GitHub environments to control publishing access:

1. Go to repository Settings → Environments
2. Create environment `pypi`:
   - Add protection rules (optional but recommended):
     - Required reviewers
     - Wait timer
     - Deployment branches: only `main`
3. Create environment `testpypi`:
   - Less restrictive for testing

## Publishing Process

### Method 1: Automatic Publishing via GitHub Release (Recommended)

This is the standard way to publish a new version:

1. **Update version in pyproject.toml**:
   ```bash
   # Edit pyproject.toml and bump version
   vim pyproject.toml
   # Change: version = "0.1.0" to version = "0.2.0"
   ```

2. **Commit and push**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push origin main
   ```

3. **Create a GitHub Release**:
   ```bash
   # Using GitHub CLI
   gh release create v0.2.0 \
     --title "Release v0.2.0" \
     --notes "Release notes here..."

   # Or use the GitHub web UI:
   # https://github.com/jrepp/docuchango/releases/new
   ```

4. **Workflow automatically**:
   - Builds the package
   - Publishes to PyPI
   - Signs packages with Sigstore
   - Uploads artifacts to GitHub Release

### Method 2: Manual Dispatch to TestPyPI

For testing before a real release:

1. **Go to Actions tab**: https://github.com/jrepp/docuchango/actions/workflows/publish.yml

2. **Click "Run workflow"**:
   - Branch: `main` (or your test branch)
   - Environment: `testpypi`

3. **Verify on TestPyPI**: https://test.pypi.org/project/docuchango/

4. **Test installation**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ docuchango
   ```

### Method 3: Manual Local Build (Development)

For local testing without publishing:

```bash
# Build package
uv build

# Check the build
uv tool run twine check dist/*

# View contents
tar tzf dist/docuchango-*.tar.gz
unzip -l dist/docuchango-*.whl
```

## Version Management

We use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version Workflow

1. **Plan the version**: Decide if it's major, minor, or patch
2. **Update pyproject.toml**: Manually set the version
3. **Update CHANGELOG**: Document changes (if you maintain one)
4. **Create release**: Follow Method 1 above

Example version progression:
- `0.1.0` → `0.1.1` (bug fix)
- `0.1.1` → `0.2.0` (new feature)
- `0.2.0` → `1.0.0` (stable release, breaking changes)

## Workflow Details

### Triggers

The publish workflow runs on:

1. **GitHub Release published**: Automatically publishes to PyPI
2. **Manual workflow dispatch**: Allows testing with TestPyPI or manual PyPI publish

### Jobs

#### 1. Build Job
- Installs uv
- Builds source distribution (.tar.gz) and wheel (.whl)
- Validates package metadata with twine
- Uploads artifacts for publishing jobs

#### 2. Publish to PyPI Job
- Runs when: GitHub Release is published or manual dispatch to `pypi`
- Uses trusted publishing (OIDC)
- Publishes to https://pypi.org

#### 3. Publish to TestPyPI Job
- Runs when: Manual dispatch to `testpypi`
- Uses trusted publishing (OIDC)
- Publishes to https://test.pypi.org

#### 4. GitHub Release Job
- Runs when: GitHub Release is published (after PyPI publish)
- Signs packages with Sigstore
- Uploads packages and signatures to GitHub Release assets

## Troubleshooting

### "Project not found" on PyPI

**Problem**: First time publishing, PyPI doesn't know about the project yet.

**Solution**:
- You cannot use trusted publishing for the first release
- For first release only, use API token:
  1. Create API token on PyPI
  2. Add as GitHub secret: `PYPI_API_TOKEN`
  3. Temporarily modify workflow to use token
  4. After first successful publish, switch to trusted publishing

### "Environment not found"

**Problem**: GitHub environment not configured.

**Solution**: Create the environment in repository Settings → Environments

### Build failures

**Problem**: Package build fails.

**Solution**: Test locally first:
```bash
uv build
uv tool run twine check dist/*
```

### Version already exists

**Problem**: Trying to publish a version that already exists on PyPI.

**Solution**: Bump the version in pyproject.toml to a new unique version.

## Security

### Trusted Publishing

This workflow uses PyPI's Trusted Publishing (OIDC):
- No API tokens needed
- More secure than long-lived tokens
- Token is generated on-demand by GitHub
- Limited to specific workflow and environment

### Sigstore

Packages are signed with Sigstore:
- Provides cryptographic proof of origin
- Verifiable with `cosign`
- Signatures stored with GitHub Release

### Verifying Published Packages

```bash
# Download and verify signature
gh release download v0.2.0
cosign verify-blob \
  --certificate docuchango-0.2.0.tar.gz.crt \
  --signature docuchango-0.2.0.tar.gz.sig \
  --certificate-identity-regexp="https://github.com/jrepp/docuchango/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  docuchango-0.2.0.tar.gz
```

## References

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions: pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [Sigstore Python](https://github.com/sigstore/sigstore-python)
- [uv documentation](https://docs.astral.sh/uv/)

## Quick Reference

```bash
# Create release and publish to PyPI
gh release create v0.2.0 --title "Release v0.2.0" --notes "..."

# Test on TestPyPI (manual dispatch via GitHub UI)
# https://github.com/jrepp/docuchango/actions/workflows/publish.yml

# Install from PyPI
pip install docuchango

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ docuchango

# Build locally
uv build

# Check build
uv tool run twine check dist/*
```
