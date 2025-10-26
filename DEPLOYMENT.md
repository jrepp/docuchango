# Deployment Guide for docuchango

This guide covers how to publish the `docuchango` package to PyPI and TestPyPI.

## Prerequisites

1. Python 3.9+ installed
2. `uv` installed (recommended) or `pip` with `build` and `twine`
3. PyPI and/or TestPyPI account
4. API tokens for PyPI/TestPyPI

## Setup PyPI Credentials

### Option 1: Using API Tokens (Recommended)

1. Create a PyPI account at https://pypi.org/account/register/
2. Go to Account Settings → API tokens
3. Create a new API token with scope for this project
4. Save the token securely

Create or update `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
repository = https://test.pypi.org/legacy/
```

### Option 2: Environment Variables

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE
```

## Pre-Deployment Checklist

Before publishing, ensure:

- [ ] All tests pass: `pytest`
- [ ] Code is formatted: `ruff format .`
- [ ] No linting errors: `ruff check .`
- [ ] Version number is updated in `pyproject.toml`
- [ ] CHANGELOG is updated (if you create one)
- [ ] README is up to date
- [ ] All dependencies are correctly specified
- [ ] Package builds successfully: `uv build`
- [ ] Test installation works in a clean environment

## Building the Package

### Using uv (Recommended)

```bash
# Clean previous builds
rm -rf dist/

# Build the package
uv build
```

This creates two distribution files in `dist/`:
- `docuchango-X.Y.Z.tar.gz` (source distribution)
- `docuchango-X.Y.Z-py3-none-any.whl` (wheel distribution)

### Using pip and build

```bash
# Install build tools
pip install build twine

# Build the package
python -m build
```

## Publishing to TestPyPI (Recommended First Step)

TestPyPI is a separate instance of PyPI for testing. Always test here first!

```bash
# Install twine if not already installed
pip install twine

# Check the distribution files
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

### Test Installation from TestPyPI

```bash
# Create a test environment
uv venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    docuchango

# Test the installation
docuchango --help
python -c "import docuchango; print(docuchango.__version__)"

# Clean up
deactivate
rm -rf test-env
```

Note: We use `--extra-index-url` because TestPyPI might not have all dependencies.

## Publishing to PyPI

Once you've verified everything works on TestPyPI:

```bash
# Upload to PyPI
twine upload dist/*
```

### Post-Deployment Verification

```bash
# Wait a few minutes for PyPI to process

# Install from PyPI
pip install docuchango

# Verify installation
docuchango --version
docuchango --help
```

## Version Management

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0 → 2.0.0): Incompatible API changes
- **MINOR** version (1.0.0 → 1.1.0): New functionality, backwards compatible
- **PATCH** version (1.0.0 → 1.0.1): Bug fixes, backwards compatible

### Updating Version

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. Update version in `docuchango/__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```

3. Commit the version bump:
   ```bash
   git add pyproject.toml docuchango/__init__.py
   git commit -m "Bump version to 0.2.0"
   git tag -a v0.2.0 -m "Version 0.2.0"
   git push && git push --tags
   ```

## Automation with GitHub Actions

You can automate releases using GitHub Actions. Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          pip install twine
          twine upload dist/*
```

Add your PyPI token as a GitHub secret named `PYPI_API_TOKEN`.

## Troubleshooting

### Package Already Exists

If you get an error that the package already exists:
- You cannot re-upload the same version
- Increment the version number in `pyproject.toml`
- Rebuild and upload again

### Missing Dependencies

If dependencies are missing on TestPyPI:
- This is normal - TestPyPI has limited packages
- Use both `--index-url` and `--extra-index-url` when installing
- Dependencies will work fine on regular PyPI

### Authentication Errors

If you get authentication errors:
- Verify your API token is correct
- Make sure you're using `__token__` as the username
- Check that `~/.pypirc` is properly formatted
- Try using environment variables instead

### Build Errors

If the build fails:
- Run `ruff check .` to find linting issues
- Run `pytest` to ensure tests pass
- Check that all required files are included in `pyproject.toml`

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning**
3. **Tag releases in git**
4. **Keep README and documentation up to date**
5. **Run all tests before publishing**
6. **Never commit API tokens to git**
7. **Use API tokens instead of passwords**
8. **Document breaking changes clearly**
9. **Consider using GitHub Actions for automation**
10. **Verify installation from PyPI after publishing**

## Additional Resources

- [PyPI Official Documentation](https://pypi.org/help/)
- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [Semantic Versioning](https://semver.org/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Twine Documentation](https://twine.readthedocs.io/)

## Support

For issues or questions about deployment:
- Check the GitHub Issues
- Review PyPI documentation
- Contact the maintainer: jacobrepp@gmail.com
