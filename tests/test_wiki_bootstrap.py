"""Wiki bundles work through the CLI and the existing generic validator."""

import shutil
from pathlib import Path

import frontmatter
import pytest
import yaml
from click.testing import CliRunner

from docuchango.cli import main
from docuchango.validator import DocValidator


def bootstrap(root, *args):
    return CliRunner().invoke(main, ["bootstrap", "--wiki", "--path", str(root / "docs-cms"), *args])


def test_wiki_bootstrap_validates_and_extends_into_system_folders(tmp_path):
    result = bootstrap(tmp_path, "--project-id", "example", "--project-name", "Example: Wiki")
    assert result.exit_code == 0, result.output
    root = tmp_path / "docs-cms"
    assert not (root / "adr").exists()
    config_path = root / "docs-project.yaml"
    config = yaml.safe_load(config_path.read_text())
    assert config["project"]["name"] == "Example: Wiki"
    config["structure"]["doc_types"]["wiki"]["folders"].append("../services/auth/docs")
    config["security"]["allow_external_paths"] = True
    config_path.write_text(yaml.safe_dump(config))
    system = tmp_path / "services/auth/docs"
    system.mkdir(parents=True)
    page = frontmatter.load(root / "templates/page.md")
    page["doc_uuid"] = "2e42edc4-de71-482c-b792-e5adf6780329"
    page.content += "\n\n[Wiki home](../../../docs-cms/README.md)\n"
    (system / "authentication.md").write_text(frontmatter.dumps(page) + "\n")
    validator = DocValidator(repo_root=tmp_path)
    validator.scan_documents()
    assert system / "authentication.md" in validator.file_to_doc
    assert all(not doc.doc_id for doc in validator.documents)
    result = CliRunner().invoke(main, ["validate", "--repo-root", str(tmp_path), "--dry-run", "--skip-build"])
    assert result.exit_code == 0, result.output


def test_wiki_bundle_override_and_overwrite_policy(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(Path(__file__).parents[1] / "docuchango/templates/wiki", bundle)
    (bundle / "templates/INITIALIZE.md").write_text("# Custom initialization\n\nInspect {{project_name}}.\n")
    result = bootstrap(tmp_path, "--template-dir", str(bundle), "--project-name", "Custom")
    assert result.exit_code == 0, result.output
    prompt = tmp_path / "docs-cms/templates/INITIALIZE.md"
    assert "Inspect Custom." in prompt.read_text()
    before = prompt.read_bytes()
    assert bootstrap(tmp_path).exit_code == 1
    assert prompt.read_bytes() == before
    unrelated = tmp_path / "docs-cms/local.txt"
    unrelated.write_text("preserve")
    assert bootstrap(tmp_path, "--force").exit_code == 0
    assert unrelated.read_text() == "preserve"


def test_invalid_bundle_writes_nothing(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "README.md").write_text("# Missing required files\n")
    result = bootstrap(tmp_path, "--template-dir", str(bundle))
    assert result.exit_code == 1
    assert "missing required files" in result.output
    assert not (tmp_path / "docs-cms").exists()


@pytest.mark.parametrize("conflict", ["templates", "pages"])
def test_force_rejects_file_ancestors_without_changing_existing_tree(tmp_path, conflict):
    root = tmp_path / "docs-cms"
    root.mkdir()
    for name in ("README.md", "docs-project.yaml", "local.txt", conflict):
        (root / name).write_bytes(f"Original {name}\n".encode())
    before = {file.relative_to(root): file.read_bytes() for file in root.rglob("*") if file.is_file()}

    result = bootstrap(tmp_path, "--force")

    assert result.exit_code == 1
    assert "Destination ancestor is not a directory:" in result.output
    assert str(root / conflict) in result.output
    assert {file.relative_to(root): file.read_bytes() for file in root.rglob("*") if file.is_file()} == before
    assert set(root.rglob("*")) == {root / name for name in before}


def test_generated_bundle_uses_lf_on_windows(tmp_path, monkeypatch):
    original_open = Path.open

    def windows_open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        # Reproduce Windows text-mode newline translation on every test platform.
        if "w" in mode and "b" not in mode and newline is None:
            newline = "\r\n"
        return original_open(self, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(Path, "open", windows_open)
    result = bootstrap(tmp_path)
    assert result.exit_code == 0, result.output
    for file in (tmp_path / "docs-cms").rglob("*"):
        if file.is_file():
            assert b"\r" not in file.read_bytes(), file
    result = CliRunner().invoke(main, ["validate", "--repo-root", str(tmp_path), "--dry-run", "--skip-build"])
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    ("filename", "content"),
    [("docs-project.yaml", "project: ["), ("docs-project.yaml", "version: '1'"), ("README.md", "{{unknown}}")],
)
def test_bundle_render_and_config_errors_write_nothing(tmp_path, filename, content):
    bundle = tmp_path / "bundle"
    shutil.copytree(Path(__file__).parents[1] / "docuchango/templates/wiki", bundle)
    (bundle / filename).write_text(content)
    result = bootstrap(tmp_path, "--template-dir", str(bundle))
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert not (tmp_path / "docs-cms").exists()


def test_default_wiki_has_unique_metadata_and_validates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["bootstrap", "--wiki"])
    assert result.exit_code == 0, result.output
    files = [tmp_path / "docs-cms" / name for name in ("AGENTS.md", "pages/getting-started.md", "templates/page.md")]
    assert len({frontmatter.load(file)["doc_uuid"] for file in files}) == 3
    before = {file: file.read_bytes() for file in files}
    result = CliRunner().invoke(main, ["validate", "--skip-build"])
    assert result.exit_code == 0, result.output
    assert before == {file: file.read_bytes() for file in files}


@pytest.mark.parametrize("args", [["--wiki", "--output", "guide.md"], ["--wiki", "--guide", "agent"], ["--force"]])
def test_incompatible_options(args):
    result = CliRunner().invoke(main, ["bootstrap", *args])
    assert result.exit_code == 2


def test_guide_mode_unchanged():
    result = CliRunner().invoke(main, ["bootstrap"])
    assert result.exit_code == 0
    assert "wiki at" not in result.output
