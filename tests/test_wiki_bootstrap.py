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


@pytest.mark.parametrize("kind", ["file", "directory", "dangling"])
def test_force_rejects_destination_symlinks_without_writes(tmp_path, kind):
    root = tmp_path / "docs-cms"
    root.mkdir()
    (root / "AGENTS.md").write_bytes(b"Existing rules\n")
    if kind == "directory":
        (root / "local").mkdir()
        (root / "local/page.md").write_bytes(b"Unrelated page\n")
        (root / "templates").symlink_to("local", target_is_directory=True)
    else:
        if kind == "file":
            (root / "local.txt").write_bytes(b"Unrelated content\n")
        (root / "README.md").symlink_to("local.txt")

    def snapshot():
        return {
            str(file.relative_to(root)): ("link", str(file.readlink()))
            if file.is_symlink()
            else ("file", file.read_bytes())
            if file.is_file()
            else ("directory", None)
            for file in root.rglob("*")
        }

    before = snapshot()
    result = bootstrap(tmp_path, "--force")
    assert result.exit_code == 1
    assert "Destination symlinks are not supported" in result.output
    assert snapshot() == before


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


@pytest.mark.parametrize("custom_types", [False, True])
def test_overlay_preserves_numbered_layout_and_validates_both(tmp_path, custom_types):
    root = tmp_path / "docs-cms"
    result = CliRunner().invoke(main, ["init", "--path", str(root), "--project-id", "existing-app"])
    assert result.exit_code == 0, result.output
    config_path = root / "docs-project.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["readability"] = {"enabled": False}
    if custom_types:
        config["structure"]["doc_types"] = {
            "rfc": {"schema": "rfc", "folders": ["rfcs"], "scan_subfolders": True, "report_numbering_gaps": True}
        }
    config_path.write_text(yaml.safe_dump(config))
    rfc = frontmatter.load(root / "templates/rfc-000-template.md")
    rfc["id"] = "rfc-001"
    rfc["title"] = "Existing system proposal"
    rfc["project_id"] = "existing-app"
    rfc["created"] = "2026-10-16"
    rfc["tags"] = ["design"]
    rfc.content = "# RFC-001: Existing system proposal\n\nAn existing proposal."
    rfc_path = root / "rfcs/rfc-001-existing-system.md"
    rfc_path.write_text(frontmatter.dumps(rfc) + "\n", newline="\n")
    rules = frontmatter.Post("# Existing rules\n\nPreserve existing instructions.")
    rules.metadata = {
        "title": "Existing rules",
        "project_id": "existing-app",
        "doc_uuid": "3a5b59f7-b738-4b2e-a5e0-1e8cf9bc5829",
        "created": "2026-10-16",
        "tags": ["documentation"],
    }
    (root / "AGENTS.md").write_text(frontmatter.dumps(rules) + "\n", newline="\n")
    before = {file: file.read_bytes() for file in root.rglob("*") if file.is_file() and file != config_path}

    result = bootstrap(tmp_path, "--overlay")

    assert result.exit_code == 0, result.output
    updated = yaml.safe_load(config_path.read_text())
    assert updated.pop("subprojects") == [{"path": "wiki/docs-project.yaml"}]
    assert updated == config
    assert all(file.read_bytes() == content for file, content in before.items())
    child = yaml.safe_load((root / "wiki/docs-project.yaml").read_text())
    assert child["project"]["id"] == "existing-app"
    assert "../../services/auth/docs" in (root / "wiki/README.md").read_text()
    validator = DocValidator(repo_root=tmp_path)
    validator.scan_documents()
    assert rfc_path in validator.file_to_doc
    assert root / "wiki/pages/getting-started.md" in validator.file_to_doc
    result = CliRunner().invoke(main, ["validate", "--repo-root", str(tmp_path), "--dry-run", "--skip-build"])
    assert result.exit_code == 0, result.output

    before_rerun = {file: file.read_bytes() for file in root.rglob("*") if file.is_file()}
    result = bootstrap(tmp_path, "--overlay")
    assert result.exit_code == 1
    assert "already registered" in result.output
    assert before_rerun == {file: file.read_bytes() for file in root.rglob("*") if file.is_file()}

    rfc["status"] = "Invalid"
    rfc_path.write_text(frontmatter.dumps(rfc) + "\n", newline="\n")
    result = CliRunner().invoke(main, ["validate", "--repo-root", str(tmp_path), "--dry-run", "--skip-build"])
    assert result.exit_code == 1
    assert "status" in result.output
    assert "Input should be" in result.output


@pytest.mark.parametrize("conflict", ["missing-config", "invalid-config", "existing-wiki", "file-wiki"])
def test_overlay_conflicts_preserve_existing_tree(tmp_path, conflict):
    root = tmp_path / "docs-cms"
    root.mkdir()
    if conflict != "missing-config":
        (root / "docs-project.yaml").write_text(
            "project: [" if conflict == "invalid-config" else "project: {id: existing, name: Existing}\n"
        )
    if conflict == "existing-wiki":
        (root / "wiki").mkdir()
        (root / "wiki/README.md").write_text("Existing wiki\n")
    elif conflict == "file-wiki":
        (root / "wiki").write_text("Existing file\n")
    before = {file: file.read_bytes() for file in root.rglob("*") if file.is_file()}
    result = bootstrap(tmp_path, "--overlay")
    assert result.exit_code == 1
    assert before == {file: file.read_bytes() for file in root.rglob("*") if file.is_file()}


@pytest.mark.parametrize(
    "args", [["--overlay"], ["--wiki", "--overlay", "--force"], ["--wiki", "--overlay", "--project-id", "other"]]
)
def test_overlay_rejects_conflicting_options(args):
    result = CliRunner().invoke(main, ["bootstrap", *args])
    assert result.exit_code == 2


def test_overlay_retains_other_subproject_registrations(tmp_path):
    root = tmp_path / "docs-cms"
    root.mkdir()
    config = {"project": {"id": "existing", "name": "Existing"}, "subprojects": ["other/docs-project.yaml"]}
    (root / "docs-project.yaml").write_text(yaml.safe_dump(config))
    result = bootstrap(tmp_path, "--overlay")
    assert result.exit_code == 0, result.output
    updated = yaml.safe_load((root / "docs-project.yaml").read_text())
    assert updated["subprojects"] == ["other/docs-project.yaml", {"path": "wiki/docs-project.yaml"}]


@pytest.mark.parametrize("registration", ["wiki", "./wiki/docs-project.yaml"])
def test_overlay_rejects_preexisting_registration_without_writes(tmp_path, registration):
    root = tmp_path / "docs-cms"
    root.mkdir()
    config = {"project": {"id": "existing", "name": "Existing"}, "subprojects": [registration]}
    config_path = root / "docs-project.yaml"
    config_path.write_text(yaml.safe_dump(config))
    before = config_path.read_bytes()
    result = bootstrap(tmp_path, "--overlay")
    assert result.exit_code == 1
    assert "already registered" in result.output
    assert config_path.read_bytes() == before
    assert not (root / "wiki").exists()


def test_overlay_bundle_failure_does_not_register_or_create_wiki(tmp_path):
    root = tmp_path / "docs-cms"
    root.mkdir()
    config_path = root / "docs-project.yaml"
    config_path.write_text("project: {id: existing, name: Existing}\n")
    before = config_path.read_bytes()
    bundle = tmp_path / "bundle"
    shutil.copytree(Path(__file__).parents[1] / "docuchango/templates/wiki", bundle)
    (bundle / "docs-project.yaml").write_text("project: {id: wrong, name: Wrong}\n")
    result = bootstrap(tmp_path, "--overlay", "--template-dir", str(bundle))
    assert result.exit_code == 1
    assert "existing project's ID and name" in result.output
    assert config_path.read_bytes() == before
    assert not (root / "wiki").exists()


@pytest.mark.parametrize("mode", ["new", "force", "overlay"])
def test_bundle_schema_ancestor_collision_preserves_existing_tree(tmp_path, mode):
    bundle = tmp_path / "bundle"
    shutil.copytree(Path(__file__).parents[1] / "docuchango/templates/wiki", bundle)
    (bundle / "docs-project.schema.json").mkdir()
    (bundle / "docs-project.schema.json/notes.md").write_text("Custom bundle notes\n")
    root = tmp_path / "docs-cms"
    if mode != "new":
        root.mkdir()
        (root / "README.md").write_bytes(b"Existing home\n")
        (root / "docs-project.yaml").write_bytes(b"project: {id: existing, name: Existing}\n")
        (root / "local.txt").write_bytes(b"Unrelated content\n")

    def snapshot():
        return {
            path.relative_to(tmp_path): path.read_bytes() if path.is_file() else None for path in tmp_path.rglob("*")
        }

    before = snapshot()
    args = ["--template-dir", str(bundle)]
    if mode != "new":
        args.append(f"--{mode}")
    result = bootstrap(tmp_path, *args)
    assert result.exit_code == 1
    assert "Bundle file is also a destination ancestor: docs-project.schema.json" in result.output
    assert snapshot() == before


@pytest.mark.parametrize("service_config", [None, "directory", "docs-root"])
def test_overlay_external_pages_keep_rd_001_and_fm_010_settings(tmp_path, service_config):
    root = tmp_path / "docs-cms"
    root.mkdir()
    parent = {
        "project": {"id": "existing", "name": "Existing"},
        "readability": {"enabled": True, "flesch_reading_ease_min": 100.0},
        "security": {"allow_external_paths": True},
    }
    service = tmp_path / "services/auth"
    service.mkdir(parents=True)
    if service_config:
        parent["subprojects"] = ["../services/auth"]
        (service / "docs-project.yaml").write_text(
            yaml.safe_dump(
                {
                    "project": {"id": "service", "name": "Service"},
                    "structure": {
                        "document_folders": [],
                        "docs_roots": ["docs"] if service_config == "docs-root" else ["."],
                    },
                }
            )
        )
    (root / "docs-project.yaml").write_text(yaml.safe_dump(parent))
    result = bootstrap(tmp_path, "--overlay")
    assert result.exit_code == 0, result.output
    wiki_config_path = root / "wiki/docs-project.yaml"
    wiki_config = yaml.safe_load(wiki_config_path.read_text())
    wiki_config["security"]["allow_external_paths"] = True
    wiki_config["structure"]["doc_types"]["wiki"]["folders"].append("../../services/auth/docs")
    wiki_config_path.write_text(yaml.safe_dump(wiki_config))
    page = frontmatter.load(root / "wiki/templates/page.md")
    page["tags"] = ["wiki"]
    page.content = (
        "# Authentication\n\n"
        + (
            "Interdisciplinary authentication orchestration necessitates comprehensive "
            "cryptographic interoperability throughout heterogeneous infrastructure. "
        )
        * 5
    )
    page_path = service / "docs/operations/authentication.md"
    page_path.parent.mkdir(parents=True)
    page_path.write_text(frontmatter.dumps(page) + "\n", newline="\n")

    validator = DocValidator(repo_root=tmp_path)
    validator.scan_documents()
    assert page_path in validator.file_to_doc
    context = validator._config_context_for_path(page_path)
    assert context is not None and context.config.project.id == "existing", "FM-010: use the wiki registration"
    settings = validator._readability_config_for(page_path)
    assert settings is not None and not settings.enabled, "RD-001: retain wiki readability settings"
    result = CliRunner().invoke(main, ["validate", "--repo-root", str(tmp_path), "--dry-run", "--skip-build"])
    assert result.exit_code == 0, result.output

    wiki_config["security"]["allow_external_paths"] = False
    wiki_config_path.write_text(yaml.safe_dump(wiki_config))
    blocked = DocValidator(repo_root=tmp_path)
    blocked.scan_documents()
    assert page_path not in blocked.file_to_doc
    settings = blocked._readability_config_for(page_path)
    assert settings is not None and settings.enabled, "RD-001: blocked folders must not claim ownership"
