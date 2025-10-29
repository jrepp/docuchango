"""Test suite for the init command."""

import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from docuchango.cli import main


class TestInitCommand:
    """Test the init command functionality."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    def test_init_default_location(self, runner, tmp_path):
        """Test init command with default location."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])

            # Print output for debugging if test fails
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")
                    import traceback

                    traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

            assert result.exit_code == 0
            assert "Successfully initialized docs-cms" in result.output

            # Check folder structure
            docs_cms = Path("docs-cms")
            assert docs_cms.exists()
            assert (docs_cms / "adr").exists()
            assert (docs_cms / "rfcs").exists()
            assert (docs_cms / "memos").exists()
            assert (docs_cms / "prd").exists()
            assert (docs_cms / "templates").exists()

            # Check files
            assert (docs_cms / "docs-project.yaml").exists()
            assert (docs_cms / "README.md").exists()
            assert (docs_cms / "templates" / "adr-000-template.md").exists()
            assert (docs_cms / "templates" / "rfc-000-template.md").exists()
            assert (docs_cms / "templates" / "memo-000-template.md").exists()
            assert (docs_cms / "templates" / "prd-000-template.md").exists()

    def test_init_custom_path(self, runner, tmp_path):
        """Test init command with custom path."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            custom_path = Path("my-custom-docs")
            result = runner.invoke(main, ["init", "--path", str(custom_path)])

            assert result.exit_code == 0
            assert f"Successfully initialized docs-cms at {custom_path}" in result.output

            # Check folder structure in custom location
            assert custom_path.exists()
            assert (custom_path / "adr").exists()
            assert (custom_path / "rfcs").exists()
            assert (custom_path / "memos").exists()
            assert (custom_path / "prd").exists()
            assert (custom_path / "templates").exists()

    def test_init_custom_project_info(self, runner, tmp_path):
        """Test init command with custom project ID and name."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                main,
                [
                    "init",
                    "--project-id",
                    "test-app",
                    "--project-name",
                    "Test Application",
                ],
            )

            assert result.exit_code == 0

            # Check that docs-project.yaml has custom values
            config_path = Path("docs-cms") / "docs-project.yaml"
            assert config_path.exists()

            content = config_path.read_text()
            assert "id: test-app" in content
            assert "name: Test Application" in content
            assert "description: Documentation for Test Application" in content

    def test_init_sets_current_date(self, runner, tmp_path):
        """Test that init command sets creation date to today."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])

            assert result.exit_code == 0

            config_path = Path("docs-cms") / "docs-project.yaml"
            content = config_path.read_text()

            # Check that today's date is in the config
            today = datetime.date.today().isoformat()
            assert f'created: "{today}"' in content

    def test_init_existing_directory_without_force(self, runner, tmp_path):
        """Test that init fails on existing non-empty directory without --force."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First initialization
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0

            # Try to initialize again without --force
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 1
            assert "Directory already exists" in result.output
            assert "Use --force to overwrite" in result.output

    def test_init_with_force_overwrites(self, runner, tmp_path):
        """Test that init with --force overwrites existing files."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First initialization
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0

            # Modify a file to verify it gets overwritten
            config_path = Path("docs-cms") / "docs-project.yaml"
            config_path.write_text("modified content")

            # Initialize again with --force
            result = runner.invoke(main, ["init", "--force"])
            assert result.exit_code == 0
            assert "Successfully initialized docs-cms" in result.output

            # Check that file was overwritten (no longer has modified content)
            content = config_path.read_text()
            assert "modified content" not in content
            assert "project:" in content

    def test_init_help(self, runner):
        """Test that init --help shows correct information."""
        result = runner.invoke(main, ["init", "--help"])

        assert result.exit_code == 0
        assert "Initialize a new docs-cms folder structure" in result.output
        assert "--path" in result.output
        assert "--project-id" in result.output
        assert "--project-name" in result.output
        assert "--force" in result.output

    def test_init_template_content_validity(self, runner, tmp_path):
        """Test that generated templates have valid content."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0

            templates_dir = Path("docs-cms") / "templates"

            # Check ADR template
            adr_template = templates_dir / "adr-000-template.md"
            adr_content = adr_template.read_text()
            assert "---" in adr_content  # Has frontmatter
            assert "title:" in adr_content
            assert "status:" in adr_content
            assert "# Context" in adr_content
            assert "# Decision" in adr_content
            assert "# Consequences" in adr_content

            # Check RFC template
            rfc_template = templates_dir / "rfc-000-template.md"
            rfc_content = rfc_template.read_text()
            assert "---" in rfc_content
            assert "# Summary" in rfc_content
            assert "# Motivation" in rfc_content
            assert "# Detailed Design" in rfc_content

            # Check Memo template
            memo_template = templates_dir / "memo-000-template.md"
            memo_content = memo_template.read_text()
            assert "---" in memo_content
            assert "# Overview" in memo_content
            assert "# Context" in memo_content

            # Check PRD template
            prd_template = templates_dir / "prd-000-template.md"
            prd_content = prd_template.read_text()
            assert "---" in prd_content
            assert "# Executive Summary" in prd_content
            assert "# Problem Statement" in prd_content
            assert "# Requirements" in prd_content

    def test_init_readme_content(self, runner, tmp_path):
        """Test that README has helpful content."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0

            readme = Path("docs-cms") / "README.md"
            readme_content = readme.read_text()

            assert "# Documentation CMS" in readme_content
            assert "## Directory Structure" in readme_content
            assert "ADR" in readme_content
            assert "RFC" in readme_content
            assert "Memo" in readme_content
            assert "PRD" in readme_content
            assert "docuchango validate" in readme_content

    def test_init_docs_project_yaml_structure(self, runner, tmp_path):
        """Test that docs-project.yaml has correct structure."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0

            config_path = Path("docs-cms") / "docs-project.yaml"
            content = config_path.read_text()

            # Check for main sections
            assert "project:" in content
            assert "structure:" in content
            assert "metadata:" in content

            # Check structure fields
            assert "adr_dir: adr" in content
            assert "rfc_dir: rfcs" in content
            assert "memo_dir: memos" in content
            assert "prd_dir: prd" in content
            assert "document_folders:" in content

            # Check document_folders list
            assert "- adr" in content
            assert "- rfcs" in content
            assert "- memos" in content
            assert "- prd" in content

    def test_init_creates_empty_folders(self, runner, tmp_path):
        """Test that all required folders are created even when empty."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0

            docs_cms = Path("docs-cms")

            # All folders should exist
            assert (docs_cms / "adr").is_dir()
            assert (docs_cms / "rfcs").is_dir()
            assert (docs_cms / "memos").is_dir()
            assert (docs_cms / "prd").is_dir()
            assert (docs_cms / "templates").is_dir()

            # Content folders should be empty
            assert len(list((docs_cms / "adr").iterdir())) == 0
            assert len(list((docs_cms / "rfcs").iterdir())) == 0
            assert len(list((docs_cms / "memos").iterdir())) == 0
            assert len(list((docs_cms / "prd").iterdir())) == 0

            # Templates folder should have files
            assert len(list((docs_cms / "templates").iterdir())) == 4

    def test_init_absolute_path(self, runner, tmp_path):
        """Test init with absolute path."""
        custom_path = tmp_path / "absolute-docs"
        result = runner.invoke(main, ["init", "--path", str(custom_path)])

        assert result.exit_code == 0
        assert custom_path.exists()
        assert (custom_path / "docs-project.yaml").exists()

    def test_init_nested_path(self, runner, tmp_path):
        """Test init creates parent directories if needed."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            nested_path = Path("level1") / "level2" / "docs"
            result = runner.invoke(main, ["init", "--path", str(nested_path)])

            assert result.exit_code == 0
            assert nested_path.exists()
            assert (nested_path / "docs-project.yaml").exists()

    def test_init_project_id_validation_in_yaml(self, runner, tmp_path):
        """Test that project-id is properly sanitized in YAML."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                main,
                ["init", "--project-id", "my-awesome-project", "--project-name", "My Awesome Project"],
            )

            assert result.exit_code == 0

            config_path = Path("docs-cms") / "docs-project.yaml"
            content = config_path.read_text()

            assert "id: my-awesome-project" in content
            assert "name: My Awesome Project" in content

    def test_init_output_messages(self, runner, tmp_path):
        """Test that init provides clear output messages."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])

            assert result.exit_code == 0

            # Check for key messages
            assert "Initializing docs-cms structure" in result.output
            assert "Created: adr/" in result.output
            assert "Created: rfcs/" in result.output
            assert "Created: memos/" in result.output
            assert "Created: prd/" in result.output
            assert "Created: templates/" in result.output
            assert "Copying templates..." in result.output
            assert "Successfully initialized" in result.output
            assert "Next steps:" in result.output
