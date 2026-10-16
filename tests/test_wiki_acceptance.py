"""Run wiki content regressions through a separate CLI process on real files."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests/fixtures/findings"
CASES = sorted(path for path in FIXTURES.iterdir() if "wiki" in path.name and (path / "expected.yaml").is_file())
pytestmark = pytest.mark.integration


def run_cli(root, *args):
    # Use this checkout with the test interpreter even when cwd is a disposable
    # repository. No Click runner, validator imports, mocks, or shell involved.
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "NO_COLOR": "1", "COLUMNS": "240"}
    result = subprocess.run(
        [sys.executable, "-m", "docuchango", *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, " ".join((result.stdout + result.stderr).split())


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


@pytest.mark.parametrize("fixture", CASES, ids=lambda path: path.name)
def test_wiki_content_detect_fix_revalidate(fixture, tmp_path):
    """Verify failure, exact repaired bytes, a clean recheck, and idempotence."""
    root = tmp_path / "wiki repository with spaces"
    shutil.copytree(fixture, root)
    expected = yaml.safe_load((root / "expected.yaml").read_text())
    (root / "expected.yaml").unlink()
    before = snapshot(root)

    code, output = run_cli(root, "validate", "--dry-run", "--skip-build")
    assert code == expected["dry_run_exit_code"], output
    for message in expected["messages"]:
        assert message in output, output
    assert snapshot(root) == before, "Dry run must not modify any file"

    code, output = run_cli(root, "validate", "--skip-build")
    assert code == expected["exit_code"], output
    for message in expected.get("fix_messages", []):
        assert message in output, output
    after = snapshot(root)
    if expected["fixed"]:
        assert expected.get("files_after"), "Repair cases must specify exact expected file contents"
        wanted = before | {path: text.encode("utf-8") for path, text in expected["files_after"].items()}
        assert after == wanted, "Only declared repairs may change the fixture tree"
        assert after != before
    else:
        assert after == before, "Report-only and withheld repairs must preserve the whole tree"

    code, output = run_cli(root, "validate", "--dry-run", "--skip-build")
    assert code == expected["exit_code"], output
    if expected["fixed"]:
        for message in expected["messages"]:
            assert message not in output, output
    else:
        for message in expected["messages"]:
            assert message in output, output
    assert snapshot(root) == after

    code, output = run_cli(root, "validate", "--skip-build")
    assert code == expected["exit_code"], output
    assert snapshot(root) == after, "A second repair run must be byte-idempotent"


def test_bootstrap_wiki_then_validate_in_separate_processes(tmp_path):
    root = tmp_path / "new repository"
    root.mkdir()
    code, output = run_cli(root, "bootstrap", "--wiki", "--project-id", "wiki-example")
    assert code == 0, output
    assert (root / "docs-cms/templates/INITIALIZE.md").is_file()
    assert (root / "docs-cms/AGENTS.md").is_file()

    # Follow the initialization workflow with real system content. Keep the
    # generated starter pages and rules to validate the combined wiki as well.
    content = FIXTURES / "_wiki-content"
    shutil.copytree(content, root, dirs_exist_ok=True)
    (root / "expected.yaml").unlink()
    before = snapshot(root)
    code, output = run_cli(root, "validate", "--dry-run", "--skip-build")
    assert code == 0, output
    code, output = run_cli(root, "validate", "--skip-build")
    assert code == 0, output
    assert snapshot(root) == before


def test_overlay_existing_rfc_layout_in_separate_processes(tmp_path):
    root = tmp_path / "existing repository"
    root.mkdir()
    code, output = run_cli(root, "init", "--project-id", "docuchango")
    assert code == 0, output
    config_path = root / "docs-cms/docs-project.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["readability"] = {"enabled": False}
    config_path.write_text(yaml.safe_dump(config), newline="\n")
    rfc = "rfcs/rfc-001-document-template-system.md"
    (root / "docs-cms" / rfc).write_text((REPO_ROOT / "docs-cms" / rfc).read_text().rstrip() + "\n", newline="\n")
    before = snapshot(root)

    code, output = run_cli(root, "bootstrap", "--wiki", "--overlay")
    assert code == 0, output
    for path, content in before.items():
        if path != "docs-cms/docs-project.yaml":
            assert (root / path).read_bytes() == content
    page = root / "docs-cms/wiki/pages/getting-started.md"
    page.write_text(page.read_text() + f"\n[Template rationale](../../{rfc})\n", newline="\n")
    after = snapshot(root)
    code, output = run_cli(root, "validate", "--dry-run", "--skip-build")
    assert code == 0, output
    code, output = run_cli(root, "validate", "--skip-build")
    assert code == 0, output
    assert snapshot(root) == after
    code, output = run_cli(root, "bootstrap", "--wiki", "--overlay")
    assert code == 1, output
    assert "already registered" in output
    assert snapshot(root) == after
