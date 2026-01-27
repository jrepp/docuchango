"""Tests for timestamp update functionality."""

import subprocess
from datetime import datetime

import frontmatter

from docuchango.fixes.timestamps import (
    get_git_dates,
    migrate_date_to_created_updated,
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


class TestMigrateDateField:
    """Test migrating legacy 'date' field."""

    def test_migrate_date_to_created_updated(self):
        """Test migrating date field to created/updated."""
        content = """---
id: "adr-001"
title: "Test ADR"
status: Accepted
date: 2025-01-26
deciders: "Team"
---

# Test
"""
        updated = migrate_date_to_created_updated(content, "2025-01-20", "2025-01-30")

        # Check date is removed
        assert "date: 2025-01-26" not in updated

        # Check created and updated are added after status
        lines = updated.split("\n")
        status_idx = next(i for i, line in enumerate(lines) if line.startswith("status:"))
        created_idx = next(i for i, line in enumerate(lines) if line.startswith("created:"))
        updated_idx = next(i for i, line in enumerate(lines) if line.startswith("updated:"))

        assert created_idx == status_idx + 1
        assert updated_idx == status_idx + 2
        assert "created: 2025-01-20" in updated
        assert "updated: 2025-01-30" in updated


class TestUpdateDocumentTimestamps:
    """Test document timestamp updates."""

    def test_skip_template_files(self, tmp_path):
        """Test that template files are skipped."""
        template = tmp_path / "adr-000-template.md"
        template.write_text("---\nid: template\n---\n# Template")

        changed, messages = update_document_timestamps(template)

        assert not changed
        assert len(messages) == 0

    def test_skip_files_with_template_in_name(self, tmp_path):
        """Test that files with 'template' in name are skipped."""
        template = tmp_path / "my-template.md"
        template.write_text("---\nid: test\n---\n# Test")

        changed, messages = update_document_timestamps(template)

        assert not changed
        assert len(messages) == 0

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
        assert "updated" in post.metadata

    def test_update_existing_created_updated_fields(self, tmp_path):
        """Test updating existing created/updated fields."""
        # Create a git repo
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create file with old dates
        doc = repo / "adr-001-test.md"
        content = """---
id: "adr-001"
title: "Test"
status: Accepted
created: 2020-01-01
updated: 2020-01-02
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
        assert len(messages) == 2  # Both created and updated should change
        assert any("created" in msg for msg in messages)
        assert any("updated" in msg for msg in messages)

        # Verify dates were updated to today's date
        post = frontmatter.loads(doc.read_text())
        assert post.metadata["created"] != "2020-01-01"
        assert post.metadata["updated"] != "2020-01-02"

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
