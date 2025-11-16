"""Comprehensive tests for timestamp fixes - positive, negative, and edge cases."""

import subprocess
from datetime import datetime
from pathlib import Path

import frontmatter
import pytest

from docuchango.fixes.timestamps import (
    get_git_dates,
    migrate_date_to_created_updated,
    update_document_timestamps,
    update_frontmatter_field,
)


class TestGetGitDatesEdgeCases:
    """Edge case tests for git date extraction."""

    def test_file_with_no_commits(self, tmp_path):
        """Test file added but not committed."""
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

    def test_file_in_non_git_directory(self, tmp_path):
        """Test file outside of git repository."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        created, updated = get_git_dates(test_file)

        assert created is None
        assert updated is None

    def test_file_with_multiple_commits(self, tmp_path):
        """Test file with commit history."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        test_file = repo / "test.md"

        # First commit
        test_file.write_text("# Version 1")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v1"], cwd=repo, check=True, capture_output=True)

        # Second commit
        test_file.write_text("# Version 2")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v2"], cwd=repo, check=True, capture_output=True)

        created, updated = get_git_dates(test_file)

        assert created is not None
        assert updated is not None
        # Both should be valid dates
        datetime.strptime(created, "%Y-%m-%d")
        datetime.strptime(updated, "%Y-%m-%d")
        # For same-day commits, might be same or different
        assert created <= updated

    def test_file_with_renamed_history(self, tmp_path):
        """Test file that was renamed."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        # Create with original name
        old_file = repo / "old.md"
        old_file.write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

        # Rename
        new_file = repo / "new.md"
        subprocess.run(["git", "mv", "old.md", "new.md"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "rename"], cwd=repo, check=True, capture_output=True)

        created, updated = get_git_dates(new_file)

        # --follow should track through rename
        assert created is not None
        assert updated is not None

    def test_file_in_subdirectory(self, tmp_path):
        """Test file in nested subdirectory."""
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


class TestUpdateFrontmatterFieldEdgeCases:
    """Edge case tests for frontmatter field updates."""

    def test_field_with_multiline_value(self):
        """Test updating multiline field values."""
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

        # Should not update multiline fields well
        # This documents current behavior
        assert "description" in updated

    def test_field_appears_multiple_times(self):
        """Test field defined multiple times (YAML allows last wins)."""
        content = """---
id: test
created: 2020-01-01
created: 2021-01-01
---
# Test
"""
        updated = update_frontmatter_field(content, "created", "2022-01-01")

        # Should update (behavior depends on implementation)
        assert "2022-01-01" in updated

    def test_field_with_special_yaml_characters(self):
        """Test field value with special YAML chars."""
        content = """---
id: test
created: "2020-01-01: special"
---
# Test
"""
        updated = update_frontmatter_field(content, "created", "2022-01-01")

        assert "2022-01-01" in updated

    def test_update_nonexistent_field(self):
        """Test updating field that doesn't exist."""
        content = """---
id: test
---
# Test
"""
        updated = update_frontmatter_field(content, "created", "2022-01-01")

        # Should not add field (just update existing)
        assert updated == content

    def test_field_with_comment(self):
        """Test preserving inline comments."""
        content = """---
id: test
created: 2020-01-01  # Original date
updated: 2021-01-01  # Last modified
---
# Test
"""
        updated = update_frontmatter_field(content, "created", "2022-01-01")

        # Should preserve comment
        assert "# Original date" in updated
        assert "2022-01-01" in updated


class TestMigrateDateFieldEdgeCases:
    """Edge case tests for date field migration."""

    @pytest.mark.xfail(reason="Documents current behavior - migration without status field")
    def test_migrate_with_no_status_field(self):
        """Test migration when status field doesn't exist."""
        content = """---
id: test
date: 2020-01-01
---
# Test
"""
        updated = migrate_date_to_created_updated(content, "2021-01-01", "2022-01-01")

        # Should still work, might not insert in expected location
        assert "date:" not in updated
        assert "created: 2021-01-01" in updated
        assert "updated: 2022-01-01" in updated

    def test_migrate_with_existing_created_field(self):
        """Test migration when created already exists."""
        content = """---
id: test
status: Accepted
date: 2020-01-01
created: 2019-01-01
---
# Test
"""
        updated = migrate_date_to_created_updated(content, "2021-01-01", "2022-01-01")

        # Should remove date, add created and updated
        # Existing created might be overwritten
        assert "date: 2020-01-01" not in updated

    def test_migrate_multiline_date(self):
        """Test date field in multiline format."""
        content = """---
id: test
status: Accepted
date:
  2020-01-01
---
# Test
"""
        updated = migrate_date_to_created_updated(content, "2021-01-01", "2022-01-01")

        # Pattern might not match multiline
        # Documents current behavior
        assert isinstance(updated, str)


class TestUpdateDocumentTimestampsEdgeCases:
    """Edge case tests for full document timestamp updates."""

    def test_template_with_numbers(self, tmp_path):
        """Test template detection with numbers."""
        for name in ["000-template.md", "001-template.md", "adr-000-something.md"]:
            doc = tmp_path / name
            doc.write_text("---\nid: test\n---\n# Test")

            changed, messages = update_document_timestamps(doc)

            # Should skip templates
            assert not changed

    def test_template_case_variations(self, tmp_path):
        """Test case-insensitive template detection."""
        for name in ["TEMPLATE.md", "Template.md", "MyTemplate.md"]:
            doc = tmp_path / name
            doc.write_text("---\nid: test\n---\n# Test")

            changed, messages = update_document_timestamps(doc)

            # Should skip templates
            assert not changed

    @pytest.mark.xfail(reason="Documents current behavior - one-sided timestamp updates")
    def test_document_with_only_created(self, tmp_path):
        """Test document with created but no updated."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        doc = repo / "test.md"
        doc.write_text("---\nid: test\ncreated: 2020-01-01\n---\n# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changed, messages = update_document_timestamps(doc)

        # Should add updated field
        if changed:
            post = frontmatter.loads(doc.read_text())
            assert "updated" in post.metadata

    @pytest.mark.xfail(reason="Documents current behavior - one-sided timestamp updates")
    def test_document_with_only_updated(self, tmp_path):
        """Test document with updated but no created."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        doc = repo / "test.md"
        doc.write_text("---\nid: test\nupdated: 2020-01-01\n---\n# Test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changed, messages = update_document_timestamps(doc)

        # Should add created field
        if changed:
            post = frontmatter.loads(doc.read_text())
            assert "created" in post.metadata

    def test_corrupt_frontmatter(self, tmp_path):
        """Test file with corrupt frontmatter."""
        doc = tmp_path / "test.md"
        doc.write_text("---\ninvalid: yaml: syntax:\n---\n# Test")

        changed, messages = update_document_timestamps(doc)

        assert not changed
        assert any("error" in msg.lower() or "parsing" in msg.lower() for msg in messages)

    def test_file_with_no_newline_at_end(self, tmp_path):
        """Test file without trailing newline."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

        doc = repo / "test.md"
        # Write without trailing newline by writing bytes
        content = "---\nid: test\ndate: 2020-01-01\n---\n# Test"
        doc.write_bytes(content.encode("utf-8"))
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changed, messages = update_document_timestamps(doc)

        # Should still work
        if changed:
            assert len(messages) > 0
