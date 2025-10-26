"""Test suite for frontmatter validation edge cases."""

import frontmatter
import pytest

from docuchango.validator import DocValidator


class TestFrontmatterValidation:
    """Test frontmatter validation with real documents."""

    def test_valid_adr_frontmatter(self, tmp_path):
        """Test that valid ADR frontmatter passes validation."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Engineering Team
tags: ["test", "validation"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# ADR-001: Test Decision

Content here.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        assert len(validator.documents) == 1
        doc = validator.documents[0]
        assert doc.title == "Test Decision"
        assert doc.status == "Accepted"
        assert doc.doc_id == "adr-001"

    def test_missing_required_frontmatter_field(self, tmp_path):
        """Test that missing required fields are detected."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
# Missing date, deciders
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# Content
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        # Should detect validation errors
        all_errors = list(validator.errors)
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        assert len(all_errors) > 0
        error_str = " ".join(all_errors).lower()
        # Should mention missing fields
        assert "date" in error_str or "deciders" in error_str or "required" in error_str

    def test_invalid_status_value(self, tmp_path):
        """Test that invalid status values are detected."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: InvalidStatus
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# Content
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        all_errors = list(validator.errors)
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        assert len(all_errors) > 0

    def test_invalid_uuid_format(self, tmp_path):
        """Test that documents with invalid UUID can be loaded but fail Pydantic validation."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "rfcs"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "rfc-001-test.md"
        content = """---
id: "rfc-001"
title: "Test RFC Title"
status: Draft
author: Team
created: 2025-10-13
tags: ["test"]
project_id: "test-project"
doc_uuid: "not-a-valid-uuid"
---

# Content
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        # Document is loaded but Pydantic schema validation would catch UUID format
        assert len(validator.documents) == 1

        # Verify Pydantic would catch this
        from pydantic import ValidationError

        from docuchango.schemas import RFCFrontmatter

        fm = frontmatter.load(doc_file)
        with pytest.raises(ValidationError) as exc_info:
            RFCFrontmatter(**fm.metadata)
        assert "uuid" in str(exc_info.value).lower()

    def test_invalid_tag_format(self, tmp_path):
        """Test that documents with invalid tag format can be loaded but fail Pydantic validation."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "memos"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "memo-001-test.md"
        content = """---
id: "memo-001"
title: "Test Memo Title"
author: Team
created: 2025-10-13
updated: 2025-10-13
tags: ["Valid Tag", "another_tag"]
project_id: "test-project"
doc_uuid: "5c345ed0-a7e3-4104-832b-c0c5d7f2848d"
---

# Content
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        # Document is loaded but Pydantic schema validation would catch tag format
        assert len(validator.documents) == 1

        # Verify Pydantic would catch this
        from pydantic import ValidationError

        from docuchango.schemas import MemoFrontmatter

        fm = frontmatter.load(doc_file)
        with pytest.raises(ValidationError) as exc_info:
            MemoFrontmatter(**fm.metadata)
        error_str = str(exc_info.value).lower()
        assert "tag" in error_str or "lowercase" in error_str

    def test_malformed_frontmatter(self, tmp_path):
        """Test that malformed YAML frontmatter is handled."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
tags: [unclosed array
---

# Content
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        # Should handle parsing error gracefully
        validator.scan_documents()

        all_errors = list(validator.errors)
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        # Should have errors about malformed YAML
        assert len(all_errors) > 0

    def test_missing_frontmatter(self, tmp_path):
        """Test that documents without frontmatter are detected."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """# ADR-001: Test Decision

No frontmatter here.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        all_errors = list(validator.errors)
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        # Should detect missing frontmatter
        assert len(all_errors) > 0

    def test_valid_rfc_with_optional_updated(self, tmp_path):
        """Test that RFC without updated field is valid."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "rfcs"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "rfc-001-test.md"
        content = """---
id: "rfc-001"
title: "Test RFC Title"
status: Draft
author: Team
created: 2025-10-13
tags: ["test"]
project_id: "test-project"
doc_uuid: "046aa65f-f236-4221-9c19-6bf3e1e9f0f0"
---

# Content
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        assert len(validator.documents) == 1

    def test_multiple_documents_validation(self, tmp_path):
        """Test validation of multiple documents in one run."""
        docs_root = tmp_path / "repo"

        # Create valid ADR
        adr_dir = docs_root / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)
        adr_file = adr_dir / "adr-001-valid.md"
        adr_file.write_text("""---
id: "adr-001"
title: "Valid ADR Title"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---
# Content
""")

        # Create invalid RFC
        rfc_dir = docs_root / "docs-cms" / "rfcs"
        rfc_dir.mkdir(parents=True)
        rfc_file = rfc_dir / "rfc-001-invalid.md"
        rfc_file.write_text("""---
id: "rfc-001"
title: "Short"
status: Draft
author: Team
created: 2025-10-13
tags: ["test"]
project_id: "test-project"
doc_uuid: "046aa65f-f236-4221-9c19-6bf3e1e9f0f0"
---
# Content
""")

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()

        assert len(validator.documents) == 2

        # Check that one has errors and one doesn't
        docs_with_errors = [doc for doc in validator.documents if len(doc.errors) > 0]
        assert len(docs_with_errors) > 0  # The invalid RFC should have errors
