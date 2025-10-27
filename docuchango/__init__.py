"""Docuchango - Docusaurus Validation and Repair Framework.

A comprehensive toolkit for Docusaurus documentation validation, testing, and repair.
Designed for opinionated micro-CMS documentation systems with human-agent collaboration.

This package provides:
- Documentation validation (frontmatter, links, formatting)
- Automated fixing of common documentation issues
- Testing utilities for documentation workflows
- CLI tools for all operations

Example:
    >>> from docuchango.validator import DocValidator
    >>> validator = DocValidator(repo_root=".")
    >>> validator.scan_documents()
    >>> validator.check_code_blocks()
"""

__version__ = "0.1.2"
__author__ = "Jacob Repp"
__email__ = "jacobrepp@gmail.com"

# Core validation exports
from docuchango.schemas import (
    ADRFrontmatter,
    GenericDocFrontmatter,
    MemoFrontmatter,
    RFCFrontmatter,
)

# Testing framework exports
from docuchango.testing import AGFAssertions, AGFCLIRunner, CLIResult, HealthChecker

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Schemas
    "ADRFrontmatter",
    "RFCFrontmatter",
    "MemoFrontmatter",
    "GenericDocFrontmatter",
    # Testing
    "AGFCLIRunner",
    "CLIResult",
    "AGFAssertions",
    "HealthChecker",
]
