# Docuchango

**Docusaurus validation and repair framework for opinionated micro-CMS documentation, designed for human-agent collaboration workflows.**

Docuchango is a comprehensive Python CLI toolkit that validates, tests, and repairs Docusaurus-based documentation systems. Built specifically for teams using documentation as a collaborative workspace between humans and AI agents, it ensures consistency, correctness, and quality in your documentation pipeline.

## Why Docuchango?

Modern documentation systems serve as more than just reference material—they're collaborative workspaces where humans and AI agents work together to create, maintain, and evolve knowledge. Docuchango provides the validation and repair infrastructure needed to maintain quality in these dynamic environments.

## Features

### 📋 Documentation Validation
- **Frontmatter Validation**: Validates YAML frontmatter using Pydantic schemas
- **Link Checking**: Verifies internal links, cross-references, and anchors
- **Markdown Formatting**: Checks for formatting issues and consistency
- **Code Block Validation**: Ensures proper code fence formatting and language tags
- **MDX Compatibility**: Validates MDX syntax for Docusaurus builds

### 🔧 Automated Fixing
Multiple fix modules for common documentation issues:
- Fix broken links and cross-references
- Correct code block formatting
- Add missing frontmatter fields
- Fix MDX syntax issues
- Normalize internal links
- And more...

### 🧪 Testing Framework
Comprehensive testing utilities for documentation workflows:
- CLI command execution and result handling
- gRPC client wrappers
- Docker Compose environment management
- Custom assertions for documentation testing
- Reusable test data factories
- Service health checks

## Installation

### From PyPI (when published)
```bash
pip install docuchango
# or with uv
uv pip install docuchango
```

### For Development
```bash
# Clone the repository
git clone <repository-url>
cd docuchango

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

Docuchango provides three main command entry points:

#### 1. Main CLI (`docuchango`)
```bash
# Show help
docuchango --help

# Validate documentation
docuchango validate --repo-root /path/to/repo

# Validate with verbose output
docuchango validate --verbose

# Skip Docusaurus build validation
docuchango validate --skip-build

# Fix all issues automatically
docuchango fix all --repo-root /path/to/repo

# Fix specific issue types
docuchango fix links
docuchango fix code-blocks

# Dry run (preview changes)
docuchango fix all --dry-run

# Check service health
docuchango test health --url http://localhost:8080
```

#### 2. Validate Shortcut (`dcc-validate`)
```bash
# Quick validation
dcc-validate --repo-root /path/to/repo --verbose
```

#### 3. Fix Shortcut (`dcc-fix`)
```bash
# Quick fix
dcc-fix all --repo-root /path/to/repo
```

### Python API

#### Validation
```python
from docuchango.validator import PrismDocValidator

# Create validator
validator = PrismDocValidator(repo_root=".", verbose=True)

# Scan and validate documents
validator.scan_documents()
validator.check_code_blocks()
validator.check_formatting()

# Check for errors
for doc in validator.documents:
    if doc.errors:
        print(f"Errors in {doc.file_path}:")
        for error in doc.errors:
            print(f"  - {error}")
```

#### Schema Validation
```python
from docuchango.schemas import ADRFrontmatter, RFCFrontmatter
import frontmatter

# Load and validate ADR frontmatter
post = frontmatter.load("docs/adr/ADR-001-example.md")
try:
    adr = ADRFrontmatter(**post.metadata)
    print(f"Valid ADR: {adr.title}")
except ValidationError as e:
    print(f"Invalid frontmatter: {e}")
```

#### Testing Framework
```python
from docuchango.testing import AGFCLIRunner, AGFAssertions, HealthChecker

# CLI testing
runner = AGFCLIRunner()
result = runner.run(["command", "arg1", "arg2"])
assert result.success
assert result.exit_code == 0

# Custom assertions
assertions = AGFAssertions()
assertions.assert_valid_json(result.stdout)
assertions.assert_contains(result.stdout, "expected text")

# Health checks
checker = HealthChecker(base_url="http://localhost:8080")
is_healthy = checker.check_health()
assert is_healthy
```

## Project Structure

```
docuchango/
├── pyproject.toml          # Project configuration (uv, ruff, dependencies)
├── README.md               # This file
├── LICENSE                 # MIT License
├── docuchango/             # Main package
│   ├── __init__.py         # Package exports
│   ├── __main__.py         # Module entry point
│   ├── cli.py              # Click-based CLI
│   ├── validator.py        # Document validation logic
│   ├── schemas.py          # Pydantic schemas for frontmatter
│   ├── fixes/              # Fix modules
│   │   ├── broken_links.py
│   │   ├── code_blocks.py
│   │   ├── docs.py
│   │   └── ...
│   └── testing/            # Testing framework
│       ├── __init__.py
│       ├── cli.py          # CLI runner
│       ├── assertions.py   # Custom assertions
│       ├── docker.py       # Docker utilities
│       ├── fixtures.py     # Test fixtures
│       └── health.py       # Health checks
└── tests/                  # Test suite
    ├── test_validator.py
    └── fixtures/
        ├── pass/           # Passing test fixtures
        └── fail/           # Failing test fixtures
```

## Development

### Setup Development Environment
```bash
# Install with development dependencies
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=docuchango --cov-report=html

# Run specific test file
pytest tests/test_validator.py

# Run with verbose output
pytest -v
```

### Code Quality

The project uses `ruff` for linting and formatting:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Building the Package

```bash
# Build with uv
uv build

# Or with pip
pip install build
python -m build
```

This will create distribution files in the `dist/` directory:
- `docuchango-0.1.0.tar.gz` (source distribution)
- `docuchango-0.1.0-py3-none-any.whl` (wheel distribution)

### Publishing to PyPI

```bash
# Install twine
pip install twine

# Check the distribution
twine check dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Documentation Schemas

The package includes Pydantic schemas for validating documentation frontmatter:

### ADR (Architecture Decision Record)
Required fields:
- `title`: Title without ADR prefix
- `status`: Proposed | Accepted | Implemented | Deprecated | Superseded
- `date`: Decision date (YYYY-MM-DD)
- `deciders`: Person or team who made the decision
- `tags`: List of lowercase, hyphenated tags
- `id`: Lowercase identifier (e.g., "adr-001")
- `project_id`: Project identifier
- `doc_uuid`: Unique UUID v4

### RFC (Request for Comments)
Required fields:
- `title`: Title without RFC prefix
- `status`: Draft | Proposed | Accepted | Implemented | Deprecated | Superseded
- `author`: Document author
- `created`: Creation date (YYYY-MM-DD)
- `updated`: Last modified date (YYYY-MM-DD)
- `tags`: List of lowercase, hyphenated tags
- `id`: Lowercase identifier (e.g., "rfc-015")
- `project_id`: Project identifier
- `doc_uuid`: Unique UUID v4

### Memo (Technical Memo)
Required fields:
- `title`: Title without MEMO prefix
- `author`: Document author
- `created`: Creation date (YYYY-MM-DD)
- `updated`: Last modified date (YYYY-MM-DD)
- `tags`: List of lowercase, hyphenated tags
- `id`: Lowercase identifier (e.g., "memo-010")
- `project_id`: Project identifier
- `doc_uuid`: Unique UUID v4

### Generic Documentation
Required fields:
- `title`: Document title
- `project_id`: Project identifier
- `doc_uuid`: Unique UUID v4

Optional fields:
- `description`: Brief description
- `sidebar_position`: Position in sidebar
- `tags`: List of tags
- `id`: Document identifier

## Human-Agent Collaboration

Docuchango is designed with human-agent collaboration in mind:

- **Automated Quality Gates**: Validation runs automatically, catching issues before they reach production
- **Repair Suggestions**: Fix modules provide automated remediation for common issues
- **Extensible Schemas**: Pydantic-based validation makes it easy to add custom rules
- **CI/CD Integration**: Easy to integrate into automated workflows
- **Testing Infrastructure**: Built-in testing utilities for documentation pipelines

## Dependencies

### Core Dependencies
- `python-frontmatter>=1.0.0` - YAML frontmatter parsing
- `pydantic>=2.0.0` - Data validation using Python type annotations
- `pyyaml>=6.0` - YAML parser
- `click>=8.0.0` - Command line interface creation
- `rich>=13.0.0` - Beautiful terminal output
- `grpcio>=1.60.0` - gRPC runtime
- `grpcio-tools>=1.60.0` - gRPC tools
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter
- `docker>=7.0.0` - Docker SDK

### Development Dependencies
- `pytest>=8.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage plugin
- `pytest-xdist>=3.5.0` - Parallel test execution
- `pytest-asyncio>=0.23.0` - Async test support
- `pytest-timeout>=2.2.0` - Test timeout support
- `ruff>=0.1.0` - Fast Python linter and formatter

## License

MIT License - See LICENSE file for details

## Author

Jacob Repp (jacobrepp@gmail.com)

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass: `pytest`
2. Code is formatted: `ruff format .`
3. No linting errors: `ruff check .`
4. Add tests for new features
5. Update documentation as needed

## Support

For issues, questions, or contributions, please visit the GitHub repository.

---

Built with ❤️ for teams that believe documentation is a collaborative art.
