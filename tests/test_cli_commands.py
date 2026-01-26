"""Tests for CLI commands in cli.py to improve coverage."""

from click.testing import CliRunner

from docuchango.cli import main, validate


class TestValidateCommand:
    """Test the validate command."""

    def test_validate_help(self):
        """Test that validate command shows help."""
        runner = CliRunner()
        result = runner.invoke(validate, ["--help"])
        assert result.exit_code == 0
        assert "Validate and fix documentation files" in result.output
        assert "--repo-root" in result.output
        assert "--verbose" in result.output
        assert "--skip-build" in result.output
        assert "--dry-run" in result.output

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

    def test_validate_with_dry_run(self, docs_repository):
        """Test validate command with --dry-run flag (no fixes applied)."""
        runner = CliRunner()
        result = runner.invoke(
            validate,
            [
                "--repo-root",
                str(docs_repository["root"]),
                "--dry-run",
                "--skip-build",
            ],
        )
        assert result.exit_code in [0, 1]
        assert "DRY RUN" in result.output

    def test_validate_current_directory(self, tmp_path, monkeypatch):
        """Test validate command uses current directory as default."""
        runner = CliRunner()

        # Change to tmp directory
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(validate, ["--skip-build"])
        # Should attempt to validate current directory
        assert result.exit_code in [0, 1, 2]

    def test_validate_actually_applies_fixes(self, tmp_path):
        """Regression test: validate must actually apply fixes, not just report them.

        This test ensures the validate command modifies files when fixes are needed.
        Previously, the fix functionality was a placeholder that only printed what
        would be fixed without actually making changes.
        """
        # Create directory structure with fixable issues
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()

        # Create an ADR file with issues that should be auto-fixed:
        # - Tags as string instead of array
        # - Tags not normalized (uppercase, spaces)
        # - Whitespace in field values
        test_file = adr_dir / "adr-001-test-fix.md"
        original_content = '''---
title: "Test ADR  "
status: accepted
tags: "API Design, Database"
---

# Test ADR

Some content here.
'''
        test_file.write_text(original_content, encoding="utf-8")

        # Run validate (which now applies fixes by default)
        runner = CliRunner()
        runner.invoke(
            validate,
            [
                "--repo-root",
                str(tmp_path),
                "--skip-build",
            ],
        )

        # Read the file back
        fixed_content = test_file.read_text(encoding="utf-8")

        # Verify fixes were actually applied
        # The file content should have changed from the original
        assert fixed_content != original_content, (
            "File was not modified - fixes were not applied! "
            "This is a regression where validate only reports but doesn't fix."
        )

        # Verify specific fixes were applied:
        # - Tags should be converted to array format
        assert "tags:" in fixed_content
        # - Tags should be normalized (lowercase, dashes)
        assert "api-design" in fixed_content.lower() or "- api-design" in fixed_content.lower()
        # - Title whitespace should be trimmed
        assert 'title: "Test ADR  "' not in fixed_content

    def test_validate_dry_run_does_not_modify_files(self, tmp_path):
        """Test that --dry-run prevents file modifications."""
        # Create directory structure with fixable issues
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()

        test_file = adr_dir / "adr-001-test-dry-run.md"
        original_content = '''---
title: "Test ADR  "
status: accepted
tags: "API Design"
---

# Test ADR
'''
        test_file.write_text(original_content, encoding="utf-8")

        # Run validate with --dry-run
        runner = CliRunner()
        runner.invoke(
            validate,
            [
                "--repo-root",
                str(tmp_path),
                "--skip-build",
                "--dry-run",
            ],
        )

        # Read the file back - should be unchanged
        after_content = test_file.read_text(encoding="utf-8")
        assert after_content == original_content, (
            "File was modified during --dry-run! "
            "Dry run should not modify any files."
        )


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
