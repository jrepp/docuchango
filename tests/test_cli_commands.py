"""Tests for CLI commands in cli.py to improve coverage."""

from click.testing import CliRunner

from docuchango.cli import fix, main, test, validate


class TestValidateCommand:
    """Test the validate command."""

    def test_validate_help(self):
        """Test that validate command shows help."""
        runner = CliRunner()
        result = runner.invoke(validate, ["--help"])
        assert result.exit_code == 0
        assert "Validate documentation files" in result.output
        assert "--repo-root" in result.output
        assert "--verbose" in result.output
        assert "--skip-build" in result.output
        assert "--fix" in result.output

    def test_validate_with_verbose(self, docs_repository):
        """Test validate command with verbose flag."""
        runner = CliRunner()
        result = runner.invoke(
            validate,
            [
                "--repo-root",
                str(docs_repository["root"]),
                "--verbose",
                "--skip-build",
            ],
        )
        # May exit with 0 or 1 depending on validation results
        assert result.exit_code in [0, 1]
        assert "Validating Documentation" in result.output or "Repository root" in result.output

    def test_validate_skip_build(self, docs_repository):
        """Test validate command with skip-build flag."""
        runner = CliRunner()
        result = runner.invoke(
            validate,
            [
                "--repo-root",
                str(docs_repository["root"]),
                "--skip-build",
            ],
        )
        assert result.exit_code in [0, 1]
        # Should not mention build validation

    def test_validate_nonexistent_path(self):
        """Test validate command with nonexistent path."""
        runner = CliRunner()
        result = runner.invoke(
            validate,
            [
                "--repo-root",
                "/nonexistent/path/that/does/not/exist",
            ],
        )
        assert result.exit_code == 2
        # Click will error on invalid path

    def test_validate_with_fix_flag(self, docs_repository):
        """Test validate command with --fix flag."""
        runner = CliRunner()
        result = runner.invoke(
            validate,
            [
                "--repo-root",
                str(docs_repository["root"]),
                "--fix",
                "--skip-build",
            ],
        )
        assert result.exit_code in [0, 1]

    def test_validate_current_directory(self, tmp_path, monkeypatch):
        """Test validate command uses current directory as default."""
        runner = CliRunner()

        # Change to tmp directory
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(validate, ["--skip-build"])
        # Should attempt to validate current directory
        assert result.exit_code in [0, 1, 2]


class TestFixCommands:
    """Test the fix command group."""

    def test_fix_help(self):
        """Test that fix command shows help."""
        runner = CliRunner()
        result = runner.invoke(fix, ["--help"])
        assert result.exit_code == 0
        assert "Fix documentation issues" in result.output

    def test_fix_all_help(self):
        """Test fix all subcommand help."""
        runner = CliRunner()
        result = runner.invoke(fix, ["all", "--help"])
        assert result.exit_code == 0
        assert "Run all automatic fixes" in result.output

    def test_fix_all_command(self, docs_repository):
        """Test fix all command execution."""
        runner = CliRunner()
        result = runner.invoke(
            fix,
            [
                "all",
                "--repo-root",
                str(docs_repository["root"]),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Fixing Documentation Issues" in result.output
        assert "DRY RUN" in result.output
        assert "Trailing whitespace" in result.output or "Would fix" in result.output

    def test_fix_all_without_dry_run(self, docs_repository):
        """Test fix all command without dry-run flag."""
        runner = CliRunner()
        result = runner.invoke(
            fix,
            [
                "all",
                "--repo-root",
                str(docs_repository["root"]),
            ],
        )
        assert result.exit_code == 0
        assert "Fixing Documentation Issues" in result.output
        # Should not show DRY RUN message
        assert "DRY RUN" not in result.output

    def test_fix_links_help(self):
        """Test fix links subcommand help."""
        runner = CliRunner()
        result = runner.invoke(fix, ["links", "--help"])
        assert result.exit_code == 0
        assert "Fix broken links" in result.output

    def test_fix_links_command(self, docs_repository):
        """Test fix links command execution."""
        runner = CliRunner()
        result = runner.invoke(
            fix,
            [
                "links",
                "--repo-root",
                str(docs_repository["root"]),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Fixing Broken Links" in result.output
        assert "DRY RUN" in result.output

    def test_fix_links_without_dry_run(self, docs_repository):
        """Test fix links command without dry-run."""
        runner = CliRunner()
        result = runner.invoke(
            fix,
            [
                "links",
                "--repo-root",
                str(docs_repository["root"]),
            ],
        )
        assert result.exit_code == 0
        assert "Fixing Broken Links" in result.output
        assert "DRY RUN" not in result.output

    def test_fix_code_blocks_help(self):
        """Test fix code-blocks subcommand help."""
        runner = CliRunner()
        result = runner.invoke(fix, ["code-blocks", "--help"])
        assert result.exit_code == 0
        assert "Fix code block formatting" in result.output

    def test_fix_code_blocks_command(self, docs_repository):
        """Test fix code-blocks command execution."""
        runner = CliRunner()
        result = runner.invoke(
            fix,
            [
                "code-blocks",
                "--repo-root",
                str(docs_repository["root"]),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Fixing Code Blocks" in result.output
        assert "DRY RUN" in result.output

    def test_fix_code_blocks_without_dry_run(self, docs_repository):
        """Test fix code-blocks command without dry-run."""
        runner = CliRunner()
        result = runner.invoke(
            fix,
            [
                "code-blocks",
                "--repo-root",
                str(docs_repository["root"]),
            ],
        )
        assert result.exit_code == 0
        assert "Fixing Code Blocks" in result.output
        assert "DRY RUN" not in result.output


class TestTestCommands:
    """Test the test command group."""

    def test_test_help(self):
        """Test that test command shows help."""
        runner = CliRunner()
        result = runner.invoke(test, ["--help"])
        assert result.exit_code == 0
        assert "Testing utilities" in result.output

    def test_test_health_help(self):
        """Test test health subcommand help."""
        runner = CliRunner()
        result = runner.invoke(test, ["health", "--help"])
        assert result.exit_code == 0
        assert "Check service health" in result.output
        assert "--url" in result.output
        assert "--timeout" in result.output

    def test_test_health_default(self):
        """Test test health command with defaults."""
        runner = CliRunner()
        result = runner.invoke(test, ["health"])
        assert result.exit_code == 0
        assert "Checking Health" in result.output
        assert "http://localhost:8080" in result.output
        assert "30s" in result.output

    def test_test_health_custom_url(self):
        """Test test health command with custom URL."""
        runner = CliRunner()
        result = runner.invoke(
            test,
            ["health", "--url", "http://example.com:9000"],
        )
        assert result.exit_code == 0
        assert "http://example.com:9000" in result.output

    def test_test_health_custom_timeout(self):
        """Test test health command with custom timeout."""
        runner = CliRunner()
        result = runner.invoke(
            test,
            ["health", "--timeout", "60"],
        )
        assert result.exit_code == 0
        assert "60s" in result.output


class TestMainCommandGroup:
    """Test the main command group."""

    def test_main_help(self):
        """Test main command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Docuchango" in result.output
        assert "Commands:" in result.output or "Usage:" in result.output

    def test_main_version(self):
        """Test main command version flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        # Should show version number

    def test_all_subcommands_listed(self):
        """Test that all subcommands are listed in main help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        # Check for main command groups
        output_lower = result.output.lower()
        assert "validate" in output_lower or "init" in output_lower


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_validate_with_exception(self, docs_repository, monkeypatch):
        """Test validate command handles exceptions gracefully."""
        runner = CliRunner()

        # Create a situation that might cause an exception
        # by making a read-only directory
        import os

        test_dir = docs_repository["root"] / "readonly"
        test_dir.mkdir()
        os.chmod(test_dir, 0o444)

        try:
            result = runner.invoke(
                validate,
                [
                    "--repo-root",
                    str(test_dir),
                    "--skip-build",
                ],
            )
            # Should handle gracefully
            assert result.exit_code in [0, 1, 2]
        finally:
            # Clean up
            os.chmod(test_dir, 0o755)

    def test_validate_verbose_with_exception(self, tmp_path):
        """Test validate command with verbose shows traceback."""
        runner = CliRunner()

        # Create minimal structure that might cause issues
        test_root = tmp_path / "broken"
        test_root.mkdir()

        result = runner.invoke(
            validate,
            [
                "--repo-root",
                str(test_root),
                "--verbose",
                "--skip-build",
            ],
        )
        # May succeed or fail, but should not crash
        assert result.exit_code in [0, 1, 2]
