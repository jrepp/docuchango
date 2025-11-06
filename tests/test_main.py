"""Tests for __main__.py module entry point."""

import subprocess
import sys


class TestMainModule:
    """Test the __main__.py module entry point."""

    def test_main_module_callable(self):
        """Test that the module can be invoked as python -m docuchango."""
        result = subprocess.run(
            [sys.executable, "-m", "docuchango", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "docuchango" in result.stdout.lower() or "version" in result.stdout.lower()

    def test_main_module_help(self):
        """Test that the module shows help when invoked."""
        result = subprocess.run(
            [sys.executable, "-m", "docuchango", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "Usage" in result.stdout or "Commands" in result.stdout

    def test_main_module_imports_correctly(self):
        """Test that __main__.py imports and calls main correctly."""
        # Import the module to ensure it doesn't raise errors
        import docuchango.__main__  # noqa: F401

        # Verify the main function is accessible
        from docuchango.cli import main

        assert callable(main)
