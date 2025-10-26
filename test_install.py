#!/usr/bin/env python3
"""Test script to verify package installation and basic imports."""

import sys


def test_basic_imports():
    """Test that all main modules can be imported."""
    print("Testing basic imports...")

    try:
        import docuchango

        print(f"✓ docuchango imported successfully (version {docuchango.__version__})")
    except ImportError as e:
        print(f"✗ Failed to import docuchango: {e}")
        return False

    try:
        from docuchango.schemas import ADRFrontmatter, MemoFrontmatter, RFCFrontmatter  # noqa: F401

        print("✓ Schemas imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import schemas: {e}")
        return False

    try:
        from docuchango.testing import AGFAssertions, AGFCLIRunner, HealthChecker  # noqa: F401

        print("✓ Testing framework imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import testing framework: {e}")
        return False

    try:
        from docuchango.cli import main  # noqa: F401

        print("✓ CLI imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import CLI: {e}")
        return False

    return True


def test_schemas():
    """Test that schemas work correctly."""
    print("\nTesting schemas...")

    from datetime import date

    from docuchango.schemas import ADRFrontmatter

    try:
        # Test valid ADR frontmatter
        adr = ADRFrontmatter(
            title="Test ADR Title",
            status="Proposed",
            date=date(2025, 1, 1),
            deciders="Test Team",
            tags=["test", "architecture"],
            id="adr-001",
            project_id="test-project",
            doc_uuid="12345678-1234-4123-8123-123456789abc",
        )
        print(f"✓ ADR schema validation works: {adr.title}")
        return True
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        return False


def test_cli_help():
    """Test that CLI help works."""
    print("\nTesting CLI help...")

    from click.testing import CliRunner

    from docuchango.cli import main

    try:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        if result.exit_code == 0:
            print("✓ CLI help command works")
            return True
        else:
            print(f"✗ CLI help failed with exit code {result.exit_code}")
            return False
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Docuchango Package Verification")
    print("=" * 60)

    all_passed = True

    if not test_basic_imports():
        all_passed = False

    if not test_schemas():
        all_passed = False

    if not test_cli_help():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
