"""Tests for timestamp update functionality."""

import subprocess
from datetime import datetime
from pathlib import Path

import frontmatter
import pytest
from click.testing import CliRunner

from docuchango.cli import main
from docuchango.fixes.timestamps import (
    get_git_dates,
    migrate_date_to_created,
    update_document_timestamps,
    update_frontmatter_field,
)


class TestGetGitDates:
    """Test git date extraction."""

    def test_get_git_dates_for_tracked_file(self, tmp_path):
        """Test getting git dates for a file in git history."""
        # Create a git repo
        repo = tmp_path / "repo"
        repo.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create and commit a file
        test_file = repo / "test.md"
        test_file.write_text("# Test")
        subprocess.run(["git", "add", "test.md"], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        # Get dates
        created, updated = get_git_dates(test_file)

        assert created is not None
        assert updated is not None
        assert created == updated  # Only one commit
        # Check format is ISO 8601 datetime (YYYY-MM-DDTHH:MM:SSZ)
        datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")

    def test_get_git_dates_for_untracked_file(self, tmp_path):
        """Test getting git dates for a file not in git."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        created, updated = get_git_dates(test_file)

        assert created is None
        assert updated is None

    def test_added_but_uncommitted_file_has_no_dates(self, tmp_path):
        """Test a file that's been git-added but not yet committed has no dates."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        test_file = repo / "test.md"
        test_file.write_text("# Test")
        # Don't commit

        created, updated = get_git_dates(test_file)

        assert created is None
        assert updated is None

    def test_file_with_multiple_commits_has_distinct_created_and_updated(self, tmp_path):
        """Test that created/updated reflect the first and latest commit respectively."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        test_file = repo / "test.md"

        test_file.write_text("# Version 1")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v1"], cwd=repo, check=True, capture_output=True)

        test_file.write_text("# Version 2")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v2"], cwd=repo, check=True, capture_output=True)

        created, updated = get_git_dates(test_file)

        assert created is not None
        assert updated is not None
        datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
        datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")
        assert created <= updated

    def test_renamed_file_history_is_followed(self, tmp_path):
        """Test that git dates are still found for a file that was renamed (git log --follow)."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        old_file = repo / "old.md"
        old_file.write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

        new_file = repo / "new.md"
        subprocess.run(["git", "mv", "old.md", "new.md"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "rename"], cwd=repo, check=True, capture_output=True)

        created, updated = get_git_dates(new_file)

        assert created is not None
        assert updated is not None

    def test_file_in_nested_subdirectory_has_dates(self, tmp_path):
        """Test that git dates are found for files nested in subdirectories."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        subdir = repo / "docs" / "adr"
        subdir.mkdir(parents=True)

        test_file = subdir / "test.md"
        test_file.write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        created, updated = get_git_dates(test_file)

        assert created is not None
        assert updated is not None


class TestUpdateFrontmatterField:
    """Test frontmatter field updates."""

    def test_update_simple_field(self):
        """Test updating a simple field."""
        content = """---
id: "test-001"
created: 2025-01-01
updated: 2025-01-15
---

# Test
"""
        updated = update_frontmatter_field(content, "created", "2025-02-01")

        assert "created: 2025-02-01" in updated
        assert "2025-01-01" not in updated

    def test_update_field_with_comment(self):
        """Test updating a field that has a comment."""
        content = """---
id: "test-001"
created: 2025-01-01  # Original date
updated: 2025-01-15
---

# Test
"""
        updated = update_frontmatter_field(content, "created", "2025-02-01")

        assert "created: 2025-02-01  # Original date" in updated
        assert "2025-01-01" not in updated

    def test_update_nonexistent_field(self):
        """Test updating a field that doesn't exist."""
        content = """---
id: "test-001"
---

# Test
"""
        updated = update_frontmatter_field(content, "created", "2025-02-01")

        # Should return unchanged content
        assert updated == content

    def test_multiline_block_scalar_replace_leaves_dangling_continuation_lines(self):
        """update_frontmatter_field only rewrites the field's own line, so a YAML block
        scalar ('|') keeps its indented continuation lines. They fold into the new
        plain-scalar value on the next parse instead of being removed. This documents
        a real sharp edge (not a fix): callers must not use this helper on multiline
        fields, since the resulting value is corrupted rather than cleanly replaced.
        """
        content = """---
id: test
description: |
  Long
  multiline
  value
---
# Test
"""
        updated = update_frontmatter_field(content, "description", "new-value")

        assert "description: new-value" in updated
        post = frontmatter.loads(updated)
        # The dangling continuation lines fold into the value instead of disappearing.
        assert post.metadata["description"] == "new-value Long multiline value"

    def test_duplicate_yaml_key_updates_every_occurrence(self):
        """Test behavior when a key is defined twice: the regex is global, so both lines change."""
        content = """---
id: test
created: 2020-01-01
created: 2021-01-01
---
# Test
"""
        updated = update_frontmatter_field(content, "created", "2022-01-01")

        assert updated.count("created: 2022-01-01") == 2

    def test_value_containing_a_colon_is_updated(self):
        """Test updating a field whose old value contains a colon."""
        content = """---
id: test
created: "2020-01-01: special"
---
# Test
"""
        updated = update_frontmatter_field(content, "created", "2022-01-01")

        assert "2022-01-01" in updated

    def test_preserves_inline_comment_on_a_different_field(self):
        """Test that updating one field does not disturb a comment on another field."""
        content = """---
id: test
created: 2020-01-01  # Original date
updated: 2021-01-01  # Last modified
---
# Test
"""
        updated = update_frontmatter_field(content, "created", "2022-01-01")

        assert "# Original date" in updated
        assert "2022-01-01" in updated


class TestMigrateDateField:
    """Test migrating legacy 'date' field."""

    def test_migrate_date_to_created(self):
        """Test migrating date field to created."""
        content = """---
id: "adr-001"
title: "Test ADR"
status: Accepted
date: 2025-01-26
deciders: "Team"
---

# Test
"""
        result = migrate_date_to_created(content, "2025-01-20")

        # Check date is removed
        assert "date: 2025-01-26" not in result

        # Check created is added after status
        lines = result.split("\n")
        status_idx = next(i for i, line in enumerate(lines) if line.startswith("status:"))
        created_idx = next(i for i, line in enumerate(lines) if line.startswith("created:"))

        assert created_idx == status_idx + 1
        assert "created: 2025-01-20" in result
        # updated field is no longer stored (derived from git)
        assert "updated:" not in result

    def test_migrate_without_status_field_inserts_after_id(self):
        """Test that created is inserted right after 'id' when there's no 'status' field."""
        content = """---
id: test
date: 2020-01-01
---
# Test
"""
        result = migrate_date_to_created(content, "2021-01-01")

        assert "date:" not in result
        assert "created: 2021-01-01" in result
        assert "updated:" not in result

    def test_migrate_preserves_existing_created_field(self):
        """Test that migration removes 'date' but does not overwrite an existing 'created'."""
        content = """---
id: test
status: Accepted
date: 2020-01-01
created: 2019-01-01
---
# Test
"""
        result = migrate_date_to_created(content, "2021-01-01")

        assert "date: 2020-01-01" not in result
        assert result.count("created:") == 1
        assert "created: 2019-01-01" in result

    def test_migrate_multiline_date_value_leaves_dangling_continuation_line(self):
        """migrate_date_to_created's regex targets a single-line 'date:' field. A
        multiline date value leaves its indented continuation line behind, dangling
        under the newly-inserted 'created:' line. This documents current behavior,
        not a guarantee that multiline dates migrate cleanly.
        """
        content = """---
id: test
status: Accepted
date:
  2020-01-01
---
# Test
"""
        result = migrate_date_to_created(content, "2021-01-01")

        assert "created: 2021-01-01" in result
        assert "  2020-01-01" in result


class TestUpdateDocumentTimestamps:
    """Test document timestamp updates."""

    @pytest.mark.parametrize(
        "name",
        [
            pytest.param("adr-000-template.md", id="numeric-prefix-plus-template-word"),
            pytest.param("my-template.md", id="template-word-substring"),
            pytest.param("000-template.md", id="leading-000-and-template-word"),
            pytest.param("001-template.md", id="leading-001-and-template-word"),
            pytest.param("000-anything.md", id="leading-000-only"),
            pytest.param("TEMPLATE.md", id="uppercase-template"),
            pytest.param("Template.md", id="titlecase-template"),
            pytest.param("MyTemplate.md", id="titlecase-template-substring"),
        ],
    )
    def test_skip_template_files(self, tmp_path, name):
        """Test that files matching the template heuristic (contains 'template',
        case-insensitively, or starts with '000-') are skipped before any git or
        frontmatter work happens.
        """
        template = tmp_path / name
        template.write_text("---\nid: template\n---\n# Template")

        changed, messages = update_document_timestamps(template)

        assert not changed
        assert messages == []

    def test_leading_000_only_matters_at_the_start_of_the_filename(self, tmp_path):
        """A '000-' or 'template' match must be a prefix/substring of the filename itself;
        'adr-000-something.md' does not start with '000-' and doesn't contain 'template',
        so it is NOT treated as a template and is processed normally.
        """
        doc = tmp_path / "adr-000-something.md"
        doc.write_text("---\nid: test\n---\n# Test")

        changed, messages = update_document_timestamps(doc)

        # Not skipped: falls through to the (missing) git history check instead.
        assert not changed
        assert messages == ["No git history found"]

    def test_handle_missing_frontmatter(self, tmp_path):
        """Test handling files without frontmatter."""
        doc = tmp_path / "test.md"
        doc.write_text("# Test\n\nNo frontmatter here")

        changed, messages = update_document_timestamps(doc)

        assert not changed
        assert "No frontmatter found" in messages

    def test_handle_no_git_history(self, tmp_path):
        """Test handling files not in git."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\n---\n# Test")

        changed, messages = update_document_timestamps(doc)

        assert not changed
        assert "No git history found" in messages

    def test_migrate_legacy_date_field(self, tmp_path):
        """Test migrating legacy 'date' field."""
        # Create a git repo
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create file with legacy date field
        doc = repo / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test"
status: Accepted
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)

        # Commit it
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add doc"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        # Update timestamps
        changed, messages = update_document_timestamps(doc)

        assert changed
        assert any("Migrated" in msg for msg in messages)

        # Verify migration
        post = frontmatter.loads(doc.read_text())
        assert "date" not in post.metadata
        assert "created" in post.metadata
        # updated field is no longer stored (derived from git)
        assert "updated" not in post.metadata

    def test_remove_legacy_date_when_created_exists(self, tmp_path):
        """Test removing deprecated date while preserving existing created."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        doc = repo / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test"
status: Accepted
date: 2025-01-26
created: 2020-01-01
---

# Test
"""
        doc.write_text(content)

        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add doc"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        changed, messages = update_document_timestamps(doc)

        assert changed
        assert messages == ["Removed deprecated 'date' field"]

        post = frontmatter.loads(doc.read_text())
        assert "date" not in post.metadata
        assert str(post.metadata["created"]) == "2020-01-01"

    def test_preserve_existing_created_without_git_history(self, tmp_path):
        """Test existing created does not require git history."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\ncreated: 2020-01-01\n---\n# Test")

        changed, messages = update_document_timestamps(doc)

        assert not changed
        assert messages == []

    def test_migrate_legacy_date_without_git_history(self, tmp_path):
        """Test legacy date can be migrated without git history."""
        doc = tmp_path / "test.md"
        doc.write_text("---\nid: test\ndate: 2020-01-01\n---\n# Test")

        changed, messages = update_document_timestamps(doc)

        assert changed
        assert messages == ["Migrated 'date' → 'created'"]

        post = frontmatter.loads(doc.read_text())
        assert "date" not in post.metadata
        assert str(post.metadata["created"]) == "2020-01-01"

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry run doesn't write changes."""
        # Create a git repo
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create file
        doc = repo / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test"
status: Accepted
date: 2025-01-26
---

# Test
"""
        doc.write_text(content)
        original_content = content

        # Commit it
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add doc"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        # Update with dry run
        changed, messages = update_document_timestamps(doc, dry_run=True)

        assert changed
        assert len(messages) > 0
        # Content should be unchanged
        assert doc.read_text() == original_content

    @pytest.mark.parametrize(
        "extra_frontmatter",
        [
            pytest.param("status: Accepted\n", id="with-status-field"),
            pytest.param("", id="without-status-field"),
        ],
    )
    def test_existing_created_field_is_never_overwritten(self, tmp_path, extra_frontmatter):
        """Test that a document with a pre-existing 'created' field is left untouched,
        with or without a 'status' field alongside it.
        """
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        doc = repo / "test.md"
        doc.write_text(f"---\nid: test\n{extra_frontmatter}created: 2020-01-01\n---\n# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changed, messages = update_document_timestamps(doc)

        assert not changed
        assert messages == []
        post = frontmatter.loads(doc.read_text())
        assert str(post.metadata["created"]) == "2020-01-01"
        assert "updated" not in post.metadata

    def test_document_with_status_but_no_date_or_created_gets_created_added(self, tmp_path):
        """Test that a committed document with neither 'date' nor 'created' gets one added
        (not a migration path, since there's no legacy 'date' field to migrate)."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        doc = repo / "test.md"
        doc.write_text("---\nid: test\nstatus: Draft\n---\n# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changed, messages = update_document_timestamps(doc)

        assert changed
        post = frontmatter.loads(doc.read_text())
        assert "created" in post.metadata
        assert "updated" not in post.metadata

    def test_created_field_is_inserted_right_after_id_when_no_status(self, tmp_path):
        """Test that a newly-added 'created' field is placed immediately after 'id'."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        doc = repo / "test.md"
        doc.write_text("---\nid: test\n---\n# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changed, _ = update_document_timestamps(doc)

        assert changed
        lines = doc.read_text().splitlines()
        id_idx = next(i for i, line in enumerate(lines) if line.startswith("id:"))
        created_idx = next(i for i, line in enumerate(lines) if line.startswith("created:"))
        assert created_idx == id_idx + 1

    def test_corrupt_frontmatter_reports_a_parse_error(self, tmp_path):
        """Test that invalid YAML in frontmatter is reported as an error, not raised."""
        doc = tmp_path / "test.md"
        doc.write_text("---\ninvalid: yaml: syntax:\n---\n# Test")

        changed, messages = update_document_timestamps(doc)

        assert not changed
        assert any("error" in msg.lower() or "parsing" in msg.lower() for msg in messages)

    def test_file_without_trailing_newline_still_migrates(self, tmp_path):
        """Test that a file lacking a trailing newline can still be migrated successfully."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        doc = repo / "test.md"
        content = "---\nid: test\ndate: 2020-01-01\n---\n# Test"
        doc.write_bytes(content.encode("utf-8"))
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changed, messages = update_document_timestamps(doc)

        assert changed
        assert messages == ["Migrated 'date' → 'created'"]


class TestBulkTimestampsCliRelativePath:
    """Regression tests for `docuchango bulk timestamps --path` with a relative root.

    Discovered files under a docs-project.yaml driven root are always
    resolved to absolute paths, so the CLI must resolve the user-supplied
    --path up front or later Path.relative_to(root) calls can raise/degrade.
    """

    def _write_project(self, root: Path) -> Path:
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
        doc.write_text("---\nid: adr-001\nstatus: Draft\ndate: 2020-01-01\n---\n# Test\n", encoding="utf-8")

        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=root, check=True, capture_output=True)
        return doc

    def test_relative_path_does_not_crash_and_shows_relative_output(self, tmp_path, monkeypatch):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(main, ["bulk", "timestamps", "--path", ".", "--verbose"])

        assert result.exit_code == 0, result.output
        assert "Modified 1 of 1 files" in result.output
        assert "adr/adr-001-test.md" in result.output
        assert str(tmp_path) not in result.output

    def test_relative_and_absolute_paths_agree(self, tmp_path, monkeypatch):
        self._write_project(tmp_path)

        absolute_result = CliRunner().invoke(
            main, ["bulk", "timestamps", "--path", str(tmp_path), "--dry-run", "--verbose"]
        )
        assert absolute_result.exit_code == 0, absolute_result.output

        monkeypatch.chdir(tmp_path)
        relative_result = CliRunner().invoke(main, ["bulk", "timestamps", "--path", ".", "--dry-run", "--verbose"])
        assert relative_result.exit_code == 0, relative_result.output
        assert relative_result.output == absolute_result.output

    def test_root_through_symlink(self, tmp_path):
        """A root reached through a symlink (as macOS /tmp is) must resolve cleanly."""
        real_root = tmp_path / "real"
        doc = self._write_project(real_root)

        symlink_root = tmp_path / "link"
        symlink_root.symlink_to(real_root)

        result = CliRunner().invoke(main, ["bulk", "timestamps", "--path", str(symlink_root), "--verbose"])

        assert result.exit_code == 0, result.output
        assert "Modified 1 of 1 files" in result.output
        post = frontmatter.loads(doc.read_text(encoding="utf-8"))
        assert "date" not in post.metadata
        assert "created" in post.metadata
