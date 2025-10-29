"""Test suite for Pydantic schema validation."""

from datetime import date

import pytest
from pydantic import ValidationError

from docuchango.schemas import (
    ADRFrontmatter,
    DocsProjectConfig,
    GenericDocFrontmatter,
    MemoFrontmatter,
    PRDFrontmatter,
    RFCFrontmatter,
)


class TestADRFrontmatter:
    """Test ADR frontmatter schema validation."""

    def test_valid_adr(self):
        """Test that valid ADR frontmatter passes validation."""
        adr = ADRFrontmatter(
            title="Use gRPC for API Design",
            status="Accepted",
            date=date(2025, 10, 13),
            deciders="Engineering Team",
            tags=["grpc", "api", "design"],
            id="adr-001",
            project_id="test-project",
            doc_uuid="8b063564-82a5-4a21-943f-e868388d36b9",
        )
        assert adr.title == "Use gRPC for API Design"
        assert adr.status == "Accepted"
        assert adr.id == "adr-001"

    def test_adr_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ADRFrontmatter(
                title="Test ADR",
                status="Proposed",
                date=date(2025, 10, 13),
                # Missing deciders
                tags=["test"],
                id="adr-001",
                project_id="test-project",
                doc_uuid="8b063564-82a5-4a21-943f-e868388d36b9",
            )
        assert "deciders" in str(exc_info.value)

    def test_adr_invalid_status(self):
        """Test that invalid status values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ADRFrontmatter(
                title="Test ADR",
                status="Invalid",  # Not in allowed values
                date=date(2025, 10, 13),
                deciders="Team",
                tags=["test"],
                id="adr-001",
                project_id="test-project",
                doc_uuid="8b063564-82a5-4a21-943f-e868388d36b9",
            )
        assert "status" in str(exc_info.value).lower()

    def test_adr_invalid_id_format(self):
        """Test that invalid ID format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ADRFrontmatter(
                title="Test ADR",
                status="Proposed",
                date=date(2025, 10, 13),
                deciders="Team",
                tags=["test"],
                id="ADR-001",  # Should be lowercase
                project_id="test-project",
                doc_uuid="8b063564-82a5-4a21-943f-e868388d36b9",
            )
        assert "adr-XXX" in str(exc_info.value).lower() or "lowercase" in str(exc_info.value).lower()

    def test_adr_invalid_uuid(self):
        """Test that invalid UUID format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ADRFrontmatter(
                title="Test ADR",
                status="Proposed",
                date=date(2025, 10, 13),
                deciders="Team",
                tags=["test"],
                id="adr-001",
                project_id="test-project",
                doc_uuid="not-a-uuid",
            )
        assert "uuid" in str(exc_info.value).lower()

    def test_adr_invalid_tags(self):
        """Test that invalid tag format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ADRFrontmatter(
                title="Test ADR",
                status="Proposed",
                date=date(2025, 10, 13),
                deciders="Team",
                tags=["Invalid Tag"],  # Should be lowercase with hyphens
                id="adr-001",
                project_id="test-project",
                doc_uuid="8b063564-82a5-4a21-943f-e868388d36b9",
            )
        assert "tag" in str(exc_info.value).lower()

    def test_adr_short_title(self):
        """Test that titles shorter than minimum length are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ADRFrontmatter(
                title="Short",  # Less than 10 characters
                status="Proposed",
                date=date(2025, 10, 13),
                deciders="Team",
                tags=["test"],
                id="adr-001",
                project_id="test-project",
                doc_uuid="8b063564-82a5-4a21-943f-e868388d36b9",
            )
        assert "title" in str(exc_info.value).lower()


class TestRFCFrontmatter:
    """Test RFC frontmatter schema validation."""

    def test_valid_rfc(self):
        """Test that valid RFC frontmatter passes validation."""
        rfc = RFCFrontmatter(
            title="VPC Management Gateway",
            status="Proposed",
            author="Engineering Team",
            created=date(2025, 10, 13),
            updated=date(2025, 10, 14),
            tags=["vpc", "management"],
            id="rfc-001",
            project_id="test-project",
            doc_uuid="046aa65f-f236-4221-9c19-6bf3e1e9f0f0",
        )
        assert rfc.title == "VPC Management Gateway"
        assert rfc.status == "Proposed"
        assert rfc.id == "rfc-001"

    def test_rfc_missing_author(self):
        """Test that missing author raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RFCFrontmatter(
                title="Test RFC Title",
                status="Draft",
                # Missing author
                created=date(2025, 10, 13),
                tags=["test"],
                id="rfc-001",
                project_id="test-project",
                doc_uuid="046aa65f-f236-4221-9c19-6bf3e1e9f0f0",
            )
        assert "author" in str(exc_info.value).lower()

    def test_rfc_optional_updated(self):
        """Test that updated field is optional."""
        rfc = RFCFrontmatter(
            title="Test RFC Title",
            status="Draft",
            author="Team",
            created=date(2025, 10, 13),
            # updated is optional
            tags=["test"],
            id="rfc-001",
            project_id="test-project",
            doc_uuid="046aa65f-f236-4221-9c19-6bf3e1e9f0f0",
        )
        assert rfc.updated is None

    def test_rfc_invalid_status(self):
        """Test that invalid status values are rejected."""
        with pytest.raises(ValidationError):
            RFCFrontmatter(
                title="Test RFC Title",
                status="InvalidStatus",
                author="Team",
                created=date(2025, 10, 13),
                tags=["test"],
                id="rfc-001",
                project_id="test-project",
                doc_uuid="046aa65f-f236-4221-9c19-6bf3e1e9f0f0",
            )


class TestMemoFrontmatter:
    """Test Memo frontmatter schema validation."""

    def test_valid_memo(self):
        """Test that valid Memo frontmatter passes validation."""
        memo = MemoFrontmatter(
            title="Atlas TFC Agent Request Pattern",
            author="Engineering Team",
            created=date(2025, 10, 14),
            updated=date(2025, 10, 14),
            tags=["atlas", "tfc", "agent"],
            id="memo-001",
            project_id="test-project",
            doc_uuid="5c345ed0-a7e3-4104-832b-c0c5d7f2848d",
        )
        assert memo.title == "Atlas TFC Agent Request Pattern"
        assert memo.id == "memo-001"

    def test_memo_missing_updated(self):
        """Test that missing updated field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            MemoFrontmatter(
                title="Test Memo Title",
                author="Team",
                created=date(2025, 10, 14),
                # Missing updated - it's required for memos
                tags=["test"],
                id="memo-001",
                project_id="test-project",
                doc_uuid="5c345ed0-a7e3-4104-832b-c0c5d7f2848d",
            )
        assert "updated" in str(exc_info.value).lower()

    def test_memo_invalid_id_format(self):
        """Test that invalid memo ID format is rejected."""
        with pytest.raises(ValidationError):
            MemoFrontmatter(
                title="Test Memo Title",
                author="Team",
                created=date(2025, 10, 14),
                updated=date(2025, 10, 14),
                tags=["test"],
                id="MEMO-001",  # Should be lowercase
                project_id="test-project",
                doc_uuid="5c345ed0-a7e3-4104-832b-c0c5d7f2848d",
            )


class TestGenericDocFrontmatter:
    """Test Generic documentation frontmatter schema validation."""

    def test_valid_generic_doc(self):
        """Test that valid generic doc frontmatter passes validation."""
        doc = GenericDocFrontmatter(
            title="Getting Started",
            project_id="test-project",
            doc_uuid="046aa65f-f236-4221-9c19-6bf3e1e9f0f0",
        )
        assert doc.title == "Getting Started"
        assert doc.description is None
        assert doc.sidebar_position is None

    def test_generic_doc_with_optional_fields(self):
        """Test that optional fields work correctly."""
        doc = GenericDocFrontmatter(
            title="Getting Started Guide",
            description="A guide for getting started",
            sidebar_position=1,
            tags=["guide", "tutorial"],
            id="getting-started",
            project_id="test-project",
            doc_uuid="046aa65f-f236-4221-9c19-6bf3e1e9f0f0",
        )
        assert doc.description == "A guide for getting started"
        assert doc.sidebar_position == 1
        assert len(doc.tags) == 2

    def test_generic_doc_short_title(self):
        """Test that very short titles are rejected."""
        with pytest.raises(ValidationError):
            GenericDocFrontmatter(
                title="AB",  # Less than 3 characters
                project_id="test-project",
                doc_uuid="046aa65f-f236-4221-9c19-6bf3e1e9f0f0",
            )

    def test_generic_doc_missing_required(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            GenericDocFrontmatter(
                title="Test Doc",
                # Missing project_id and doc_uuid
            )


class TestPRDFrontmatter:
    """Test PRD frontmatter schema validation."""

    def test_valid_prd(self):
        """Test that valid PRD frontmatter passes validation."""
        prd = PRDFrontmatter(
            title="User Authentication System",
            status="Draft",
            author="Product Team",
            created=date(2025, 10, 15),
            updated=date(2025, 10, 20),
            target_release="v2.0.0",
            tags=["feature", "authentication", "security"],
            id="prd-001",
            project_id="test-project",
            doc_uuid="9a234567-1234-4abc-8def-123456789abc",
        )
        assert prd.title == "User Authentication System"
        assert prd.status == "Draft"
        assert prd.target_release == "v2.0.0"
        assert prd.id == "prd-001"

    def test_prd_missing_target_release(self):
        """Test that missing target_release field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PRDFrontmatter(
                title="Test PRD Title",
                status="Draft",
                author="Team",
                created=date(2025, 10, 15),
                # Missing target_release
                tags=["test"],
                id="prd-001",
                project_id="test-project",
                doc_uuid="9a234567-1234-4abc-8def-123456789abc",
            )
        assert "target_release" in str(exc_info.value).lower()

    def test_prd_invalid_status(self):
        """Test that invalid PRD status values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRDFrontmatter(
                title="Test PRD Title",
                status="Invalid Status",  # Not in allowed values
                author="Team",
                created=date(2025, 10, 15),
                target_release="v1.0.0",
                tags=["test"],
                id="prd-001",
                project_id="test-project",
                doc_uuid="9a234567-1234-4abc-8def-123456789abc",
            )
        assert "status" in str(exc_info.value).lower()

    def test_prd_invalid_id_format(self):
        """Test that invalid PRD ID format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRDFrontmatter(
                title="Test PRD Title",
                status="Draft",
                author="Team",
                created=date(2025, 10, 15),
                target_release="v1.0.0",
                tags=["test"],
                id="PRD-001",  # Should be lowercase
                project_id="test-project",
                doc_uuid="9a234567-1234-4abc-8def-123456789abc",
            )
        assert "prd-xxx" in str(exc_info.value).lower() or "lowercase" in str(exc_info.value).lower()

    def test_prd_updated_required(self):
        """Test that PRD updated field is required (consistent with Memo)."""
        with pytest.raises(ValidationError) as exc_info:
            PRDFrontmatter(
                title="Test PRD with no update",
                status="Draft",
                author="Team",
                created=date(2025, 10, 15),
                # updated is now required - missing it should fail
                target_release="Q1 2026",
                tags=["test"],
                id="prd-002",
                project_id="test-project",
                doc_uuid="9a234567-1234-4abc-8def-123456789abc",
            )
        assert "updated" in str(exc_info.value).lower()


class TestDocsProjectConfig:
    """Test DocsProjectConfig schema validation."""

    def test_valid_config_with_all_fields(self):
        """Test that valid config with all fields passes validation."""
        config = DocsProjectConfig(
            project={
                "id": "example-project",
                "name": "Example Project",
                "description": "Test project description",
            },
            structure={
                "adr_dir": "adr",
                "rfc_dir": "rfcs",
                "memo_dir": "memos",
                "prd_dir": "prd",
                "template_dir": "templates",
                "document_folders": ["adr", "rfcs", "memos", "prd"],
            },
            metadata={
                "created": date(2025, 10, 27),
                "maintainers": ["Human Team", "AI Agents"],
                "purpose": "Demonstrate best practices",
            },
        )
        assert config.project.id == "example-project"
        assert config.project.name == "Example Project"
        assert config.structure.adr_dir == "adr"
        assert config.structure.prd_dir == "prd"
        assert len(config.structure.document_folders) == 4
        assert config.metadata is not None
        assert config.metadata.purpose == "Demonstrate best practices"

    def test_valid_config_with_defaults(self):
        """Test that config works with minimal required fields and defaults."""
        config = DocsProjectConfig(
            project={
                "id": "minimal-project",
                "name": "Minimal Project",
            }
            # structure and metadata will use defaults
        )
        assert config.project.id == "minimal-project"
        assert config.structure.adr_dir == "adr"
        assert config.structure.rfc_dir == "rfcs"
        assert config.structure.memo_dir == "memos"
        assert config.structure.prd_dir == "prd"
        assert config.structure.template_dir == "templates"
        assert config.structure.document_folders == ["adr", "rfcs", "memos", "prd"]
        assert config.metadata is None

    def test_config_custom_document_folders(self):
        """Test that document_folders can be customized."""
        config = DocsProjectConfig(
            project={
                "id": "custom-project",
                "name": "Custom Project",
            },
            structure={
                "document_folders": ["adr", "prd"],  # Only scan ADR and PRD
            },
        )
        assert config.structure.document_folders == ["adr", "prd"]
        # Other fields should use defaults
        assert config.structure.adr_dir == "adr"
        assert config.structure.rfc_dir == "rfcs"

    def test_config_invalid_project_id(self):
        """Test that invalid project ID format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocsProjectConfig(
                project={
                    "id": "Invalid_Project_ID",  # Contains uppercase and underscore
                    "name": "Test Project",
                }
            )
        assert "lowercase" in str(exc_info.value).lower() or "hyphen" in str(exc_info.value).lower()

    def test_config_missing_required_project_fields(self):
        """Test that missing required project fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DocsProjectConfig(
                project={
                    "id": "test-project",
                    # Missing name
                }
            )
        assert "name" in str(exc_info.value).lower()

    def test_config_custom_folder_names(self):
        """Test that folder names can be customized."""
        config = DocsProjectConfig(
            project={
                "id": "custom-folders",
                "name": "Custom Folders Project",
            },
            structure={
                "adr_dir": "decisions",
                "rfc_dir": "proposals",
                "memo_dir": "notes",
                "prd_dir": "requirements",
                "document_folders": ["decisions", "proposals", "requirements"],
            },
        )
        assert config.structure.adr_dir == "decisions"
        assert config.structure.rfc_dir == "proposals"
        assert config.structure.memo_dir == "notes"
        assert config.structure.prd_dir == "requirements"
        assert config.structure.document_folders == ["decisions", "proposals", "requirements"]
