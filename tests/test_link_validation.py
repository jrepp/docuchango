"""Test suite for link validation functionality."""

import re
import time

from click.testing import CliRunner

from docuchango.cli import validate
from docuchango.fixes.mdx_syntax import fix_mdx_issues
from docuchango.validator import DocValidator, LinkType


def _flat(text: str) -> str:
    """Collapse whitespace so Rich's console wrapping cannot break matching."""
    return re.sub(r"\s+", " ", text)


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

    def test_valid_relative_static_asset_link(self, tmp_path):
        """Test validation of relative links to non-markdown assets."""
        docs_root = tmp_path / "repo"
        rfc_dir = docs_root / "docs-cms" / "rfcs"
        static_dir = docs_root / "docs-cms" / "static" / "rfc-001"
        rfc_dir.mkdir(parents=True)
        static_dir.mkdir(parents=True)

        target_file = static_dir / "architecture.png"
        target_file.write_bytes(b"png")

        doc_file = rfc_dir / "rfc-001-test.md"
        content = """---
id: "rfc-001"
title: "Test RFC"
status: Draft
created: 2025-10-13
authors: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

![Architecture](../static/rfc-001/architecture.png)
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        rfc_doc = [doc for doc in validator.documents if "rfc-001" in str(doc.file_path)][0]
        assert len(rfc_doc.links) == 1
        assert rfc_doc.links[0].is_valid is True
        assert not rfc_doc.links[0].error_message.endswith(".png.md")

    def test_valid_relative_static_asset_link_with_query_and_anchor(self, tmp_path):
        """Test validation ignores query strings and anchors on asset links."""
        docs_root = tmp_path / "repo"
        rfc_dir = docs_root / "docs-cms" / "rfcs"
        static_dir = docs_root / "docs-cms" / "static" / "rfc-001"
        rfc_dir.mkdir(parents=True)
        static_dir.mkdir(parents=True)

        target_file = static_dir / "architecture.svg"
        target_file.write_text("<svg></svg>")

        doc_file = rfc_dir / "rfc-001-test.md"
        content = """---
id: "rfc-001"
title: "Test RFC"
status: Draft
created: 2025-10-13
authors: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

![Architecture](../static/rfc-001/architecture.svg?raw=true#diagram)
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        rfc_doc = [doc for doc in validator.documents if "rfc-001" in str(doc.file_path)][0]
        assert len(rfc_doc.links) == 1
        assert rfc_doc.links[0].is_valid is True

    def test_valid_relative_asset_link_with_url_escaped_name(self, tmp_path):
        """Test validation decodes URL-escaped local file names."""
        docs_root = tmp_path / "repo"
        rfc_dir = docs_root / "docs-cms" / "rfcs"
        static_dir = docs_root / "docs-cms" / "static" / "rfc-001"
        rfc_dir.mkdir(parents=True)
        static_dir.mkdir(parents=True)

        target_file = static_dir / "expanded architecture.png"
        target_file.write_bytes(b"png")

        doc_file = rfc_dir / "rfc-001-test.md"
        content = """---
id: "rfc-001"
title: "Test RFC"
status: Draft
created: 2025-10-13
authors: Team
tags: ["test"]
project_id: "test-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

![Architecture](../static/rfc-001/expanded%20architecture.png)
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

        rfc_doc = [doc for doc in validator.documents if "rfc-001" in str(doc.file_path)][0]
        assert len(rfc_doc.links) == 1
        assert rfc_doc.links[0].is_valid is True

    def test_valid_extensionless_relative_internal_link(self, tmp_path):
        """Test extensionless document links still fall back to .md."""
        docs_root = tmp_path / "repo"
        doc_dir = docs_root / "docs-cms" / "adr"
        doc_dir.mkdir(parents=True)

        target_file = doc_dir / "adr-002-target.md"
        target_file.write_text("# Target\n")

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

See [ADR 002](./adr-002-target#context) for details.
"""
        doc_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.extract_links()
        validator.validate_links()

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


class TestLnk010EndToEnd:
    """LNK-010 through the real ``validate`` command.

    The fixer and the LNK-001 report resolve links with the same code in
    ``docuchango.links``, so these cases check the pairing that matters: a
    single candidate is rewritten and leaves nothing to report, several
    candidates are left alone and named in the report, and a link inside a
    code fence is invisible to both.
    """

    CONFIG = """version: "1"
project:
  id: fixture-project
  name: Fixture Project
  description: Synthetic project
structure:
  adr_dir: adr
  rfc_dir: rfcs
  doc_types:
    adr:
      schema: adr
      folders: [adr]
    rfc:
      schema: rfc
      folders: [rfcs]
    guide:
      schema: generic
      folders: [guides, handbook]
security:
  allow_external_paths: false
readability:
  enabled: false
"""

    RFC = """---
id: "rfc-001"
title: "RFC-001: Links Out"
status: Draft
created: 2026-01-02
author: Team
tags: ["test"]
project_id: "fixture-project"
doc_uuid: "8b063564-82a5-4a21-943f-e868388d36b9"
---

# RFC-001: Links Out

{body}
"""

    ADR = """---
id: "adr-002"
title: "ADR-002: Target"
status: Accepted
created: 2026-01-02
deciders: Team
tags: ["test"]
project_id: "fixture-project"
doc_uuid: "9b063564-82a5-4a21-943f-e868388d36b9"
---

# ADR-002: Target

The document the link is meant to reach.
"""

    GUIDE = """---
title: "Setup, the {folder} copy"
tags: ["test"]
project_id: "fixture-project"
doc_uuid: "{uuid}"
---

# Setup

One of two documents named `setup.md`.
"""

    def _repo(self, tmp_path, body):
        """A repo whose RFC-001 body is ``body``; returns (root, rfc path)."""
        root = tmp_path / "repo"
        (root / "docs-cms").mkdir(parents=True)
        (root / "docs-cms" / "docs-project.yaml").write_text(self.CONFIG)
        (root / "docs-cms" / "rfcs").mkdir()
        rfc = root / "docs-cms" / "rfcs" / "rfc-001-links-out.md"
        rfc.write_text(self.RFC.format(body=body))
        return root, rfc

    def _adr(self, root):
        (root / "docs-cms" / "adr").mkdir(parents=True, exist_ok=True)
        (root / "docs-cms" / "adr" / "adr-002-target.md").write_text(self.ADR)

    def _guides(self, root):
        """Two `setup.md` documents in generic lanes, so the shared filename
        is an LNK-010 ambiguity and not also an ID or UUID duplicate."""
        for folder, uuid in (
            ("guides", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            ("handbook", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
        ):
            path = root / "docs-cms" / folder
            path.mkdir(parents=True, exist_ok=True)
            (path / "setup.md").write_text(self.GUIDE.format(folder=folder, uuid=uuid))

    def _run(self, root, *extra):
        args = ["--repo-root", str(root), "--skip-build", *extra]
        return CliRunner().invoke(validate, args, env={"COLUMNS": "200"}, catch_exceptions=False)

    def test_unique_candidate_is_rewritten_and_nothing_is_reported(self, tmp_path):
        root, rfc = self._repo(tmp_path, "See [the decision](./adr-002-target.md#context).")
        self._adr(root)

        result = self._run(root)

        assert result.exit_code == 0, result.output
        assert (
            "LNK-010: Line 14: Rewrote link './adr-002-target.md#context' to '../adr/adr-002-target.md#context'"
            in _flat(result.output)
        )
        assert "(../adr/adr-002-target.md#context)" in rfc.read_text()

    def test_second_run_reports_and_changes_nothing(self, tmp_path):
        root, rfc = self._repo(tmp_path, "See [the decision](./adr-002-target.md).")
        self._adr(root)

        self._run(root)
        after_first = rfc.read_text()
        result = self._run(root)

        assert result.exit_code == 0, result.output
        assert "LNK-010" not in result.output
        assert rfc.read_text() == after_first

    def test_ambiguous_candidates_are_left_alone_and_listed(self, tmp_path):
        root, rfc = self._repo(tmp_path, "Follow [the setup guide](./setup.md).")
        self._guides(root)
        before = rfc.read_text()

        result = self._run(root, "--dry-run")
        flat = _flat(result.output)

        assert result.exit_code == 1
        assert "LNK-001: Line 14: Broken link './setup.md'" in flat
        assert "2 scanned documents are named 'setup.md'" in flat
        assert "../guides/setup.md, ../handbook/setup.md" in flat
        assert "Rewrote link" not in flat
        assert rfc.read_text() == before

    def test_link_in_a_code_fence_is_neither_reported_nor_rewritten(self, tmp_path):
        root, rfc = self._repo(tmp_path, "```markdown\nSee [the decision](./adr-002-target.md).\n```")
        self._adr(root)
        before = rfc.read_text()

        result = self._run(root, "--dry-run")

        assert result.exit_code == 0, result.output
        assert "LNK-001" not in result.output
        assert "LNK-010" not in result.output
        assert rfc.read_text() == before

    def test_no_candidate_stays_a_plain_report(self, tmp_path):
        root, rfc = self._repo(tmp_path, "See [the decision](./adr-999-missing.md).")
        before = rfc.read_text()

        result = self._run(root, "--dry-run")
        flat = _flat(result.output)

        assert result.exit_code == 1
        assert "LNK-001: Line 14: Broken link './adr-999-missing.md'" in flat
        assert "scanned documents are named" not in flat
        assert rfc.read_text() == before


class TestMdxDurationPatternBacktrackingSafety:
    """fix_mdx_issues() backtick-wraps '<10ms'-style text so MDX doesn't parse it as a
    JSX tag. The regex behind that once used an unbounded '\\w+' for the optional
    trailing word, which is vulnerable to catastrophic backtracking (ReDoS) on inputs
    with many short "words" after the number. It was bounded to '\\w{1,20}'. These
    tests exercise the real fix_mdx_issues() function (not a copy of the regex) so a
    future edit that reintroduces unbounded backtracking gets caught here.
    """

    def test_many_words_after_number_completes_quickly(self):
        """Test that a line with many space-separated words doesn't trigger exponential
        backtracking."""
        adversarial = "<123 " + "abc " * 30 + "xyz"

        start = time.time()
        _fixed, changes = fix_mdx_issues(adversarial)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"fix_mdx_issues took too long: {elapsed}s (possible ReDoS)"
        assert changes  # The leading number was still matched and fixed

    def test_word_longer_than_twenty_chars_is_truncated_at_the_backtick(self):
        """Test that the trailing word is capped at 20 characters: the match (and thus
        the backtick-wrapped portion) stops there, and the remainder of the word is
        left outside the backticks."""
        line = "<123 verylongwordthatexceedstwentycharacters"

        start = time.time()
        fixed, changes = fix_mdx_issues(line)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"fix_mdx_issues took too long: {elapsed}s (possible ReDoS)"
        assert fixed == "`<123 verylongwordthatexce`edstwentycharacters"
        assert changes == ["Line 1: '<123 verylongwordthatexce' → '`<123 verylongwordthatexce`'"]

    def test_valid_duration_and_size_annotations_are_still_backtick_wrapped(self):
        """Test that the bounded regex still matches every real-world case it's meant to:
        bare numbers, durations, percentages, and byte-size units."""
        cases = {
            "<10": "`<10`",
            "<10ms": "`<10ms`",
            "<1 minute": "`<1 minute`",
            "<0.5 seconds": "`<0.5 seconds`",
            "<100%": "`<100%`",
            "<5MB": "`<5MB`",
            "<2.5GB": "`<2.5GB`",
            "<1KB": "`<1KB`",
        }

        for line, expected in cases.items():
            fixed, changes = fix_mdx_issues(line)
            assert fixed == expected, f"Should fix {line!r} to {expected!r}"
            assert len(changes) == 1

    def test_content_already_in_backticks_is_left_alone(self):
        """Test that already-backticked '<...' text is not double-wrapped."""
        for line in ["`<10ms`", "`<1 minute`", "``<100%``"]:
            fixed, changes = fix_mdx_issues(line)
            assert fixed == line
            assert changes == []
