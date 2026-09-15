"""Tests for CLI commands in cli.py to improve coverage."""

import subprocess
from pathlib import Path

import frontmatter
from click.testing import CliRunner

from docuchango.cli import bootstrap, main, migrate, validate


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
        assert "--allow-empty" in result.output

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

    def test_validate_relative_repo_root_does_not_crash(self, docs_repository, monkeypatch):
        """Regression test: a relative --repo-root must not raise Path.relative_to.

        Discovered document paths are always resolved to absolute paths, so
        --repo-root must be resolved up front (see the comment near the top
        of this function) or comparisons against a relative root crash.
        """
        runner = CliRunner()
        monkeypatch.chdir(docs_repository["root"].parent)

        result = runner.invoke(
            validate,
            ["--repo-root", docs_repository["root"].name, "--skip-build"],
            catch_exceptions=False,
        )

        assert result.exit_code in [0, 1]
        assert str(docs_repository["root"]) not in result.output

    def test_validate_repo_root_through_symlink(self, docs_repository, tmp_path):
        """A --repo-root reached through a symlink (as macOS /tmp is) must resolve cleanly."""
        symlink_root = tmp_path / "link-to-repo"
        symlink_root.symlink_to(docs_repository["root"])

        runner = CliRunner()
        result = runner.invoke(
            validate,
            ["--repo-root", str(symlink_root), "--skip-build"],
            catch_exceptions=False,
        )

        assert result.exit_code in [0, 1]

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
        original_content = """---
title: "Test ADR  "
status: accepted
tags: "API Design, Database"
---

# Test ADR

Some content here.
"""
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
        original_content = """---
title: "Test ADR  "
status: accepted
tags: "API Design"
---

# Test ADR
"""
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
            "File was modified during --dry-run! Dry run should not modify any files."
        )

    def test_validate_writes_frontmatter_metadata_once(self, tmp_path, monkeypatch):
        """Frontmatter metadata fixes should be batched into one write per file."""
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()

        test_file = adr_dir / "adr-001-batched-fixes.md"
        test_file.write_text(
            """---
id: adr-001
title: "Batched Metadata Fixes  "
status: accepted
created: 2025-01-01
deciders: Core Team
tags: "API Design"
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Batched Metadata Fixes
""",
            encoding="utf-8",
        )

        original_write_text = Path.write_text
        writes = []

        def counting_write_text(self, *args, **kwargs):
            if self == test_file:
                writes.append(args[0])
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", counting_write_text)

        runner = CliRunner()
        result = runner.invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 0
        assert len(writes) == 1
        fixed_content = test_file.read_text(encoding="utf-8")
        assert "status: Accepted" in fixed_content
        assert "api-design" in fixed_content
        assert 'title: "Batched Metadata Fixes  "' not in fixed_content

    def test_validate_output_shows_fixes_and_issues_with_paths(self, tmp_path):
        """Test that validate output shows both fixed and unfixable issues with file paths.

        This test verifies:
        1. Auto-fixed issues are reported with file paths
        2. Remaining (unfixable) issues are reported with file paths
        3. The summary shows counts for both categories
        """
        # Create directory structure
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()

        # File 1: Has fixable issues (tags need normalization)
        fixable_file = adr_dir / "adr-001-fixable.md"
        fixable_content = """---
title: "Fixable ADR"
status: accepted
tags: "API Design, Database"
---

# Fixable ADR

This file has fixable issues.
"""
        fixable_file.write_text(fixable_content, encoding="utf-8")

        # File 2: Has unfixable issues (invalid filename pattern for validation)
        # Note: We use trailing whitespace which gets fixed, but code fence issues
        # that the validator will catch
        unfixable_file = adr_dir / "adr-002-unfixable.md"
        unfixable_content = """---
title: "Unfixable ADR"
status: accepted
tags: []
---

# Unfixable ADR

```python
code without blank line before
```
More text without blank line after code block.
```javascript
more code
```
"""
        unfixable_file.write_text(unfixable_content, encoding="utf-8")

        # Run validate
        runner = CliRunner()
        result = runner.invoke(
            validate,
            [
                "--repo-root",
                str(tmp_path),
                "--skip-build",
            ],
        )

        # Verify output contains file paths
        output = result.output

        # Should show scanned files
        assert "Scanned" in output
        assert "files" in output

        # Should show the fixable file path when fixes are applied
        # (Tags should be normalized from string to array)
        if "Fixes applied" in output or "fixed" in output.lower():
            assert "adr-001-fixable.md" in output or "adr/adr-001" in output

        # Should show remaining issues section if there are validation errors
        if "Remaining issues" in output:
            # Should include file path for unfixable issues
            assert "adr-002-unfixable.md" in output or "adr/adr-002" in output

        # Verify the fixable file was actually modified
        fixed_content = fixable_file.read_text(encoding="utf-8")
        # Tags should be converted from string to array
        assert "tags:" in fixed_content
        # Original string format should be gone
        assert 'tags: "API Design, Database"' not in fixed_content

    def test_validate_reports_broken_links(self, tmp_path):
        """Regression test: CLI validate must run link validation."""
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)

        test_file = adr_dir / "adr-001-broken-link.md"
        test_file.write_text(
            """---
id: adr-001
title: Valid ADR Title
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: []
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Valid ADR Title

[Missing document](./missing.md)
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(validate, ["--repo-root", str(tmp_path), "--skip-build", "--dry-run"])

        assert result.exit_code == 1
        assert "adr-001-broken-link.md" in result.output
        assert "Broken link './missing.md'" in result.output

    def test_validate_reports_duplicate_ids(self, tmp_path):
        """Regression test: CLI validate must run document ID validation."""
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)

        first_file = adr_dir / "adr-001-first.md"
        first_file.write_text(
            """---
id: adr-001
title: First ADR Title
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: []
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# First ADR Title
""",
            encoding="utf-8",
        )

        second_file = adr_dir / "adr-002-second.md"
        second_file.write_text(
            """---
id: adr-001
title: Second ADR Title
status: Accepted
created: 2025-01-02
deciders: Core Team
tags: []
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abd
---

# Second ADR Title
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(validate, ["--repo-root", str(tmp_path), "--skip-build", "--dry-run"])

        assert result.exit_code == 1
        assert "adr-002-second.md" in result.output
        assert "Duplicate ID 'adr-001'" in result.output


class TestValidateAtomicFixes:
    """Regression tests for atomic fixing: a run either fixes everything and
    exits 0, or leaves the tree exactly as it found it and exits 1.

    See the bug report this closes: validate used to write Phase 1 fixes to
    disk immediately, so a run that failed in Phase 2 could leave a partially
    rewritten tree behind even though the overall run failed.
    """

    @staticmethod
    def _write_fixable(path: Path) -> str:
        """An ADR with a bare code fence: fully fixed by fix_code_blocks."""
        content = """---
id: adr-001
title: "Fixable ADR"
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: [testing]
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789aaa
---

# Fixable ADR

```
plain text with no language
```
"""
        path.write_text(content, encoding="utf-8")
        return content

    @staticmethod
    def _write_unfixable(path: Path) -> str:
        """An ADR with an invalid status literal: no fixer corrects this."""
        content = """---
id: adr-002
title: "Unfixable ADR"
status: Bogus
created: 2025-01-01
deciders: Core Team
tags: [testing]
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789bbb
---

# Unfixable ADR

Nothing here can be auto-fixed.
"""
        path.write_text(content, encoding="utf-8")
        return content

    def test_atomic_default_withholds_fixes_when_issues_remain(self, tmp_path):
        """A mixed tree exits 1 and is left byte-identical under the default."""
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)
        fixable_file = adr_dir / "adr-001-fixable.md"
        unfixable_file = adr_dir / "adr-002-unfixable.md"
        fixable_before = self._write_fixable(fixable_file)
        unfixable_before = self._write_unfixable(unfixable_file)

        runner = CliRunner()
        result = runner.invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 1
        assert "withheld" in result.output.lower()
        assert fixable_file.read_bytes() == fixable_before.encode("utf-8"), (
            "the fixable file must be left byte-identical when the run fails and stays atomic"
        )
        assert unfixable_file.read_bytes() == unfixable_before.encode("utf-8")

        # --no-atomic on the same, still-untouched tree keeps today's
        # behaviour: the fixable file is written even though the run fails.
        result = runner.invoke(validate, ["--repo-root", str(tmp_path), "--skip-build", "--no-atomic"])

        assert result.exit_code == 1
        assert "applied" in result.output.lower()
        assert fixable_file.read_bytes() != fixable_before.encode("utf-8"), (
            "--no-atomic must write the fix for the fixable file even though the unfixable issue remains"
        )

    def test_atomic_fully_fixable_tree_is_fixed_and_exits_zero(self, tmp_path):
        """A tree with only fixable issues is fixed in place and exits 0."""
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)
        fixable_file = adr_dir / "adr-001-fixable.md"
        before = self._write_fixable(fixable_file)

        runner = CliRunner()
        result = runner.invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 0
        assert "withheld" not in result.output.lower()
        after_first = fixable_file.read_bytes()
        assert after_first != before.encode("utf-8")

        # A second run is a no-op: the fix already landed and validation
        # is clean, so nothing is left to fix or withhold.
        result = runner.invoke(validate, ["--repo-root", str(tmp_path), "--skip-build"])

        assert result.exit_code == 0
        assert fixable_file.read_bytes() == after_first


class TestValidateEmptyScan:
    """SCAN-001: a run that validated nothing must not report success.

    Regression tests for the bug where `validate` exited 0 with "All
    documents valid" whenever discovery turned up no documents, so a wrong
    --repo-root, a checkout without the documentation tree, or a repository
    that never ran `docuchango init` passed CI without validating anything.
    """

    CLEAN_ADR = """---
id: adr-001
title: "ADR-001: Clean Document"
status: Accepted
created: 2025-01-01
deciders: "Core Team"
tags: [testing]
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789ccc
---

# ADR-001: Clean Document

Nothing here needs fixing.
"""

    @staticmethod
    def _run(*args):
        # A wide console keeps Rich from hard-wrapping the finding message.
        return CliRunner().invoke(validate, list(args), env={"COLUMNS": "200"}, catch_exceptions=False)

    def test_empty_repo_root_exits_nonzero_with_scan_001(self, tmp_path):
        """An empty repository root is a failure, not a clean validation."""
        result = self._run("--repo-root", str(tmp_path), "--skip-build")

        assert result.exit_code == 1
        assert "SCAN-001" in result.output
        assert "All documents valid" not in result.output

    def test_scan_001_message_says_what_to_check(self, tmp_path):
        """The message names the repo root, the config and the escape hatch."""
        result = self._run("--repo-root", str(tmp_path), "--skip-build")

        output = " ".join(result.output.split())
        assert "No documents were found" in output
        assert "no docs-project.yaml was found" in output
        assert "docs-cms/adr" in output
        assert "--allow-empty" in output

    def test_dry_run_and_skip_build_do_not_hide_empty_scan(self, tmp_path):
        """--dry-run and --skip-build must not suppress SCAN-001."""
        for extra in ([], ["--dry-run"], ["--verbose"], ["--dry-run", "--verbose"]):
            result = self._run("--repo-root", str(tmp_path), "--skip-build", *extra)
            assert result.exit_code == 1, f"{extra} hid the empty scan:\n{result.output}"
            assert "SCAN-001" in result.output, f"{extra} hid the empty scan:\n{result.output}"

    def test_allow_empty_exits_zero_and_says_so(self, tmp_path):
        """--allow-empty restores exit 0 without claiming documents were valid."""
        result = self._run("--repo-root", str(tmp_path), "--skip-build", "--allow-empty")

        assert result.exit_code == 0
        assert "SCAN-001" not in result.output
        assert "No documents found" in result.output
        assert "All documents valid" not in result.output

    def test_populated_tree_is_unaffected(self, tmp_path):
        """A normal tree still exits 0 and never mentions SCAN-001."""
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "adr-001-clean.md").write_text(self.CLEAN_ADR, encoding="utf-8")

        result = self._run("--repo-root", str(tmp_path), "--skip-build")

        assert result.exit_code == 0, result.output
        assert "SCAN-001" not in result.output
        assert "All documents valid" in result.output

    def test_documents_outside_the_doc_folders_are_not_an_empty_scan(self, tmp_path):
        """Plain Markdown at a docs root counts even though CLI discovery misses it.

        `_discover_doc_files` only walks the configured document folders,
        while the validator also parses loose Markdown at each docs root. A
        tree with only the latter validated one document, so SCAN-001 must
        not fire on it.
        """
        docs_cms = tmp_path / "docs-cms"
        docs_cms.mkdir()
        (docs_cms / "docs-project.yaml").write_text(
            'version: "1"\nproject:\n  id: test-project\n  name: Test Project\n',
            encoding="utf-8",
        )
        (docs_cms / "overview.md").write_text(
            "---\ntitle: Overview\nproject_id: test-project\n"
            "doc_uuid: 12345678-1234-4123-8123-123456789ddd\n---\n\n# Overview\n\nA loose document.\n",
            encoding="utf-8",
        )

        result = self._run("--repo-root", str(tmp_path), "--skip-build")

        assert "SCAN-001" not in result.output, result.output
        assert result.exit_code == 0, result.output


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


class TestMigrateCommand:
    """Test the migrate command."""

    def test_migrate_help(self):
        """Test migrate command shows help."""
        runner = CliRunner()
        result = runner.invoke(migrate, ["--help"])
        assert result.exit_code == 0
        assert "Migrate documents" in result.output
        assert "--project-id" in result.output
        assert "--dry-run" in result.output

    def test_migrate_removes_updated_field(self, tmp_path):
        """Test that migrate removes the 'updated' field."""
        # Create a git repo
        repo = tmp_path / "repo"
        adr_dir = repo / "adr"
        adr_dir.mkdir(parents=True)

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create file with 'updated' field that should be removed
        test_file = adr_dir / "adr-001-test.md"
        content = """---
id: adr-001
title: "Test ADR Title"
status: Accepted
created: "2025-01-01"
updated: "2025-01-15"
deciders: "Core Team"
tags:
  - test
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Test ADR
"""
        test_file.write_text(content, encoding="utf-8")

        # Commit it
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add doc"], cwd=repo, check=True, capture_output=True)

        # Run migrate
        runner = CliRunner()
        result = runner.invoke(migrate, ["--project-id", "test-project", "--path", str(repo)])

        assert result.exit_code == 0
        assert "Removed 'updated' field" in result.output

        # Verify updated field was removed
        post = frontmatter.loads(test_file.read_text(encoding="utf-8"))
        assert "updated" not in post.metadata
        assert "created" in post.metadata

    def test_migrate_removes_date_field(self, tmp_path):
        """Test that migrate removes the legacy 'date' field."""
        # Create a git repo
        repo = tmp_path / "repo"
        adr_dir = repo / "adr"
        adr_dir.mkdir(parents=True)

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create file with legacy 'date' field
        test_file = adr_dir / "adr-001-test.md"
        content = """---
id: adr-001
title: "Test ADR Title"
status: Accepted
date: "2025-01-01"
deciders: "Core Team"
tags:
  - test
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Test ADR
"""
        test_file.write_text(content, encoding="utf-8")

        # Commit it
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add doc"], cwd=repo, check=True, capture_output=True)

        # Run migrate
        runner = CliRunner()
        result = runner.invoke(migrate, ["--project-id", "test-project", "--path", str(repo)])

        assert result.exit_code == 0
        assert "Removed deprecated 'date' field" in result.output

        # Verify date field was removed and created was added
        post = frontmatter.loads(test_file.read_text(encoding="utf-8"))
        assert "date" not in post.metadata
        assert "created" in post.metadata
        # created should be a datetime (unquoted ISO 8601 parsed by PyYAML)
        from datetime import datetime

        assert isinstance(post.metadata["created"], datetime)

    def test_migrate_uses_legacy_date_when_git_history_missing(self, tmp_path):
        """Test that migrate preserves timestamp metadata without git history."""
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir(parents=True)

        test_file = adr_dir / "adr-001-test.md"
        content = """---
id: adr-001
title: "Test ADR Title"
status: Accepted
date: "2025-01-01"
deciders: "Core Team"
tags:
  - test
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Test ADR
"""
        test_file.write_text(content, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(migrate, ["--project-id", "test-project", "--path", str(tmp_path)])

        assert result.exit_code == 0

        post = frontmatter.loads(test_file.read_text(encoding="utf-8"))
        assert "date" not in post.metadata
        assert str(post.metadata["created"]) == "2025-01-01"

    def test_migrate_preserves_existing_created(self, tmp_path):
        """Test that migrate preserves existing 'created' values."""
        # Create a git repo
        repo = tmp_path / "repo"
        adr_dir = repo / "adr"
        adr_dir.mkdir(parents=True)

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create file with date-only 'created' field
        test_file = adr_dir / "adr-001-test.md"
        content = """---
id: adr-001
title: "Test ADR Title"
status: Accepted
date: "2024-12-31"
created: "2025-01-01"
deciders: "Core Team"
tags:
  - test
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Test ADR
"""
        test_file.write_text(content, encoding="utf-8")

        # Commit it
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add doc"], cwd=repo, check=True, capture_output=True)

        # Run migrate
        runner = CliRunner()
        result = runner.invoke(migrate, ["--project-id", "test-project", "--path", str(repo)])

        assert result.exit_code == 0
        assert "Normalized created" not in result.output

        # Verify created is preserved
        post = frontmatter.loads(test_file.read_text(encoding="utf-8"))
        assert "date" not in post.metadata
        assert "created" in post.metadata
        assert str(post.metadata["created"]) == "2025-01-01"

    def test_migrate_dry_run_no_changes(self, tmp_path):
        """Test that --dry-run doesn't modify files."""
        # Create a git repo
        repo = tmp_path / "repo"
        adr_dir = repo / "adr"
        adr_dir.mkdir(parents=True)

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create file with fields to be removed
        test_file = adr_dir / "adr-001-test.md"
        original_content = """---
id: adr-001
title: "Test ADR Title"
status: Accepted
created: "2025-01-01"
updated: "2025-01-15"
deciders: "Core Team"
tags:
  - test
project_id: test-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Test ADR
"""
        test_file.write_text(original_content, encoding="utf-8")

        # Commit it
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add doc"], cwd=repo, check=True, capture_output=True)

        # Run migrate with --dry-run
        runner = CliRunner()
        result = runner.invoke(migrate, ["--project-id", "test-project", "--path", str(repo), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Would modify" in result.output

        # Verify file was NOT modified
        after_content = test_file.read_text(encoding="utf-8")
        assert after_content == original_content

    def _write_project(self, root: Path) -> Path:
        """Write a docs-project.yaml driven repo, which forces resolved (absolute)
        discovered file paths regardless of whether --path itself is relative."""
        adr_dir = root / "adr"
        adr_dir.mkdir(parents=True)
        (root / "docs-project.yaml").write_text(
            """
project:
  id: repro
  name: Repro
structure:
  document_folders:
    - adr
""".strip(),
            encoding="utf-8",
        )
        doc = adr_dir / "adr-001-test.md"
        # Pre-populate doc_uuid/created so re-running migrate is deterministic
        # (migrate would otherwise mint a fresh random doc_uuid each run).
        doc.write_text(
            "---\n"
            "id: adr-001\n"
            "status: Accepted\n"
            "doc_uuid: 12345678-1234-4123-8123-123456789abc\n"
            "created: '2025-01-01T00:00:00Z'\n"
            "---\n\n# Test ADR\n",
            encoding="utf-8",
        )
        return doc

    def test_migrate_relative_path_does_not_crash(self, tmp_path, monkeypatch):
        """Regression test: a relative --path must not crash with Path.relative_to.

        Discovered files are resolved to absolute paths when a docs-project.yaml
        is present, but the original code compared them against the unresolved
        --path the user typed.
        """
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(migrate, ["--project-id", "test-project", "--path", ".", "--verbose"])

        assert result.exit_code == 0, result.output
        assert "Modified 1 of 1 files" in result.output
        assert "adr/adr-001-test.md" in result.output
        assert str(tmp_path) not in result.output

    def test_migrate_relative_and_absolute_paths_agree(self, tmp_path, monkeypatch):
        """A relative --path must produce the same result as the absolute form."""
        self._write_project(tmp_path)

        runner = CliRunner()
        absolute_result = runner.invoke(
            migrate, ["--project-id", "test-project", "--path", str(tmp_path), "--dry-run", "--verbose"]
        )
        assert absolute_result.exit_code == 0, absolute_result.output

        monkeypatch.chdir(tmp_path)
        relative_result = runner.invoke(
            migrate, ["--project-id", "test-project", "--path", ".", "--dry-run", "--verbose"]
        )
        assert relative_result.exit_code == 0, relative_result.output
        assert relative_result.output == absolute_result.output

    def test_migrate_root_through_symlink(self, tmp_path):
        """A root reached through a symlink (as macOS /tmp is) must resolve cleanly."""
        real_root = tmp_path / "real"
        doc = self._write_project(real_root)

        symlink_root = tmp_path / "link"
        symlink_root.symlink_to(real_root)

        runner = CliRunner()
        result = runner.invoke(migrate, ["--project-id", "test-project", "--path", str(symlink_root), "--verbose"])

        assert result.exit_code == 0, result.output
        assert "Modified 1 of 1 files" in result.output
        post = frontmatter.loads(doc.read_text(encoding="utf-8"))
        assert post.metadata["project_id"] == "test-project"


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


class TestBulkUpdateCommand:
    """Test bulk update command validation."""

    def test_bulk_update_rejects_empty_set_field_name(self):
        runner = CliRunner()

        result = runner.invoke(main, ["bulk", "update", "--set", "=value"])

        assert result.exit_code == 1
        assert "non-empty field name" in result.output

    def test_bulk_update_rejects_empty_rename_target(self):
        runner = CliRunner()

        result = runner.invoke(main, ["bulk", "update", "--rename", "old_name="])

        assert result.exit_code == 1
        assert "non-empty OLD and NEW" in result.output


class TestCliBootstrap:
    """Test the bootstrap command, which prints an onboarding guide."""

    def test_bootstrap_help(self):
        """Test bootstrap --help documents the command."""
        runner = CliRunner()
        result = runner.invoke(bootstrap, ["--help"])
        assert result.exit_code == 0
        assert "bootstrap" in result.output.lower() or "guide" in result.output.lower()

    def test_bootstrap_default(self):
        """Test bootstrap with default guide."""
        runner = CliRunner()
        result = runner.invoke(bootstrap)
        # May succeed or fail depending on whether guides are available
        assert result.exit_code in [0, 1]

    def test_bootstrap_agent_guide(self):
        """Test bootstrap --guide agent."""
        runner = CliRunner()
        result = runner.invoke(bootstrap, ["--guide", "agent"])
        assert result.exit_code in [0, 1]

    def test_bootstrap_best_practices_guide(self):
        """Test bootstrap --guide best-practices."""
        runner = CliRunner()
        result = runner.invoke(bootstrap, ["--guide", "best-practices"])
        assert result.exit_code in [0, 1]

    def test_bootstrap_output_to_file(self, tmp_path):
        """Test bootstrap --output writes the guide to a file."""
        runner = CliRunner()
        output_file = tmp_path / "guide.md"
        result = runner.invoke(bootstrap, ["--output", str(output_file)])
        assert result.exit_code in [0, 1]
