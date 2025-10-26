# Docuchango

Docusaurus validation and repair framework for opinionated micro-CMS documentation, designed for human-agent collaboration workflows.

## Features

- **Validation**: Frontmatter (Pydantic schemas), links, formatting, code blocks, MDX compatibility
- **Automated Fixes**: Broken links, code blocks, frontmatter, MDX syntax
- **Testing Framework**: CLI runners, assertions, Docker utilities, health checks

## Installation

```bash
pip install docuchango
# or
uv pip install docuchango
```

## Usage

### CLI

```bash
# Validate
docuchango validate --repo-root /path/to/repo --verbose
dcc-validate --verbose

# Fix
docuchango fix all --repo-root /path/to/repo
dcc-fix links

# Test
docuchango test health --url http://localhost:8080
```

### Python API

```python
from docuchango.validator import PrismDocValidator
from docuchango.schemas import ADRFrontmatter, RFCFrontmatter

# Validate documents
validator = PrismDocValidator(repo_root=".", verbose=True)
validator.scan_documents()
validator.check_code_blocks()
validator.check_formatting()

# Use schemas
adr = ADRFrontmatter(**frontmatter_data)
```

## Documentation Schemas

### ADR (Architecture Decision Record)
Required: `title`, `status`, `date`, `deciders`, `tags`, `id`, `project_id`, `doc_uuid`

### RFC (Request for Comments)
Required: `title`, `status`, `author`, `created`, `updated`, `tags`, `id`, `project_id`, `doc_uuid`

### Memo
Required: `title`, `author`, `created`, `updated`, `tags`, `id`, `project_id`, `doc_uuid`

### Generic Documentation
Required: `title`, `project_id`, `doc_uuid`
Optional: `description`, `sidebar_position`, `tags`, `id`

## Development

```bash
# Setup
uv sync
pip install -e ".[dev]"

# Test
pytest
pytest --cov=docuchango

# Quality
ruff format .
ruff check .

# Build
uv build
```

## Project Structure

```
docuchango/
├── docuchango/        # Main package
│   ├── cli.py         # Click CLI
│   ├── validator.py   # Validation logic
│   ├── schemas.py     # Pydantic schemas
│   ├── fixes/         # Fix modules (11)
│   └── testing/       # Test framework (5)
└── tests/             # Test suite with fixtures
```

## Dependencies

**Core**: python-frontmatter, pydantic, pyyaml, click, rich, grpcio, psycopg2-binary, docker

**Dev**: pytest, pytest-cov, pytest-xdist, pytest-asyncio, pytest-timeout, ruff

## License

MIT License - See LICENSE file

## Author

Jacob Repp (jacobrepp@gmail.com)

## Repository

https://github.com/jrepp/docuchango
