"""Test suite for link validation functionality."""

from docuchango.validator import DocValidator, LinkType


class TestLinkExtraction:
    """Test link extraction from markdown documents."""

    def test_extract_simple_links(self, tmp_path):
        """Test extraction of basic markdown links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# ADR-001: Test Decision

See [RFC 015](../rfcs/rfc-015-test.md) for details.
Also check [external docs](https://example.com/docs).
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        assert len(validator.documents) == 1
        doc = validator.documents[0]
        assert len(doc.links) == 2

        # Check link targets
        targets = [link.target for link in doc.links]
        assert "../rfcs/rfc-015-test.md" in targets
        assert "https://example.com/docs" in targets

    def test_skip_links_in_code_fences(self, tmp_path):
        """Test that links inside code fences are ignored."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# ADR-001: Test Decision

Valid link: [docs](./test.md)

```bash
# This link should be ignored: [fake](./fake.md)
echo "test"
```

Another valid link: [example](https://example.com)
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 2  # Only 2 links outside code fence

        targets = [link.target for link in doc.links]
        assert "./test.md" in targets
        assert "https://example.com" in targets
        assert "./fake.md" not in targets

    def test_skip_links_in_inline_code(self, tmp_path):
        """Test that links in inline code are ignored."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# ADR-001: Test Decision

Use the syntax `[link](url)` for markdown links.
But this is real: [actual link](./real.md)
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 1
        assert doc.links[0].target == "./real.md"

    def test_skip_mailto_and_data_links(self, tmp_path):
        """Test that mailto: and data: links are skipped."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# ADR-001: Test Decision

Contact: [email](mailto:test@example.com)
Image: [img](data:image/png;base64,abc123)
Real link: [doc](./test.md)
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 1
        assert doc.links[0].target == "./test.md"

    def test_extract_multiple_links_per_line(self, tmp_path):
        """Test extraction of multiple links on the same line."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [RFC 001](./rfc-001.md) and [RFC 002](./rfc-002.md) for context.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 2

        targets = [link.target for link in doc.links]
        assert "./rfc-001.md" in targets
        assert "./rfc-002.md" in targets


class TestLinkClassification:
    """Test link type classification."""

    def test_classify_external_links(self, tmp_path):
        """Test classification of external HTTP/HTTPS links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [HTTP link](http://example.com) and [HTTPS link](https://example.com).
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        for link in doc.links:
            assert link.link_type == LinkType.EXTERNAL

    def test_classify_anchor_links(self, tmp_path):
        """Test classification of anchor links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [section below](#context) for details.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 1
        assert doc.links[0].link_type == LinkType.ANCHOR

    def test_classify_docusaurus_plugin_links(self, tmp_path):
        """Test classification of Docusaurus plugin links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [data layer](/prism-data-layer/netflix/scale) and [ADR](/adr/ADR-046).
Also [RFC](/rfc/RFC-001) and [memo](/memos/MEMO-003).
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 4
        for link in doc.links:
            assert link.link_type == LinkType.DOCUSAURUS_PLUGIN

    def test_classify_internal_doc_links(self, tmp_path):
        """Test classification of internal document links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [relative](./test.md) and [parent](../docs/guide.md).
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 2
        for link in doc.links:
            assert link.link_type == LinkType.INTERNAL_DOC

    def test_classify_adr_and_rfc_links(self, tmp_path):
        """Test classification of ADR and RFC links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [ADR](../adr/adr-002-test.md) and [RFC](../rfcs/rfc-001-test.md).
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()

        doc = validator.documents[0]
        assert len(doc.links) == 2

        adr_link = [link for link in doc.links if "adr" in link.target.lower()][0]
        assert adr_link.link_type == LinkType.INTERNAL_ADR

        rfc_link = [link for link in doc.links if "rfc" in link.target.lower()][0]
        assert rfc_link.link_type == LinkType.INTERNAL_RFC


class TestLinkValidation:
    """Test link validation logic."""

    def test_external_links_are_valid(self, tmp_path):
        """Test that external links are marked as valid."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [docs](https://example.com/docs).
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        doc = validator.documents[0]
        assert len(doc.links) == 1
        assert doc.links[0].is_valid is True

    def test_anchor_links_are_valid(self, tmp_path):
        """Test that anchor links are marked as valid."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [context](#context) below.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        doc = validator.documents[0]
        assert len(doc.links) == 1
        assert doc.links[0].is_valid is True

    def test_docusaurus_plugin_links_are_valid(self, tmp_path):
        """Test that Docusaurus plugin links are marked as valid."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [ADR](/adr/ADR-046) and [RFC](/rfc/RFC-001).
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        doc = validator.documents[0]
        assert len(doc.links) == 2
        for link in doc.links:
            assert link.is_valid is True

    def test_valid_relative_internal_link(self, tmp_path):
        """Test validation of existing relative internal links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        # Create target file
        target_file = doc_dir / "adr-002-target.md"
        target_file.write_text("# Target\n")

        # Create source file with link
        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [ADR 002](./adr-002-target.md) for details.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        # Find the link to adr-002
        all_links = []
        for doc in validator.documents:
            all_links.extend(doc.links)

        adr_link = [link for link in all_links if "adr-002" in link.target][0]
        assert adr_link.is_valid is True

    def test_invalid_relative_internal_link(self, tmp_path):
        """Test validation of missing relative internal links."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        # Create source file with broken link
        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [missing](./missing-file.md) for details.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        doc = validator.documents[0]
        assert len(doc.links) == 1
        assert doc.links[0].is_valid is False
        assert "not found" in doc.links[0].error_message.lower()

    def test_valid_parent_directory_link(self, tmp_path):
        """Test validation of parent directory links."""
        docs_root = tmp_path / "repo"
        adr_dir = docs_root / "docs-cms" / "adr"
        rfc_dir = docs_root / "docs-cms" / "rfcs"
        adr_dir.mkdir(parents=True)
        rfc_dir.mkdir(parents=True)

        # Create target RFC
        target_file = rfc_dir / "rfc-001-test.md"
        target_file.write_text("# RFC 001\n")

        # Create ADR with link to RFC
        doc_file = adr_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [RFC 001](../rfcs/rfc-001-test.md) for details.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        # Find ADR document
        adr_doc = [doc for doc in validator.documents if "adr-001" in str(doc.file_path)][0]
        assert len(adr_doc.links) == 1
        assert adr_doc.links[0].is_valid is True

    def test_link_with_anchor_validates_base_file(self, tmp_path):
        """Test that links with anchors validate the base file."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        # Create target file
        target_file = doc_dir / "adr-002-target.md"
        target_file.write_text("# Target\n\n## Section\n")

        # Create source file with link including anchor
        doc_file = doc_dir / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [section](./adr-002-target.md#section) for details.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        # Find the link
        adr_doc = [doc for doc in validator.documents if "adr-001" in str(doc.file_path)][0]
        assert len(adr_doc.links) == 1
        assert adr_doc.links[0].is_valid is True

    def test_multiple_documents_link_validation(self, tmp_path):
        """Test link validation across multiple documents."""
        docs_root = tmp_path / "repo"
        adr_dir = docs_root / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)

        # Create three ADRs that link to each other
        adr1 = adr_dir / "adr-001-first.md"
        adr1.write_text("""---
id: "adr-001"
title: "First Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

See [ADR 002](./adr-002-second.md) and [ADR 003](./adr-003-third.md).
""")

        adr2 = adr_dir / "adr-002-second.md"
        adr2.write_text("""---
id: "adr-002"
title: "Second Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "9b063564-82a5-4a21-943f-e868388d36b9"
---

Builds on [ADR 001](./adr-001-first.md).
""")

        adr3 = adr_dir / "adr-003-third.md"
        adr3.write_text("""---
id: "adr-003"
title: "Third Decision"
status: Accepted
date: 2025-10-13
deciders: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "ab063564-82a5-4a21-943f-e868388d36b9"
---

Supersedes [ADR 001](./adr-001-first.md) and [broken link](./missing.md).
""")

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        # Count valid and invalid links
        all_links = []
        for doc in validator.documents:
            all_links.extend(doc.links)

        valid_links = [link for link in all_links if link.is_valid]
        invalid_links = [link for link in all_links if not link.is_valid]

        assert len(valid_links) == 4  # All internal links except the broken one
        assert len(invalid_links) == 1  # Only the missing.md link
        assert invalid_links[0].target == "./missing.md"
