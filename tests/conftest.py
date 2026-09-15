"""Pytest fixtures and test data generators for docuchango tests.

This module provides reusable fixtures and data generators for testing.
"""

import copy
import random
import string
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml

# Set fixed seed for reproducible test data
random.seed(42)


class DataGenerator:
    """Generator for deterministic test data.

    Uses a fixed seed (42) for reproducibility. All random methods will
    generate the same values across test runs, ensuring deterministic behavior.
    """

    @staticmethod
    def random_string(length: int = 10, chars: str = string.ascii_lowercase) -> str:
        """Generate a deterministic pseudo-random string."""
        return "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def random_slug(words: int = 2) -> str:
        """Generate a deterministic pseudo-random slug (e.g., 'test-doc-001')."""
        word_list = ["test", "doc", "page", "guide", "manual", "reference", "api", "cli"]
        selected = random.sample(word_list, min(words, len(word_list)))
        return "-".join(selected) + f"-{random.randint(1, 999):03d}"

    @staticmethod
    def random_uuid() -> str:
        """Generate a random UUID (uses uuid4, not affected by seed)."""
        return str(uuid.uuid4())

    @staticmethod
    def random_date(start_year: int = 2020, end_year: int = 2025) -> str:
        """Generate a deterministic pseudo-random date in YYYY-MM-DD format."""
        start = datetime(start_year, 1, 1)
        end = datetime(end_year, 12, 31)
        delta = end - start
        random_days = random.randint(0, delta.days)
        random_date = start + timedelta(days=random_days)
        return random_date.strftime("%Y-%m-%d")

    @staticmethod
    def random_title(words: int = 3) -> str:
        """Generate a random title."""
        word_list = [
            "Introduction",
            "Guide",
            "Tutorial",
            "Reference",
            "Overview",
            "Documentation",
            "Architecture",
            "Design",
            "Implementation",
            "Testing",
            "Deployment",
            "Configuration",
        ]
        return " ".join(random.sample(word_list, min(words, len(word_list))))

    @staticmethod
    def random_tag_list(count: int = 3) -> list[str]:
        """Generate a list of random tags."""
        tags = ["api", "cli", "docs", "testing", "architecture", "design", "feature", "bugfix", "enhancement"]
        return random.sample(tags, min(count, len(tags)))

    @staticmethod
    def random_status() -> str:
        """Generate a random status for ADR/RFC."""
        return random.choice(["Proposed", "Accepted", "Deprecated", "Superseded", "Draft"])

    @staticmethod
    def random_doc_type() -> str:
        """Generate a random document type."""
        return random.choice(["adr", "rfc", "guide", "tutorial", "reference"])


class MarkdownGenerator:
    """Generator for markdown content."""

    @staticmethod
    def frontmatter(
        title: str | None = None,
        doc_id: str | None = None,
        project_id: str | None = None,
        doc_uuid: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate frontmatter YAML."""
        gen = DataGenerator()
        data: dict[str, Any] = {
            "title": title or gen.random_title(),
            "id": doc_id or gen.random_slug(),
            "project_id": project_id or f"project-{gen.random_string(5)}",
            "doc_uuid": doc_uuid or gen.random_uuid(),
        }
        data.update(kwargs)

        lines = ["---"]
        for key, value in data.items():
            if isinstance(value, str):
                lines.append(f'{key}: "{value}"')
            elif isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f'  - "{item}"')
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        return "\n".join(lines)

    @staticmethod
    def code_block(language: str = "python", lines: int = 5) -> str:
        """Generate a code block."""
        gen = DataGenerator()
        code_lines = []
        for i in range(lines):
            code_lines.append(f"# Line {i + 1}: {gen.random_string(20)}")
        return f"```{language}\n" + "\n".join(code_lines) + "\n```"

    @staticmethod
    def paragraph(sentences: int = 3) -> str:
        """Generate a paragraph of lorem ipsum-style text."""
        words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit"]
        paragraph_lines = []
        for _ in range(sentences):
            sentence_words = random.sample(words * 3, random.randint(5, 15))
            sentence = " ".join(sentence_words).capitalize() + "."
            paragraph_lines.append(sentence)
        return " ".join(paragraph_lines)

    @staticmethod
    def heading(level: int = 2, text: str | None = None) -> str:
        """Generate a heading."""
        gen = DataGenerator()
        text = text or gen.random_title()
        return f"{'#' * level} {text}"

    @staticmethod
    def link(text: str | None = None, url: str | None = None) -> str:
        """Generate a markdown link."""
        gen = DataGenerator()
        text = text or gen.random_title(2)
        url = url or f"/docs/{gen.random_slug()}"
        return f"[{text}]({url})"

    @staticmethod
    def list_items(count: int = 5) -> str:
        """Generate a bulleted list."""
        gen = DataGenerator()
        lines = []
        for i in range(count):
            lines.append(f"- Item {i + 1}: {gen.random_string(20)}")
        return "\n".join(lines)

    @staticmethod
    def full_document(
        include_frontmatter: bool = True,
        include_code: bool = True,
        paragraphs: int = 3,
    ) -> str:
        """Generate a full markdown document."""
        mg = MarkdownGenerator()
        doc_parts = []

        if include_frontmatter:
            doc_parts.append(mg.frontmatter())
            doc_parts.append("")

        doc_parts.append(mg.heading(1, "Main Title"))
        doc_parts.append("")
        doc_parts.append(mg.paragraph())
        doc_parts.append("")

        for i in range(paragraphs):
            doc_parts.append(mg.heading(2, f"Section {i + 1}"))
            doc_parts.append("")
            doc_parts.append(mg.paragraph())
            doc_parts.append("")

            if include_code:
                doc_parts.append(mg.code_block())
                doc_parts.append("")

        return "\n".join(doc_parts)


@pytest.fixture
def data_gen():
    """Fixture providing a data generator instance."""
    return DataGenerator()


@pytest.fixture
def md_gen():
    """Fixture providing a markdown generator instance."""
    return MarkdownGenerator()


@pytest.fixture
def sample_frontmatter(data_gen):
    """Fixture providing sample frontmatter data."""
    return {
        "title": data_gen.random_title(),
        "id": data_gen.random_slug(),
        "project_id": f"project-{data_gen.random_string(5)}",
        "doc_uuid": data_gen.random_uuid(),
        "date": data_gen.random_date(),
        "status": data_gen.random_status(),
        "tags": data_gen.random_tag_list(),
    }


@pytest.fixture
def sample_markdown_file(tmp_path, md_gen):
    """Fixture that creates a sample markdown file."""
    file_path = tmp_path / "test_document.md"
    content = md_gen.full_document()
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def docs_repository(tmp_path, md_gen):
    """Fixture that creates a complete docs repository structure."""
    # Create directory structure
    repo_root = tmp_path / "test-repo"
    docs_cms = repo_root / "docs-cms"
    adr_dir = docs_cms / "adr"
    rfc_dir = docs_cms / "rfc"
    guides_dir = docs_cms / "guides"

    for directory in [adr_dir, rfc_dir, guides_dir]:
        directory.mkdir(parents=True)

    # Create sample documents
    for i in range(3):
        adr_file = adr_dir / f"adr-{i + 1:03d}-test.md"
        adr_file.write_text(md_gen.full_document(), encoding="utf-8")

        rfc_file = rfc_dir / f"rfc-{i + 1:03d}-test.md"
        rfc_file.write_text(md_gen.full_document(), encoding="utf-8")

        guide_file = guides_dir / f"guide-{i + 1:03d}.md"
        guide_file.write_text(md_gen.full_document(), encoding="utf-8")

    # Create config file
    config_file = docs_cms / "docs-project.yaml"
    config_content = """project:
  id: "test-project"
  name: "Test Project"
  description: "Test documentation project"

metadata:
  created: "2025-01-01"
  version: "1.0.0"

docusaurus:
  root_path: "docs-cms"
  base_url: "/docs/"
"""
    config_file.write_text(config_content, encoding="utf-8")

    return {
        "root": repo_root,
        "docs_cms": docs_cms,
        "adr_dir": adr_dir,
        "rfc_dir": rfc_dir,
        "guides_dir": guides_dir,
        "config_file": config_file,
    }


#: Canonical docs-project.yaml content shared by tests that just need a valid,
#: minimal project config rather than one exercising a specific config option.
#: Individual tests customize it via `write_docs_project_config`'s `project_id`
#: and `extra_config` arguments instead of hand-writing their own YAML.
DEFAULT_DOCS_PROJECT_CONFIG: dict[str, Any] = {
    "version": "1",
    "project": {
        "id": "test-project",
        "name": "Test Project",
        "description": "Test documentation project",
    },
    "structure": {
        "adr_dir": "adr",
        "rfc_dir": "rfcs",
        "memo_dir": "memos",
        "document_folders": ["adr", "rfcs", "memos"],
    },
    "security": {"allow_external_paths": False},
}


def write_docs_project_config(
    target_dir: Path,
    project_id: str | None = None,
    extra_config: dict[str, Any] | None = None,
) -> Path:
    """Write a canonical docs-project.yaml into `target_dir`.

    Args:
        target_dir: Directory to write docs-project.yaml into.
        project_id: Overrides just `project.id`; leave unset to keep the default
            "test-project".
        extra_config: Merged on top of the canonical defaults. A `"project"` entry
            is merged one level deep (so callers can override `id`/`name` without
            repeating `description`); every other top-level key replaces the
            default wholesale, which lets a test add config sections the
            canonical default doesn't have (e.g. `"indexes"`).

    Returns:
        The path to the written docs-project.yaml.
    """
    config = copy.deepcopy(DEFAULT_DOCS_PROJECT_CONFIG)
    if project_id is not None:
        config["project"]["id"] = project_id
    if extra_config:
        for key, value in extra_config.items():
            if key == "project" and isinstance(value, dict):
                config["project"].update(value)
            else:
                config[key] = value

    config_path = target_dir / "docs-project.yaml"
    config_path.write_text(yaml.dump(config, sort_keys=False), encoding="utf-8")
    return config_path


@pytest.fixture
def docs_tree(tmp_path):
    """Factory fixture that builds a docs folder tree plus a canonical
    docs-project.yaml, for tests that need more control than `docs_repository`
    gives (a custom root, a subset of folders, or extra config keys).

    Returns a `make(...)` callable rather than a fixed structure, since the
    project id, extra config, and folder layout needed vary per test:

        def test_something(docs_tree):
            tree = docs_tree(project_id="my-project", extra_config={"indexes": [...]})
            tree["root"]       # tmp_path / "docs-cms" by default
            tree["config_file"]  # tree["root"] / "docs-project.yaml"
    """

    def make(
        root: Path | None = None,
        folders: tuple[str, ...] = ("adr", "rfcs", "memos"),
        project_id: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Path]:
        root = root if root is not None else tmp_path / "docs-cms"
        root.mkdir(parents=True, exist_ok=True)
        for folder in folders:
            (root / folder).mkdir(parents=True, exist_ok=True)
        config_file = write_docs_project_config(root, project_id=project_id, extra_config=extra_config)
        return {"root": root, "config_file": config_file}

    return make


@pytest.fixture
def broken_markdown_samples():
    """Fixture providing various broken markdown samples for testing."""
    return {
        "missing_frontmatter": """# Title

This document has no frontmatter.
""",
        "invalid_frontmatter": """---
title: Test
this is not valid yaml
---

# Content
""",
        "trailing_whitespace": """# Title

Line with trailing spaces
Another line
""",
        "empty_code_fence": """# Title

```
code without language
```
""",
        "broken_link": """# Title

[Broken Link](/nonexistent/path)
""",
        "no_blank_before_fence": """Some text
```python
code
```
""",
        "no_blank_after_fence": """```python
code
```
Next line
""",
    }


@pytest.fixture
def valid_markdown_samples(md_gen):
    """Fixture providing valid markdown samples."""
    return {
        "with_frontmatter": md_gen.full_document(include_frontmatter=True),
        "without_frontmatter": md_gen.full_document(include_frontmatter=False),
        "with_code": md_gen.full_document(include_code=True),
        "without_code": md_gen.full_document(include_code=False, paragraphs=5),
    }
