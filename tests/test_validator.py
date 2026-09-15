"""Test suite for the documentation validator."""

from pathlib import Path

import pytest

from docuchango.validator import DocValidator


class TestMarkdownValidation:
    """Test markdown validation against known good and bad fixtures."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"

    def test_fixtures_exist(self, fixtures_dir):
        """Verify that test fixtures directory exists and contains files."""
        assert fixtures_dir.exists(), "Fixtures directory does not exist"
        assert (fixtures_dir / "pass").exists(), "Pass fixtures directory missing"
        assert (fixtures_dir / "fail").exists(), "Fail fixtures directory missing"

        pass_fixtures = list((fixtures_dir / "pass").glob("*.md"))
        fail_fixtures = list((fixtures_dir / "fail").glob("*.md"))

        assert len(pass_fixtures) > 0, "No passing fixtures found"
        assert len(fail_fixtures) > 0, "No failing fixtures found"

    def test_passing_fixtures(self, fixtures_dir, tmp_path):
        """Test that documents in pass directory validate successfully."""
        pass_dir = fixtures_dir / "pass"
        fixtures = list(pass_dir.glob("*.md"))

        assert len(fixtures) > 0, "No passing test fixtures found"

        for fixture_file in fixtures:
            docs_root = tmp_path / f"test_{fixture_file.stem}"

            if fixture_file.stem.startswith("adr-"):
                target_dir = docs_root / "docs-cms" / "adr"
            elif fixture_file.stem.startswith("rfc-"):
                target_dir = docs_root / "docs-cms" / "rfcs"
            elif fixture_file.stem.startswith("memo-"):
                target_dir = docs_root / "docs-cms" / "memos"
            else:
                pytest.fail(f"Unknown fixture type: {fixture_file.stem}")

            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / fixture_file.name
            target_file.write_text(fixture_file.read_text())

            validator = DocValidator(repo_root=docs_root, verbose=False)
            validator.scan_documents()
            validator.check_code_blocks()
            validator.check_formatting()

            # Collect all errors (validator-level + all document-level)
            all_errors = list(validator.errors)
            for doc in validator.documents:
                all_errors.extend(doc.errors)

            code_block_errors = [e for e in all_errors if "code block" in e.lower() or "fence" in e.lower()]
            format_errors = [e for e in all_errors if "whitespace" in e.lower()]

            assert len(code_block_errors) == 0, (
                f"Fixture {fixture_file.name} has code block errors: {code_block_errors}"
            )
            assert len(format_errors) == 0, f"Fixture {fixture_file.name} has formatting errors: {format_errors}"

    def test_failing_fixtures(self, fixtures_dir, tmp_path):
        """Test that documents in fail directory fail validation with expected errors."""
        fail_dir = fixtures_dir / "fail"
        fixtures = list(fail_dir.glob("*.md"))

        assert len(fixtures) > 0, "No failing test fixtures found"

        for fixture_file in fixtures:
            docs_root = tmp_path / f"test_{fixture_file.stem}"

            if fixture_file.stem.startswith("adr-"):
                target_dir = docs_root / "docs-cms" / "adr"
            elif fixture_file.stem.startswith("rfc-"):
                target_dir = docs_root / "docs-cms" / "rfcs"
            elif fixture_file.stem.startswith("memo-"):
                target_dir = docs_root / "docs-cms" / "memos"
            else:
                pytest.fail(f"Unknown fixture type: {fixture_file.stem}")

            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / fixture_file.name
            target_file.write_text(fixture_file.read_text())

            validator = DocValidator(repo_root=docs_root, verbose=False)
            validator.scan_documents()
            validator.check_code_blocks()
            validator.check_formatting()

            # Collect all errors (validator-level + all document-level)
            all_errors = list(validator.errors)
            for doc in validator.documents:
                all_errors.extend(doc.errors)

            assert len(all_errors) > 0, f"Fixture {fixture_file.name} should fail but passed validation"

    def test_unclosed_code_fence_error_message(self, tmp_path):
        """Test that unclosed code fence errors are clear and point to the root cause (Issue #31)."""
        docs_root = tmp_path / "test_issue31"
        target_dir = docs_root / "docs-cms" / "memos"
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create a document with an unclosed code fence that causes cascading errors
        content = """---
id: "memo-999"
slug: memo-999-test
title: "Test Unclosed Fence"
date: "2025-11-16"
author: "Test Author"
created: "2025-11-16"
updated: "2025-11-16"
tags: ["test"]
project_id: "test-project"
doc_uuid: "12345678-1234-4000-8000-123456789012"
---

## Section 1

Some content here.

```markdown
This is markdown content.
More markdown content here.

## Section 2

This should trigger confusion because the markdown fence above is unclosed.

```text
This looks like a new code block.
```

## Section 3

More content.
"""
        target_file = target_dir / "memo-999-test-unclosed.md"
        target_file.write_text(content)

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.check_code_blocks()

        # Collect all errors
        all_errors = []
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        # Should have at least 2 errors: unclosed block + cascading error
        assert len(all_errors) >= 2, f"Expected at least 2 errors, got {len(all_errors)}: {all_errors}"

        # Line 18 is where the ```markdown code block starts in the test content above (after frontmatter)
        unclosed_block_start_line = 18

        # First error should mention the unclosed block at the original location
        unclosed_errors = [
            e for e in all_errors if f"Unclosed code block starting at line {unclosed_block_start_line}" in e
        ]
        assert len(unclosed_errors) > 0, (
            f"Should detect unclosed block at line {unclosed_block_start_line}. Errors: {all_errors}"
        )

        # Should have a cascading error explanation
        cascading_errors = [
            e for e in all_errors if "appears to be a new opening fence" in e and "interpreted as a closing fence" in e
        ]
        assert len(cascading_errors) > 0, f"Should explain cascading error. Errors: {all_errors}"

        # Should NOT have confusing "Closing fence has extra text" errors without context
        confusing_errors = [
            e for e in all_errors if "Closing code fence has extra text" in e and "appears to be" not in e
        ]
        assert len(confusing_errors) == 0, f"Should not have confusing closing fence errors. Found: {confusing_errors}"

    def test_prd_duplicate_uuid_is_reported(self, tmp_path):
        """PRDs require doc_uuid, so duplicate PRD UUIDs must be reported."""
        docs_root = tmp_path / "repo"
        prd_dir = docs_root / "docs-cms" / "prd"
        prd_dir.mkdir(parents=True)

        duplicate_uuid = "12345678-1234-4123-8123-123456789abc"
        for number, title in [(1, "First Product Requirement"), (2, "Second Product Requirement")]:
            (prd_dir / f"prd-{number:03d}-test.md").write_text(
                f"""---
id: prd-{number:03d}
title: {title}
status: Draft
author: Product Team
created: 2025-01-0{number}
target_release: TBD
tags: []
project_id: test-project
doc_uuid: {duplicate_uuid}
---

# {title}
""",
                encoding="utf-8",
            )

        validator = DocValidator(repo_root=docs_root, verbose=False)
        validator.scan_documents()
        validator.check_uuids()

        all_errors = []
        for doc in validator.documents:
            all_errors.extend(doc.errors)

        assert any("Duplicate UUID" in error and duplicate_uuid in error for error in all_errors)


class TestValidatorEdgeCases:
    """Test DocValidator behaviour on empty or malformed input."""

    def test_scan_documents_on_empty_directory(self, tmp_path):
        """Scanning a directory with no markdown files should yield no documents."""
        validator = DocValidator(repo_root=tmp_path, verbose=False)
        validator.scan_documents()
        assert len(validator.documents) == 0

    def test_scan_documents_with_malformed_frontmatter_does_not_raise(self, tmp_path):
        """Malformed YAML frontmatter should be recorded as a document error, not raise."""
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()

        test_file = adr_dir / "adr-001-test.md"
        # Invalid YAML frontmatter (unterminated quote)
        test_file.write_text(
            """---
title: "Test
status: accepted
---

# Content
""",
            encoding="utf-8",
        )

        validator = DocValidator(repo_root=tmp_path, verbose=False)
        validator.scan_documents()

        # A file whose frontmatter can't be parsed is skipped, not raised.
        assert len(validator.documents) == 0


class TestUtf8ByteOrderMark:
    """FMT-012: documents behind a UTF-8 BOM are parsed, and the BOM is reported."""

    BOM = b"\xef\xbb\xbf"
    VALID_ADR = (
        "---\n"
        'id: "adr-001"\n'
        'title: "ADR-001: Test"\n'
        "status: Accepted\n"
        "created: 2026-01-02\n"
        "tags: []\n"
        'project_id: "fixture"\n'
        'doc_uuid: "4f2f2b3e-0e2c-4b0a-9a4f-2a8b1c9d0e11"\n'
        "---\n"
        "# ADR-001: Test\n"
    )

    def _adr(self, tmp_path: Path, body: bytes) -> Path:
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        doc = adr_dir / "adr-001-test.md"
        doc.write_bytes(body)
        return doc

    def test_frontmatter_behind_a_bom_is_parsed(self, tmp_path):
        """A BOM must not make a document with frontmatter look like it has none."""
        self._adr(tmp_path, self.BOM + self.VALID_ADR.encode("utf-8"))

        validator = DocValidator(repo_root=tmp_path, verbose=False)
        validator.scan_documents()

        assert len(validator.documents) == 1
        doc = validator.documents[0]
        assert doc.doc_id == "adr-001"
        assert not any("Missing YAML frontmatter" in error for error in doc.errors)

    def test_bom_is_reported_as_fmt_012(self, tmp_path):
        """check_formatting reports the byte-order mark it found on disk."""
        self._adr(tmp_path, self.BOM + self.VALID_ADR.encode("utf-8"))

        validator = DocValidator(repo_root=tmp_path, verbose=False)
        validator.scan_documents()
        validator.check_formatting()

        errors = validator.documents[0].errors
        assert any("FMT-012: UTF-8 byte-order mark at start of file" in error for error in errors)

    def test_document_without_a_bom_is_not_reported(self, tmp_path):
        """FMT-012 does not fire on an ordinary UTF-8 document."""
        self._adr(tmp_path, self.VALID_ADR.encode("utf-8"))

        validator = DocValidator(repo_root=tmp_path, verbose=False)
        validator.scan_documents()
        validator.check_formatting()

        assert not any("FMT-012" in error for error in validator.documents[0].errors)

    def test_bom_without_frontmatter_still_reports_fm_001(self, tmp_path):
        """Stripping the BOM does not invent frontmatter for a plain Markdown file."""
        self._adr(tmp_path, self.BOM + b"# ADR-001: Test\n\nNo frontmatter here.\n")

        validator = DocValidator(repo_root=tmp_path, verbose=False)
        validator.scan_documents()

        assert len(validator.documents) == 1
        assert any("Missing YAML frontmatter" in error for error in validator.documents[0].errors)


class TestProjectIdMatch:
    """FM-010: project_id is compared with the governing config's project.id."""

    ROOT_CONFIG = (
        'version: "1"\n'
        "project:\n"
        "  id: root-project\n"
        "  name: Root Project\n"
        "  description: Root project of the test tree\n"
        "structure:\n"
        "  adr_dir: adr\n"
        "  rfc_dir: rfcs\n"
        "  memo_dir: memos\n"
        "  document_folders:\n"
        "    - adr\n"
        "security:\n"
        "  allow_external_paths: false\n"
        "readability:\n"
        "  enabled: false\n"
    )

    @staticmethod
    def _adr(project_id_line: str) -> str:
        return (
            "---\n"
            "id: adr-001\n"
            'title: "ADR-001: Test"\n'
            "status: Accepted\n"
            "created: 2026-01-02\n"
            "tags: []\n"
            'deciders: "Engineering Team"\n'
            f"{project_id_line}"
            "doc_uuid: 4f2f2b3e-0e2c-4b0a-9a4f-2a8b1c9d0e11\n"
            "---\n"
            "\n"
            "# ADR-001: Test\n"
        )

    def _tree(self, tmp_path: Path, project_id_line: str, config: str | None = None) -> Path:
        docs_cms = tmp_path / "docs-cms"
        (docs_cms / "adr").mkdir(parents=True)
        if config is not None:
            (docs_cms / "docs-project.yaml").write_text(config, encoding="utf-8")
        (docs_cms / "adr" / "adr-001-test.md").write_text(self._adr(project_id_line), encoding="utf-8")
        return tmp_path

    @staticmethod
    def _findings(repo_root: Path) -> list[str]:
        validator = DocValidator(repo_root=repo_root, verbose=False)
        validator.scan_documents()
        validator.check_project_ids()
        return [error for doc in validator.documents for error in doc.errors if "FM-010" in error]

    def test_matching_project_id_reports_nothing(self, tmp_path):
        """A document whose project_id equals project.id is not a finding."""
        root = self._tree(tmp_path, "project_id: root-project\n", self.ROOT_CONFIG)

        assert self._findings(root) == []

    def test_non_placeholder_mismatch_is_reported(self, tmp_path):
        """A deliberate-looking value is reported with both IDs named."""
        root = self._tree(tmp_path, "project_id: other-project\n", self.ROOT_CONFIG)

        findings = self._findings(root)

        assert len(findings) == 1
        assert "other-project" in findings[0]
        assert "root-project" in findings[0]
        assert "docs-cms/docs-project.yaml" in findings[0]

    def test_empty_project_id_is_reported(self, tmp_path):
        """An empty value is reported rather than silently passing."""
        root = self._tree(tmp_path, 'project_id: ""\n', self.ROOT_CONFIG)

        findings = self._findings(root)

        assert len(findings) == 1
        assert "(empty)" in findings[0]

    def test_missing_project_id_is_left_to_the_schema(self, tmp_path):
        """FM-002 and FM-005 own an absent key, so FM-010 does not double-report."""
        root = self._tree(tmp_path, "", self.ROOT_CONFIG)

        validator = DocValidator(repo_root=root, verbose=False)
        validator.scan_documents()
        validator.check_project_ids()

        errors = validator.documents[0].errors
        assert any("project_id" in error and "Field required" in error for error in errors)
        assert not any("FM-010" in error for error in errors)

    def test_check_is_skipped_without_a_config(self, tmp_path):
        """With no docs-project.yaml there is no project.id to compare against."""
        root = self._tree(tmp_path, "project_id: other-project\n", config=None)

        validator = DocValidator(repo_root=root, verbose=False)
        validator.scan_documents()
        validator.check_project_ids()

        assert validator.project_configs == []
        assert len(validator.documents) == 1, "the document must still be scanned for the test to mean anything"
        assert not any("FM-010" in error for error in validator.documents[0].errors)

    def test_sub_project_document_is_measured_against_its_own_config(self, tmp_path):
        """A monorepo is not flattened to the root project's ID."""
        root_config = self.ROOT_CONFIG + "subprojects:\n  - services/service-a\n"
        root = self._tree(tmp_path, "project_id: root-project\n", root_config)

        service = root / "docs-cms" / "services" / "service-a"
        (service / "adr").mkdir(parents=True)
        (service / "docs-project.yaml").write_text(
            self.ROOT_CONFIG.replace("id: root-project", "id: service-a").replace(
                "name: Root Project", "name: Service A"
            ),
            encoding="utf-8",
        )
        (service / "adr" / "adr-002-service.md").write_text(
            self._adr("project_id: root-project\n")
            .replace("adr-001", "adr-002")
            .replace("ADR-001", "ADR-002")
            .replace("4f2f2b3e", "5f2f2b3e"),
            encoding="utf-8",
        )

        findings = self._findings(root)

        assert len(findings) == 1
        assert "service-a" in findings[0]
        assert "root-project" in findings[0]
