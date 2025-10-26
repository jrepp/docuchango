"""Test suite for the documentation validator."""

from pathlib import Path

import pytest

from docuchango.validator import DocValidator


class TestMarkdownValidation:
    """Test markdown validation against known good and bad fixtures."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"

    def test_fixtures_exist(self, fixtures_dir):
        """Verify that test fixtures directory exists and contains files."""
        assert fixtures_dir.exists(), "Fixtures directory does not exist"
        assert (fixtures_dir / "pass").exists(), "Pass fixtures directory missing"
        assert (fixtures_dir / "fail").exists(), "Fail fixtures directory missing"

        pass_fixtures = list((fixtures_dir / "pass").glob("*.md"))
        fail_fixtures = list((fixtures_dir / "fail").glob("*.md"))

        assert len(pass_fixtures) > 0, "No passing fixtures found"
        assert len(fail_fixtures) > 0, "No failing fixtures found"

    def test_passing_fixtures(self, fixtures_dir, tmp_path):
        """Test that documents in pass directory validate successfully."""
        pass_dir = fixtures_dir / "pass"
        fixtures = list(pass_dir.glob("*.md"))

        assert len(fixtures) > 0, "No passing test fixtures found"

        for fixture_file in fixtures:
            docs_root = tmp_path / f"test_{fixture_file.stem}"

            if fixture_file.stem.startswith("adr-"):
                target_dir = docs_root / "docs-cms" / "adr"
            elif fixture_file.stem.startswith("rfc-"):
                target_dir = docs_root / "docs-cms" / "rfcs"
            elif fixture_file.stem.startswith("memo-"):
                target_dir = docs_root / "docs-cms" / "memos"
            else:
                pytest.fail(f"Unknown fixture type: {fixture_file.stem}")

            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / fixture_file.name
            target_file.write_text(fixture_file.read_text())

            validator = DocValidator(repo_root=docs_root, verbose=False)
            validator.scan_documents()
            validator.check_code_blocks()
            validator.check_formatting()

            # Collect all errors (validator-level + all document-level)
            all_errors = list(validator.errors)
            for doc in validator.documents:
                all_errors.extend(doc.errors)

            code_block_errors = [e for e in all_errors if "code block" in e.lower() or "fence" in e.lower()]
            format_errors = [e for e in all_errors if "whitespace" in e.lower()]

            assert len(code_block_errors) == 0, (
                f"Fixture {fixture_file.name} has code block errors: {code_block_errors}"
            )
            assert len(format_errors) == 0, f"Fixture {fixture_file.name} has formatting errors: {format_errors}"

    def test_failing_fixtures(self, fixtures_dir, tmp_path):
        """Test that documents in fail directory fail validation with expected errors."""
        fail_dir = fixtures_dir / "fail"
        fixtures = list(fail_dir.glob("*.md"))

        assert len(fixtures) > 0, "No failing test fixtures found"

        for fixture_file in fixtures:
            docs_root = tmp_path / f"test_{fixture_file.stem}"

            if fixture_file.stem.startswith("adr-"):
                target_dir = docs_root / "docs-cms" / "adr"
            elif fixture_file.stem.startswith("rfc-"):
                target_dir = docs_root / "docs-cms" / "rfcs"
            elif fixture_file.stem.startswith("memo-"):
                target_dir = docs_root / "docs-cms" / "memos"
            else:
                pytest.fail(f"Unknown fixture type: {fixture_file.stem}")

            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / fixture_file.name
            target_file.write_text(fixture_file.read_text())

            validator = DocValidator(repo_root=docs_root, verbose=False)
            validator.scan_documents()
            validator.check_code_blocks()
            validator.check_formatting()

            # Collect all errors (validator-level + all document-level)
            all_errors = list(validator.errors)
            for doc in validator.documents:
                all_errors.extend(doc.errors)

            assert len(all_errors) > 0, f"Fixture {fixture_file.name} should fail but passed validation"
