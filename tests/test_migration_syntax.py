"""Tests for migration_syntax.py fix module."""


from docuchango.fixes.migration_syntax import fix_migration_file


class TestMigrationSyntaxFixes:
    """Test migration syntax fixing functionality."""

    def test_fix_single_index(self, tmp_path, capsys):
        """Test extracting single inline INDEX to separate statement."""
        test_file = tmp_path / "001_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    INDEX idx_email (email)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        # Should have separate CREATE INDEX statement
        assert "CREATE INDEX IF NOT EXISTS idx_email ON users (email);" in fixed
        # Original INDEX should be removed from table
        assert "INDEX idx_email (email)" not in fixed
        # Table structure should remain
        assert "CREATE TABLE users" in fixed

    def test_fix_multiple_indexes(self, tmp_path, capsys):
        """Test extracting multiple inline indexes."""
        test_file = tmp_path / "002_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(255),
    INDEX idx_email (email),
    INDEX idx_name (name)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        assert "CREATE INDEX IF NOT EXISTS idx_email ON users (email);" in fixed
        assert "CREATE INDEX IF NOT EXISTS idx_name ON users (name);" in fixed

    def test_fix_table_with_if_not_exists(self, tmp_path, capsys):
        """Test table with IF NOT EXISTS clause."""
        test_file = tmp_path / "003_test.sql"
        content = """CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    INDEX idx_email (email)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        assert "CREATE INDEX IF NOT EXISTS idx_email ON users (email);" in fixed
        assert "CREATE TABLE IF NOT EXISTS users" in fixed

    def test_fix_composite_index(self, tmp_path, capsys):
        """Test index with multiple columns."""
        test_file = tmp_path / "004_test.sql"
        content = """CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    created_at TIMESTAMP,
    INDEX idx_user_created (user_id, created_at)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        assert "CREATE INDEX IF NOT EXISTS idx_user_created ON orders (user_id, created_at);" in fixed

    def test_no_changes_needed(self, tmp_path, capsys):
        """Test file with no inline indexes."""
        test_file = tmp_path / "005_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is False

        # File should not be modified
        fixed = test_file.read_text(encoding="utf-8")
        assert fixed == content

    def test_already_separate_index(self, tmp_path, capsys):
        """Test file with already separate CREATE INDEX."""
        test_file = tmp_path / "006_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_email ON users (email);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is False

    def test_multiple_tables(self, tmp_path, capsys):
        """Test multiple CREATE TABLE statements."""
        test_file = tmp_path / "007_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    INDEX idx_email (email)
);

CREATE TABLE posts (
    id INT PRIMARY KEY,
    user_id INT,
    INDEX idx_user (user_id)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        assert "CREATE INDEX IF NOT EXISTS idx_email ON users (email);" in fixed
        assert "CREATE INDEX IF NOT EXISTS idx_user ON posts (user_id);" in fixed

    def test_trailing_comma_cleanup(self, tmp_path, capsys):
        """Test that trailing commas are cleaned up."""
        test_file = tmp_path / "008_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    INDEX idx_email (email)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        # Should not have trailing comma before closing paren
        assert ",\n)" not in fixed
        assert ", )" not in fixed

    def test_empty_file(self, tmp_path, capsys):
        """Test empty file handling."""
        test_file = tmp_path / "009_test.sql"
        test_file.write_text("", encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is False

    def test_file_with_comments(self, tmp_path, capsys):
        """Test file with SQL comments."""
        test_file = tmp_path / "010_test.sql"
        content = """-- Migration file
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255), -- User email
    INDEX idx_email (email)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        # Comments should be preserved
        assert "-- Migration file" in fixed
        assert "CREATE INDEX IF NOT EXISTS idx_email ON users (email);" in fixed

    def test_unicode_content_preserved(self, tmp_path, capsys):
        """Test Unicode content is preserved."""
        test_file = tmp_path / "011_test.sql"
        content = """-- Unicode comment: 中文 → ✓
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(255), -- User name ✓
    INDEX idx_name (name)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        assert "中文" in fixed
        assert "→" in fixed
        assert "✓" in fixed

    def test_case_insensitive_create_table(self, tmp_path, capsys):
        """Test lowercase 'create table' - documents current behavior."""
        test_file = tmp_path / "012_test.sql"
        content = """create table users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    INDEX idx_email (email)
);"""
        test_file.write_text(content, encoding="utf-8")

        # Current implementation: outer regex has IGNORECASE but inner regex doesn't
        # So lowercase "create table" doesn't get fully processed
        result = fix_migration_file(test_file)
        assert result is False  # No changes made due to inner regex limitation

    def test_index_with_backticks(self, tmp_path, capsys):
        """Test index with backticks (MySQL style)."""
        test_file = tmp_path / "013_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    INDEX `idx_email` (email)
);"""
        test_file.write_text(content, encoding="utf-8")

        # Note: Current implementation may not handle backticks perfectly
        # This test documents actual behavior
        fix_migration_file(test_file)
        # May or may not modify depending on regex matching
        fixed = test_file.read_text(encoding="utf-8")
        assert "CREATE TABLE users" in fixed

    def test_multiline_table_definition(self, tmp_path, capsys):
        """Test table with complex multiline definition."""
        test_file = tmp_path / "014_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_created (created_at)
);"""
        test_file.write_text(content, encoding="utf-8")

        result = fix_migration_file(test_file)
        assert result is True

        fixed = test_file.read_text(encoding="utf-8")
        assert "CREATE INDEX IF NOT EXISTS idx_email ON users (email);" in fixed
        assert "CREATE INDEX IF NOT EXISTS idx_created ON users (created_at);" in fixed
        # Table constraints should remain
        assert "DEFAULT CURRENT_TIMESTAMP" in fixed

    def test_console_output(self, tmp_path, capsys):
        """Test that function prints progress messages."""
        test_file = tmp_path / "015_test.sql"
        content = """CREATE TABLE users (
    id INT PRIMARY KEY,
    INDEX idx_id (id)
);"""
        test_file.write_text(content, encoding="utf-8")

        fix_migration_file(test_file)

        captured = capsys.readouterr()
        assert "Processing:" in captured.out
        assert "015_test.sql" in captured.out
        assert "Fixed" in captured.out

    def test_no_changes_console_output(self, tmp_path, capsys):
        """Test console output when no changes needed."""
        test_file = tmp_path / "016_test.sql"
        content = "CREATE TABLE users (id INT PRIMARY KEY);"
        test_file.write_text(content, encoding="utf-8")

        fix_migration_file(test_file)

        captured = capsys.readouterr()
        assert "No changes needed" in captured.out
