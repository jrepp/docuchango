#!/usr/bin/env python3
"""Pydantic schemas for Prism documentation frontmatter validation.

These schemas enforce consistent metadata across ADRs, RFCs, and Memos.
"""

import datetime
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ADRFrontmatter(BaseModel):
    """Schema for Architecture Decision Record frontmatter.

    REQUIRED FIELDS (all must be present):
    - title: Title without ADR prefix (e.g., "Use Rust for Proxy"). ID displayed by sidebar.
    - status: Current state (Proposed/Accepted/Implemented/Deprecated/Superseded)
    - date: Decision date in ISO 8601 format (YYYY-MM-DD)
    - deciders: Person or team who made the decision (e.g., "Core Team", "Platform Team")
    - tags: List of lowercase hyphenated tags for categorization
    - id: Lowercase identifier matching filename (e.g., "adr-001" for ADR-001-rust-proxy.md)
    - project_id: Project identifier from docs-project.yaml (e.g., "prism-data-layer")
    - doc_uuid: Unique identifier for backend tracking (UUID v4 format)
    """

    title: str = Field(
        ...,
        min_length=10,
        description="ADR title without prefix (e.g., 'Use Rust for Proxy'). The ID prefix is in the 'id' field and displayed by sidebar.",
    )
    status: Literal["Proposed", "Accepted", "Implemented", "Deprecated", "Superseded"] = Field(
        ...,
        description="Decision status. Use 'Proposed' for drafts, 'Accepted' for approved, 'Implemented' for completed",
    )
    date: datetime.date = Field(
        ...,
        description="Date of decision in ISO 8601 format (YYYY-MM-DD). Use date decision was made, not file creation date",
    )
    deciders: str = Field(
        ..., description="Who made the decision. Use team name (e.g., 'Core Team') or individual name"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="List of lowercase, hyphenated tags (e.g., ['architecture', 'backend', 'security'])",
    )
    id: str = Field(
        ...,
        description="Lowercase ID matching filename format: 'adr-XXX' where XXX is 3-digit number (e.g., 'adr-001')",
    )
    project_id: str = Field(
        ...,
        description="Project identifier from docs-project.yaml. Must match configured project ID (e.g., 'prism-data-layer')",
    )
    doc_uuid: str = Field(
        ...,
        description="Unique identifier for backend tracking. Must be valid UUID v4 format. Generated automatically by migration script",
    )

    # Title validator removed - titles should NOT include prefix (e.g., "ADR-001:")
    # The ID prefix is in the 'id' field and displayed by the sidebar presentation layer

    @field_validator("tags")
    @classmethod
    def validate_tags_format(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase and hyphenated"""
        for tag in v:
            if not re.match(r"^[a-z0-9\-]+$", tag):
                raise ValueError(
                    f"Invalid tag '{tag}' - tags must be lowercase with hyphens only (e.g., 'data-access', 'backend')"
                )
        return v

    @field_validator("deciders")
    @classmethod
    def validate_deciders(cls, v: str) -> str:
        """Ensure deciders is not empty"""
        if not v.strip():
            raise ValueError("'deciders' field cannot be empty")
        return v

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Ensure ID is lowercase adr-XXX format"""
        if not re.match(r"^adr-\d{3}$", v):
            raise ValueError(f"ADR id must be lowercase 'adr-XXX' format (e.g., 'adr-001'). Got: {v}")
        return v

    @field_validator("doc_uuid")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Ensure doc_uuid is a valid UUID v4"""
        if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", v):
            raise ValueError(f"doc_uuid must be a valid UUID v4 format. Got: {v}")
        return v


class RFCFrontmatter(BaseModel):
    """Schema for Request for Comments frontmatter.

    REQUIRED FIELDS (all must be present):
    - title: Title without RFC prefix (e.g., "Plugin Architecture"). ID displayed by sidebar.
    - status: Current state (Draft/Proposed/Accepted/Implemented/Rejected)
    - author: Document author (person or team who wrote the RFC)
    - created: Date RFC was first created in ISO 8601 format (YYYY-MM-DD)
    - updated: Date RFC was last modified in ISO 8601 format (YYYY-MM-DD)
    - tags: List of lowercase hyphenated tags for categorization
    - id: Lowercase identifier matching filename (e.g., "rfc-015" for RFC-015-plugin-architecture.md)
    - project_id: Project identifier from docs-project.yaml (e.g., "prism-data-layer")
    - doc_uuid: Unique identifier for backend tracking (UUID v4 format)
    """

    title: str = Field(
        ...,
        min_length=10,
        description="RFC title without prefix (e.g., 'Plugin Architecture'). The ID prefix is in the 'id' field and displayed by sidebar.",
    )
    status: Literal["Draft", "Proposed", "Accepted", "Implemented", "Deprecated", "Superseded"] = Field(
        ..., description="RFC status. Use 'Draft' for work-in-progress, 'Proposed' for review, 'Accepted' for approved"
    )
    author: str = Field(
        ..., description="RFC author. Use person name or team name (e.g., 'Platform Team', 'John Smith')"
    )
    created: datetime.date = Field(
        ...,
        description="Date RFC was first created in ISO 8601 format (YYYY-MM-DD). Do not change after initial creation",
    )
    updated: Optional[datetime.date] = Field(
        None, description="Date RFC was last modified in ISO 8601 format (YYYY-MM-DD). Update whenever content changes"
    )
    tags: list[str] = Field(
        default_factory=list, description="List of lowercase, hyphenated tags (e.g., ['design', 'api', 'backend'])"
    )
    id: str = Field(
        ...,
        description="Lowercase ID matching filename format: 'rfc-XXX' where XXX is 3-digit number (e.g., 'rfc-015')",
    )
    project_id: str = Field(
        ...,
        description="Project identifier from docs-project.yaml. Must match configured project ID (e.g., 'prism-data-layer')",
    )
    doc_uuid: str = Field(
        ...,
        description="Unique identifier for backend tracking. Must be valid UUID v4 format. Generated automatically by migration script",
    )

    # Title validator removed - titles should NOT include prefix (e.g., "RFC-001:")
    # The ID prefix is in the 'id' field and displayed by the sidebar presentation layer

    @field_validator("tags")
    @classmethod
    def validate_tags_format(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase and hyphenated"""
        for tag in v:
            if not re.match(r"^[a-z0-9\-]+$", tag):
                raise ValueError(
                    f"Invalid tag '{tag}' - tags must be lowercase with hyphens only (e.g., 'api-design', 'patterns')"
                )
        return v

    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str) -> str:
        """Ensure author is not empty"""
        if not v.strip():
            raise ValueError("'author' field cannot be empty")
        return v

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Ensure ID is lowercase rfc-XXX format"""
        if not re.match(r"^rfc-\d{3}$", v):
            raise ValueError(f"RFC id must be lowercase 'rfc-XXX' format (e.g., 'rfc-001'). Got: {v}")
        return v

    @field_validator("doc_uuid")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Ensure doc_uuid is a valid UUID v4"""
        if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", v):
            raise ValueError(f"doc_uuid must be a valid UUID v4 format. Got: {v}")
        return v


class MemoFrontmatter(BaseModel):
    """Schema for technical memo frontmatter.

    REQUIRED FIELDS (all must be present):
    - title: Title without MEMO prefix (e.g., "Load Test Results"). ID displayed by sidebar.
    - author: Document author (person or team who wrote the memo)
    - created: Date memo was first created in ISO 8601 format (YYYY-MM-DD)
    - updated: Date memo was last modified in ISO 8601 format (YYYY-MM-DD)
    - tags: List of lowercase hyphenated tags for categorization
    - id: Lowercase identifier matching filename (e.g., "memo-010" for MEMO-010-loadtest-results.md)
    - project_id: Project identifier from docs-project.yaml (e.g., "prism-data-layer")
    - doc_uuid: Unique identifier for backend tracking (UUID v4 format)
    """

    title: str = Field(
        ...,
        min_length=10,
        description="Memo title without prefix (e.g., 'Load Test Results'). The ID prefix is in the 'id' field and displayed by sidebar.",
    )
    author: str = Field(..., description="Memo author. Use person name or team name (e.g., 'Platform Team', 'Claude')")
    created: datetime.date = Field(
        ...,
        description="Date memo was first created in ISO 8601 format (YYYY-MM-DD). Do not change after initial creation",
    )
    updated: datetime.date = Field(
        ..., description="Date memo was last modified in ISO 8601 format (YYYY-MM-DD). Update whenever content changes"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="List of lowercase, hyphenated tags (e.g., ['implementation', 'testing', 'performance'])",
    )
    id: str = Field(
        ...,
        description="Lowercase ID matching filename format: 'memo-XXX' where XXX is 3-digit number (e.g., 'memo-010')",
    )
    project_id: str = Field(
        ...,
        description="Project identifier from docs-project.yaml. Must match configured project ID (e.g., 'prism-data-layer')",
    )
    doc_uuid: str = Field(
        ...,
        description="Unique identifier for backend tracking. Must be valid UUID v4 format. Generated automatically by migration script",
    )

    # Title validator removed - titles should NOT include prefix (e.g., "MEMO-001:")
    # The ID prefix is in the 'id' field and displayed by the sidebar presentation layer

    @field_validator("tags")
    @classmethod
    def validate_tags_format(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase and hyphenated"""
        for tag in v:
            if not re.match(r"^[a-z0-9\-]+$", tag):
                raise ValueError(
                    f"Invalid tag '{tag}' - tags must be lowercase with hyphens only (e.g., 'architecture', 'design')"
                )
        return v

    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str) -> str:
        """Ensure author is not empty"""
        if not v.strip():
            raise ValueError("'author' field cannot be empty")
        return v

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Ensure ID is lowercase memo-XXX format"""
        if not re.match(r"^memo-\d{3}$", v):
            raise ValueError(f"Memo id must be lowercase 'memo-XXX' format (e.g., 'memo-001'). Got: {v}")
        return v

    @field_validator("doc_uuid")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Ensure doc_uuid is a valid UUID v4"""
        if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", v):
            raise ValueError(f"doc_uuid must be a valid UUID v4 format. Got: {v}")
        return v


class GenericDocFrontmatter(BaseModel):
    """Schema for generic documentation frontmatter (guides, tutorials, reference docs).

    REQUIRED FIELDS:
    - title: Document title (descriptive, no prefix required)
    - project_id: Project identifier from docs-project.yaml (e.g., "prism-data-layer")
    - doc_uuid: Unique identifier for backend tracking (UUID v4 format)

    OPTIONAL FIELDS:
    - description: Brief description of the document
    - sidebar_position: Position in Docusaurus sidebar (integer)
    - tags: List of lowercase hyphenated tags for categorization
    - id: Document identifier (if applicable, lowercase with hyphens)
    """

    title: str = Field(
        ...,
        min_length=3,
        description="Document title. Should be descriptive and clear (e.g., 'Getting Started Guide', 'API Reference')",
    )
    description: Optional[str] = Field(
        None, description="Brief description of the document content. Optional but recommended"
    )
    sidebar_position: Optional[int] = Field(
        None, description="Position in Docusaurus sidebar (lower numbers appear first). Optional"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="List of lowercase, hyphenated tags (e.g., ['guide', 'tutorial', 'reference'])",
    )
    id: Optional[str] = Field(
        None,
        description="Document identifier (optional). Use lowercase with hyphens if provided (e.g., 'getting-started')",
    )
    project_id: str = Field(
        ...,
        description="Project identifier from docs-project.yaml. Must match configured project ID (e.g., 'prism-data-layer')",
    )
    doc_uuid: str = Field(
        ...,
        description="Unique identifier for backend tracking. Must be valid UUID v4 format. Generated automatically by migration script",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags_format(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase and hyphenated"""
        for tag in v:
            if not re.match(r"^[a-z0-9\-]+$", tag):
                raise ValueError(f"Invalid tag '{tag}' - tags must be lowercase with hyphens only")
        return v

    @field_validator("doc_uuid")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Ensure doc_uuid is a valid UUID v4"""
        if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", v):
            raise ValueError(f"doc_uuid must be a valid UUID v4 format. Got: {v}")
        return v


# Valid status values for quick reference
VALID_ADR_STATUSES = ["Proposed", "Accepted", "Implemented", "Deprecated", "Superseded"]
VALID_RFC_STATUSES = ["Draft", "Proposed", "Accepted", "Implemented", "Deprecated", "Superseded"]

# Common tag suggestions (not enforced, just for reference)
COMMON_TAGS = [
    "architecture",
    "backend",
    "performance",
    "go",
    "rust",
    "testing",
    "reliability",
    "dx",
    "operations",
    "observability",
    "plugin",
    "cli",
    "protobuf",
    "api-design",
    "deployment",
    "security",
    "authentication",
    "patterns",
    "schemas",
    "registry",
]
