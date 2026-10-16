"""Initialize a wiki from a replaceable, file-based template bundle."""

from __future__ import annotations

import datetime
import json
import re
import uuid
from importlib import resources
from pathlib import Path

import click
import yaml

from docuchango import __version__
from docuchango.schemas import DocsProjectConfig


def initialize_wiki_overlay(target: Path, template_dir: Path | None) -> None:
    """Register an isolated wiki without replacing existing document types."""
    config_path = target / "docs-project.yaml"
    wiki_root = target / "wiki"
    try:
        if config_path.is_symlink() or wiki_root.is_symlink():
            raise ValueError("Overlay config and wiki root must not be symlinks.")
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        config = DocsProjectConfig.model_validate(data)
        wiki_config_path = wiki_root / "docs-project.yaml"
        for subproject in config.subprojects:
            registered = (target / subproject.path).resolve()
            if registered in (wiki_root.resolve(), wiki_config_path.resolve()):
                raise ValueError("Wiki overlay is already registered; edit the existing wiki instead.")
        data.setdefault("subprojects", []).append({"path": "wiki/docs-project.yaml"})
        DocsProjectConfig.model_validate(data)
        updated_config = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise click.ClickException(str(exc)) from exc

    initialize_wiki(wiki_root, config.project.id, config.project.name, template_dir, force=False, overlay=True)
    config_path.write_text(updated_config, encoding="utf-8", newline="\n")


def initialize_wiki(
    target: Path, project_id: str, project_name: str, template_dir: Path | None, force: bool, *, overlay: bool = False
) -> None:
    """Render and check the whole bundle before writing any output."""
    source = template_dir or Path(str(resources.files("docuchango") / "templates" / "wiki"))
    if target.exists() and (not target.is_dir() or (any(target.iterdir()) and not force)):
        if overlay:
            raise click.ClickException(f"Wiki destination already exists: {target}. Edit the existing wiki instead.")
        raise click.ClickException(f"Directory already exists: {target}. Use --force to overwrite bundle files.")
    required = {"docs-project.yaml", "README.md", "AGENTS.md", "templates/INITIALIZE.md", "templates/page.md"}
    values = {
        "project_id": project_id,
        "project_name": project_name,
        "project_id_yaml": json.dumps(project_id),
        "project_name_yaml": json.dumps(project_name),
        "date": datetime.date.today().isoformat(),
        "version": __version__,
        "system_docs_example": "../../services/auth/docs" if overlay else "../services/auth/docs",
    }
    rendered: dict[Path, str] = {}
    try:
        for file in sorted(source.rglob("*")):
            if file.is_symlink():
                raise ValueError(f"Template symlinks are not supported: {file}")
            if not file.is_file():
                continue
            relative = file.relative_to(source)
            tokens = {**values, "doc_uuid": str(uuid.uuid4())}

            def substitute(match: re.Match[str], tokens: dict[str, str] = tokens, relative: Path = relative) -> str:
                key = match.group(1)
                if key not in tokens:
                    raise ValueError(f"Unknown template token {key!r} in {relative}")
                return tokens[key]

            rendered[relative] = re.sub(r"\{\{([a-z_]+)\}\}", substitute, file.read_text(encoding="utf-8"))
        missing = required - {p.as_posix() for p in rendered}
        if missing:
            raise ValueError(f"Wiki bundle missing required files: {', '.join(sorted(missing))}")
        bundle_config = DocsProjectConfig.model_validate(yaml.safe_load(rendered[Path("docs-project.yaml")]))
        if overlay and (bundle_config.project.id != project_id or bundle_config.project.name != project_name):
            raise ValueError("Overlay bundle must use the existing project's ID and name.")
        rendered[Path("docs-project.schema.json")] = (
            resources.files("docuchango") / "templates" / "docs-project.schema.json"
        ).read_text(encoding="utf-8")
        for relative in rendered:
            destination = target / relative
            component = destination
            while component != target:
                if component.is_symlink():
                    raise ValueError(f"Destination symlinks are not supported: {component}")
                component = component.parent
            if not destination.resolve().is_relative_to(target.resolve()):
                raise ValueError(f"Destination escapes wiki root: {destination}")
            if destination.exists() and not destination.is_file():
                raise ValueError(f"Destination is not a file: {destination}")
            for ancestor in destination.parents:
                if ancestor.exists() and not ancestor.is_dir():
                    raise ValueError(f"Destination ancestor is not a directory: {ancestor}")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise click.ClickException(str(exc)) from exc

    for relative, content in rendered.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
