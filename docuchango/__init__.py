"""Docuchango - Docusaurus Validation and Repair Framework.

A comprehensive toolkit for Docusaurus documentation validation and repair.
Designed for opinionated micro-CMS documentation systems with human-agent collaboration.

This package provides:
- Documentation validation (frontmatter, links, formatting)
- Automated fixing of common documentation issues
- CLI tools for all operations

Example:
    >>> from docuchango.validator import DocValidator
    >>> validator = DocValidator(repo_root=".")
    >>> validator.scan_documents()
    >>> validator.check_code_blocks()
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("docuchango")
except PackageNotFoundError:
    # Package is not installed, use fallback version
    __version__ = "0.0.0.dev0"

__author__ = "Jacob Repp"
__email__ = "jacobrepp@gmail.com"

# Core validation exports
from docuchango.schemas import (
    ADRFrontmatter,
    GenericDocFrontmatter,
    MemoFrontmatter,
    PRDFrontmatter,
    RFCFrontmatter,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Schemas
    "ADRFrontmatter",
    "RFCFrontmatter",
    "MemoFrontmatter",
    "PRDFrontmatter",
    "GenericDocFrontmatter",
]
