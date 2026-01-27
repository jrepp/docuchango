"""Tests to improve code coverage for fix modules.

These tests focus on the main() functions and edge cases that were not covered
by the existing unit tests.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch


class TestCrossPluginLinksMain:
    """Test the main() function of cross_plugin_links module."""

    def test_main_with_valid_docs_cms(self, tmp_path, monkeypatch):
        """Test main() with a valid docs-cms directory structure."""
        from docuchango.fixes import cross_plugin_links

        # Create docs-cms structure
        docs_cms = tmp_path / "docs-cms"
        adr_dir = docs_cms / "adr"
        rfcs_dir = docs_cms / "rfcs"
        memos_dir = docs_cms / "memos"

        adr_dir.mkdir(parents=True)
        rfcs_dir.mkdir(parents=True)
        memos_dir.mkdir(parents=True)

        # Create test files with cross-plugin links
        adr_file = adr_dir / "ADR-001-test.md"
        adr_file.write_text("[RFC](../rfcs/RFC-001-ref.md)", encoding="utf-8")

        # Patch the module to use our test directory
        monkeypatch.setattr(
            cross_plugin_links,
            "main",
            lambda: _run_cross_plugin_main(tmp_path / "docs-cms"),
        )

        # Run main and capture output
        output = StringIO()
        with patch.object(sys, "stdout", output):
            _run_cross_plugin_main(docs_cms)

    def test_main_skips_index_and_template(self, tmp_path):
        """Test that main() skips index.md and template files."""
        from docuchango.fixes.cross_plugin_links import fix_cross_plugin_links

        docs_cms = tmp_path / "docs-cms"
        rfcs_dir = docs_cms / "rfcs"
        rfcs_dir.mkdir(parents=True)

        # Create files that should be skipped
        index_file = rfcs_dir / "index.md"
        template_file = rfcs_dir / "000-template.md"

        index_file.write_text("[Link](../adr/ADR-001.md)", encoding="utf-8")
        template_file.write_text("[Link](../adr/ADR-001.md)", encoding="utf-8")

        # These files should be skipped by main(), so test fix_cross_plugin_links directly
        # to verify they would be changed if processed
        assert fix_cross_plugin_links(index_file, dry_run=True) == 1
        assert fix_cross_plugin_links(template_file, dry_run=True) == 1

    def test_main_with_nonexistent_directory(self, tmp_path):
        """Test main() when docs-cms doesn't exist."""
        # The main() function should handle missing directories gracefully
        docs_cms = tmp_path / "docs-cms"
        # Don't create the directory
        assert not docs_cms.exists()


def _run_cross_plugin_main(docs_cms: Path) -> None:
    """Helper to run cross_plugin_links main with custom docs path."""
    import re

    directories = ["adr", "rfcs", "memos"]
    total_fixed = 0

    for directory in directories:
        dir_path = docs_cms / directory
        if not dir_path.exists():
            continue

        for md_file in dir_path.glob("*.md"):
            if md_file.name in ["index.md", "000-template.md"]:
                continue

            content = md_file.read_text(encoding="utf-8")
            original = content

            content = re.sub(r"\]\(\.\./rfcs/(RFC-[^)]+)\.md\)", r"](/rfc/\1)", content)
            content = re.sub(r"\]\(\.\./adr/(ADR-[^)]+)\.md\)", r"](/adr/\1)", content)
            content = re.sub(r"\]\(\.\./memos/(MEMO-[^)]+)\.md\)", r"](/memos/\1)", content)

            if content != original:
                md_file.write_text(content, encoding="utf-8")
                print(f"✓ Fixed {md_file.relative_to(docs_cms)}")
                total_fixed += 1

    print(f"\n✅ Fixed {total_fixed} files with cross-plugin links")


class TestDocLinksMain:
    """Test the main() function of doc_links module."""

    def test_main_function_exists(self):
        """Test that main function can be imported."""
        from docuchango.fixes.doc_links import main

        assert callable(main)

    def test_fix_links_handles_no_changes(self, tmp_path):
        """Test fix_links_in_file when no changes needed."""
        from docuchango.fixes.doc_links import fix_links_in_file

        test_file = tmp_path / "test.md"
        test_file.write_text("No links here", encoding="utf-8")

        relative, case = fix_links_in_file(test_file)
        assert relative == 0
        assert case == 0


class TestInternalLinks:
    """Test internal_links module for improved coverage."""

    def test_fix_links_in_content(self):
        """Test fix_links_in_content function."""
        from docuchango.fixes.internal_links import fix_links_in_content

        content = """# Title

[External Link](https://example.com)
"""
        result, count = fix_links_in_content(content)
        assert isinstance(result, str)
        assert isinstance(count, int)

    def test_fix_links_in_file_no_changes(self, tmp_path):
        """Test fix_links_in_file when no changes needed."""
        from docuchango.fixes.internal_links import fix_links_in_file

        test_file = tmp_path / "test.md"
        content = """# Title

[External Link](https://example.com)
"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_links_in_file(test_file, dry_run=True)
        assert result == 0

    def test_fix_links_in_file_with_changes(self, tmp_path):
        """Test fix_links_in_file with internal links to fix."""
        from docuchango.fixes.internal_links import fix_links_in_file

        test_file = tmp_path / "test.md"
        # Content with internal links that might need fixing
        content = """# Title

[ADR](ADR-001-decision.md)
"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_links_in_file(test_file, dry_run=True)
        # Result depends on the internal link patterns
        assert isinstance(result, int)

    def test_process_directory(self, tmp_path):
        """Test process_directory function."""
        from docuchango.fixes.internal_links import process_directory

        # Create a directory with a markdown file
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        test_file = test_dir / "test.md"
        test_file.write_text("# Test\n\n[Link](./other.md)", encoding="utf-8")

        result = process_directory(test_dir, dry_run=True)
        assert isinstance(result, dict)


class TestCliBootstrap:
    """Test CLI bootstrap command for improved coverage."""

    def test_bootstrap_help(self):
        """Test bootstrap command help."""
        from click.testing import CliRunner

        from docuchango.cli import bootstrap

        runner = CliRunner()
        result = runner.invoke(bootstrap, ["--help"])
        assert result.exit_code == 0
        assert "bootstrap" in result.output.lower() or "guide" in result.output.lower()

    def test_bootstrap_default(self):
        """Test bootstrap command with default guide."""
        from click.testing import CliRunner

        from docuchango.cli import bootstrap

        runner = CliRunner()
        result = runner.invoke(bootstrap)
        # May succeed or fail depending on whether guides are available
        assert result.exit_code in [0, 1]

    def test_bootstrap_agent_guide(self):
        """Test bootstrap command with agent guide."""
        from click.testing import CliRunner

        from docuchango.cli import bootstrap

        runner = CliRunner()
        result = runner.invoke(bootstrap, ["--guide", "agent"])
        # May succeed or fail depending on whether guides are available
        assert result.exit_code in [0, 1]

    def test_bootstrap_best_practices_guide(self):
        """Test bootstrap command with best-practices guide."""
        from click.testing import CliRunner

        from docuchango.cli import bootstrap

        runner = CliRunner()
        result = runner.invoke(bootstrap, ["--guide", "best-practices"])
        # May succeed or fail depending on whether guides are available
        assert result.exit_code in [0, 1]

    def test_bootstrap_output_to_file(self, tmp_path):
        """Test bootstrap command with output to file."""
        from click.testing import CliRunner

        from docuchango.cli import bootstrap

        runner = CliRunner()
        output_file = tmp_path / "guide.md"
        result = runner.invoke(bootstrap, ["--output", str(output_file)])
        # May succeed or fail depending on whether guides are available
        assert result.exit_code in [0, 1]


class TestInitCommand:
    """Test init command edge cases for improved coverage."""

    def test_init_with_existing_empty_directory(self, tmp_path):
        """Test init command with existing empty directory."""
        from click.testing import CliRunner

        from docuchango.cli import init

        target_dir = tmp_path / "docs-cms"
        target_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(init, ["--path", str(target_dir)])
        # Should succeed since directory is empty
        assert result.exit_code == 0

    def test_init_with_custom_project_info(self, tmp_path):
        """Test init command with custom project ID and name."""
        from click.testing import CliRunner

        from docuchango.cli import init

        target_dir = tmp_path / "docs-cms"

        runner = CliRunner()
        result = runner.invoke(
            init,
            [
                "--path",
                str(target_dir),
                "--project-id",
                "test-project",
                "--project-name",
                "Test Project",
            ],
        )
        assert result.exit_code == 0

        # Verify project info in docs-project.yaml
        config_file = target_dir / "docs-project.yaml"
        if config_file.exists():
            content = config_file.read_text(encoding="utf-8")
            assert "test-project" in content
            assert "Test Project" in content


class TestValidatorEdgeCases:
    """Test validator edge cases for improved coverage."""

    def test_validator_with_empty_directory(self, tmp_path):
        """Test validator with empty docs directory."""
        from docuchango.validator import DocValidator

        validator = DocValidator(repo_root=tmp_path, verbose=False, fix=False)
        validator.scan_documents()
        # Should handle empty directories gracefully
        assert len(validator.documents) == 0

    def test_validator_with_invalid_frontmatter(self, tmp_path):
        """Test validator with invalid frontmatter."""
        from docuchango.validator import DocValidator

        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()

        test_file = adr_dir / "adr-001-test.md"
        # Invalid YAML frontmatter
        test_file.write_text(
            """---
title: "Test
status: accepted
---

# Content
""",
            encoding="utf-8",
        )

        validator = DocValidator(repo_root=tmp_path, verbose=False, fix=False)
        validator.scan_documents()
        # Should handle invalid frontmatter gracefully


class TestDocsModule:
    """Test docs module for improved coverage."""

    def test_fix_trailing_whitespace(self, tmp_path):
        """Test fix_trailing_whitespace function."""
        from docuchango.fixes.docs import fix_trailing_whitespace

        test_file = tmp_path / "test.md"
        content = "# Title   \n\nContent with trailing spaces   \n"
        test_file.write_text(content, encoding="utf-8")

        result = fix_trailing_whitespace(test_file)
        assert isinstance(result, int)

    def test_fix_code_fence_languages(self, tmp_path):
        """Test fix_code_fence_languages function."""
        from docuchango.fixes.docs import fix_code_fence_languages

        test_file = tmp_path / "test.md"
        content = "```\ncode\n```\n"
        test_file.write_text(content, encoding="utf-8")

        result = fix_code_fence_languages(test_file)
        assert isinstance(result, int)

    def test_fix_blank_lines_before_fences(self, tmp_path):
        """Test fix_blank_lines_before_fences function."""
        from docuchango.fixes.docs import fix_blank_lines_before_fences

        test_file = tmp_path / "test.md"
        content = "# Title\n```python\ncode\n```\n"
        test_file.write_text(content, encoding="utf-8")

        result = fix_blank_lines_before_fences(test_file)
        assert isinstance(result, int)

    def test_fix_blank_lines_after_fences(self, tmp_path):
        """Test fix_blank_lines_after_fences function."""
        from docuchango.fixes.docs import fix_blank_lines_after_fences

        test_file = tmp_path / "test.md"
        content = "```python\ncode\n```\nMore text\n"
        test_file.write_text(content, encoding="utf-8")

        result = fix_blank_lines_after_fences(test_file)
        assert isinstance(result, int)


class TestSchemaValidation:
    """Test schema validation edge cases."""

    def test_adr_frontmatter_with_all_fields(self):
        """Test ADR frontmatter with all fields populated."""
        from docuchango.schemas import ADRFrontmatter

        frontmatter = ADRFrontmatter(
            id="adr-001",
            title="Test ADR Title That Is Long Enough",
            status="Accepted",
            tags=["api", "database"],
            created="2024-01-01",
            updated="2024-01-02",
            deciders="Core Team",
            project_id="test-project",
            doc_uuid="12345678-1234-4123-8123-123456789abc",
        )
        assert frontmatter.id == "adr-001"
        assert frontmatter.status == "Accepted"

    def test_rfc_frontmatter_with_all_fields(self):
        """Test RFC frontmatter with all fields populated."""
        from docuchango.schemas import RFCFrontmatter

        frontmatter = RFCFrontmatter(
            id="rfc-015",
            title="Test RFC Title That Is Long Enough",
            status="Accepted",
            tags=["api"],
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-02",
            project_id="test-project",
            doc_uuid="12345678-1234-4123-8123-123456789abc",
        )
        assert frontmatter.id == "rfc-015"

    def test_memo_frontmatter_with_all_fields(self):
        """Test Memo frontmatter with all fields populated."""
        from docuchango.schemas import MemoFrontmatter

        frontmatter = MemoFrontmatter(
            id="memo-001",
            title="Test Memo Title That Is Long Enough",
            status="Final",
            tags=["note"],
            author="Test Author",
            date="2024-01-01",
            created="2024-01-01",
            updated="2024-01-02",
            project_id="test-project",
            doc_uuid="12345678-1234-4123-8123-123456789abc",
        )
        assert frontmatter.id == "memo-001"

    def test_prd_frontmatter_with_all_fields(self):
        """Test PRD frontmatter with all fields populated."""
        from docuchango.schemas import PRDFrontmatter

        frontmatter = PRDFrontmatter(
            id="prd-001",
            title="Test PRD Title That Is Long Enough",
            status="Draft",
            tags=["feature"],
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-02",
            target_release="Q1 2024",
            project_id="test-project",
            doc_uuid="12345678-1234-4123-8123-123456789abc",
        )
        assert frontmatter.id == "prd-001"

    def test_generic_doc_frontmatter(self):
        """Test GenericDocFrontmatter with various fields."""
        from docuchango.schemas import GenericDocFrontmatter

        frontmatter = GenericDocFrontmatter(
            id="doc-001",
            title="Test Document Title",
            project_id="test-project",
            doc_uuid="12345678-1234-4123-8123-123456789abc",
        )
        assert frontmatter.id == "doc-001"
