"""LNK-011: rewriting links that leave the repository to absolute URLs.

The rule under test is the one in RFC-003: a link that ``LNK-002`` reports --
one whose target resolves outside ``--repo-root`` -- becomes
``<project.repository_url>/<path from the repository root to the target>``,
with the anchor kept as written, and only when the target exists on disk.

The fixtures here build a tiny monorepo: a ``site/`` checkout that is the
repository root of the run, and a ``shared/`` folder one level above it that
the run can see on disk but that is outside the root, which is exactly the
shape that produces an escaping link with a real target.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from docuchango.cli import _discover_doc_claims, _repository_urls_from_claims
from docuchango.fixes.cross_plugin_links import (
    fix_cross_plugin_links,
    fix_cross_plugin_links_in_tree,
    main,
)
from docuchango.links import repository_file_url
from docuchango.schemas import DocsProjectConfig

REPOSITORY_URL = "https://github.com/acme/handbook/blob/main/site"

ADR_TEMPLATE = """---
id: adr-001
title: "ADR-001: Links Out Of The Repository"
status: Accepted
created: 2026-01-02
tags: [testing]
deciders: "Engineering Team"
project_id: fixture-project
doc_uuid: 11111111-0111-4111-8111-111111111111
---

# ADR-001: Links Out Of The Repository

{body}
"""


def _tree(tmp_path: Path, body: str, repository_url: str | None = REPOSITORY_URL) -> tuple[Path, Path]:
    """Build the site/ + shared/ monorepo and return (repo root, ADR path)."""
    glossary = tmp_path / "shared" / "reference" / "glossary.md"
    glossary.parent.mkdir(parents=True)
    glossary.write_text("# Glossary\n", encoding="utf-8")

    repo_root = tmp_path / "site"
    adr_dir = repo_root / "docs-cms" / "adr"
    adr_dir.mkdir(parents=True)

    project: dict[str, object] = {"id": "fixture-project", "name": "Fixture Project"}
    if repository_url is not None:
        project["repository_url"] = repository_url
    (repo_root / "docs-cms" / "docs-project.yaml").write_text(
        yaml.dump({"version": "1", "project": project, "structure": {"document_folders": ["adr"]}}),
        encoding="utf-8",
    )

    adr = adr_dir / "adr-001-links-out.md"
    adr.write_text(ADR_TEMPLATE.format(body=body), encoding="utf-8")
    return repo_root.resolve(), adr


class TestRepositoryFileUrl:
    """The URL construction rule, independent of any document."""

    def test_repo_relative_path_is_appended(self, tmp_path: Path) -> None:
        target = tmp_path / "docs" / "guide.md"
        assert repository_file_url("https://example.com/org/repo/blob/main", tmp_path, target) == (
            "https://example.com/org/repo/blob/main/docs/guide.md"
        )

    def test_trailing_slash_on_the_configured_url_is_stripped(self, tmp_path: Path) -> None:
        target = tmp_path / "guide.md"
        assert repository_file_url("https://example.com/org/repo/blob/main/", tmp_path, target) == (
            "https://example.com/org/repo/blob/main/guide.md"
        )

    def test_nested_target_keeps_every_segment(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c" / "deep.md"
        assert repository_file_url("https://example.com/repo", tmp_path, target) == (
            "https://example.com/repo/a/b/c/deep.md"
        )

    def test_parent_segments_are_taken_off_the_configured_url(self, tmp_path: Path) -> None:
        """A target above --repo-root consumes the tail of the URL path."""
        repo_root = tmp_path / "site"
        repo_root.mkdir()
        target = tmp_path / "shared" / "glossary.md"
        assert repository_file_url("https://example.com/org/repo/blob/main/site", repo_root, target) == (
            "https://example.com/org/repo/blob/main/shared/glossary.md"
        )

    def test_url_too_shallow_for_the_target_is_declined(self, tmp_path: Path) -> None:
        """When '../' outruns the URL path there is nothing left to address."""
        repo_root = tmp_path / "site"
        repo_root.mkdir()
        target = tmp_path / "shared" / "glossary.md"
        assert repository_file_url("https://example.com", repo_root, target) is None

    @pytest.mark.parametrize("configured", ["ssh://git.example.com/repo", "example.com/repo", "/srv/repo"])
    def test_non_http_base_is_declined(self, tmp_path: Path, configured: str) -> None:
        assert repository_file_url(configured, tmp_path, tmp_path / "x.md") is None


class TestRepositoryUrlSchema:
    """`project.repository_url` is validated when the config loads."""

    def test_absolute_http_url_is_accepted(self) -> None:
        config = DocsProjectConfig(
            project={"id": "p", "name": "P", "repository_url": "http://example.com/repo"},
        )
        assert config.project.repository_url == "http://example.com/repo"

    def test_absent_url_defaults_to_none(self) -> None:
        config = DocsProjectConfig(project={"id": "p", "name": "P"})
        assert config.project.repository_url is None

    @pytest.mark.parametrize(
        "value",
        ["git@github.com:org/repo.git", "ssh://git@example.com/repo", "github.com/org/repo", "/srv/docs", ""],
    )
    def test_non_http_url_is_rejected(self, value: str) -> None:
        with pytest.raises(ValueError, match="repository_url"):
            DocsProjectConfig(project={"id": "p", "name": "P", "repository_url": value})


class TestFixCrossPluginLinks:
    """One document at a time."""

    def test_escaping_link_is_rewritten_with_the_anchor_kept(self, tmp_path: Path) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md#terms).")

        changed, messages = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert changed
        assert messages == [
            "LNK-011: Line 14: Rewrote link '../../../shared/reference/glossary.md#terms' to "
            "'https://github.com/acme/handbook/blob/main/shared/reference/glossary.md#terms'"
        ]
        assert (
            "[glossary](https://github.com/acme/handbook/blob/main/shared/reference/glossary.md#terms)"
            in adr.read_text(encoding="utf-8")
        )

    def test_query_string_is_kept(self, tmp_path: Path) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md?plain=1).")

        fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert "glossary.md?plain=1)" in adr.read_text(encoding="utf-8")

    def test_missing_target_is_left_alone(self, tmp_path: Path) -> None:
        """A typo must not be frozen into a well-formed dead URL."""
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/missing.md).")
        before = adr.read_text(encoding="utf-8")

        changed, messages = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed
        assert messages == []
        assert adr.read_text(encoding="utf-8") == before

    def test_link_inside_a_code_fence_is_left_alone(self, tmp_path: Path) -> None:
        body = "```markdown\nSee [glossary](../../../shared/reference/glossary.md).\n```"
        repo_root, adr = _tree(tmp_path, body)
        before = adr.read_text(encoding="utf-8")

        changed, _ = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed
        assert adr.read_text(encoding="utf-8") == before

    def test_link_inside_an_inline_code_span_is_left_alone(self, tmp_path: Path) -> None:
        repo_root, adr = _tree(tmp_path, "Write `[glossary](../../../shared/reference/glossary.md)` for it.")

        changed, _ = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed

    def test_link_that_stays_inside_the_repository_is_left_alone(self, tmp_path: Path) -> None:
        """Not an LNK-002 finding, so not an LNK-011 rewrite either."""
        repo_root, adr = _tree(tmp_path, "See [config](../docs-project.yaml) and [site](../../README.md).")
        (repo_root / "README.md").write_text("# Site\n", encoding="utf-8")
        before = adr.read_text(encoding="utf-8")

        changed, _ = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed
        assert adr.read_text(encoding="utf-8") == before

    def test_external_anchor_and_scheme_targets_are_left_alone(self, tmp_path: Path) -> None:
        body = "[a](https://example.com) [b](#section) [c](mailto:x@example.com) [d](tel:+123)"
        repo_root, adr = _tree(tmp_path, body)

        changed, _ = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed

    def test_link_title_and_angle_bracket_forms_are_left_alone(self, tmp_path: Path) -> None:
        body = (
            '[a](../../../shared/reference/glossary.md "Glossary")\n'
            "[b](<../../../shared/reference/glossary.md>)\n"
            "[c](../../../shared/reference/glossary%2Emd)"
        )
        repo_root, adr = _tree(tmp_path, body)

        changed, _ = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed

    def test_reference_style_links_and_images_are_left_alone(self, tmp_path: Path) -> None:
        body = "[a][ref]\n\n[ref]: ../../../shared/reference/glossary.md"
        repo_root, adr = _tree(tmp_path, body)

        changed, _ = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed

    def test_two_links_on_one_line_are_both_rewritten(self, tmp_path: Path) -> None:
        body = "[a](../../../shared/reference/glossary.md) and [b](../../../shared/reference/glossary.md#terms)"
        repo_root, adr = _tree(tmp_path, body)

        changed, messages = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert changed
        assert len(messages) == 2
        text = adr.read_text(encoding="utf-8")
        assert "[a](https://github.com/acme/handbook/blob/main/shared/reference/glossary.md)" in text
        assert "[b](https://github.com/acme/handbook/blob/main/shared/reference/glossary.md#terms)" in text

    def test_dry_run_reports_without_writing(self, tmp_path: Path) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md).")
        before = adr.read_text(encoding="utf-8")

        changed, messages = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL, dry_run=True)

        assert changed
        assert len(messages) == 1
        assert adr.read_text(encoding="utf-8") == before

    def test_second_run_is_a_no_op(self, tmp_path: Path) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md#terms).")

        fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)
        after_first = adr.read_text(encoding="utf-8")
        changed, messages = fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        assert not changed
        assert messages == []
        assert adr.read_text(encoding="utf-8") == after_first

    def test_unicode_content_survives_the_rewrite(self, tmp_path: Path) -> None:
        body = "Title → ✓ 中文\n\nSee [glossary](../../../shared/reference/glossary.md)."
        repo_root, adr = _tree(tmp_path, body)

        fix_cross_plugin_links(adr, repo_root, REPOSITORY_URL)

        text = adr.read_text(encoding="utf-8")
        assert "→" in text
        assert "中文" in text


class TestRepositoryUrlResolution:
    """Which URL governs a document, including the sub-project fallback."""

    @staticmethod
    def _monorepo(tmp_path: Path, sub_url: str | None) -> Path:
        repo_root = tmp_path / "site"
        (repo_root / "adr").mkdir(parents=True)
        (repo_root / "service-a" / "adr").mkdir(parents=True)

        (repo_root / "docs-project.yaml").write_text(
            yaml.dump(
                {
                    "version": "1",
                    "project": {
                        "id": "root-project",
                        "name": "Root",
                        "repository_url": "https://example.com/org/repo/blob/main/site",
                    },
                    "structure": {"document_folders": ["adr"]},
                    "subprojects": ["service-a"],
                }
            ),
            encoding="utf-8",
        )
        sub_project: dict[str, object] = {"id": "service-a", "name": "Service A"}
        if sub_url is not None:
            sub_project["repository_url"] = sub_url
        (repo_root / "service-a" / "docs-project.yaml").write_text(
            yaml.dump({"version": "1", "project": sub_project, "structure": {"document_folders": ["adr"]}}),
            encoding="utf-8",
        )
        for folder, uuid in (("adr", "22222222"), ("service-a/adr", "33333333")):
            (repo_root / folder / "adr-001-x.md").write_text(
                ADR_TEMPLATE.format(body="Body.").replace("11111111", uuid),
                encoding="utf-8",
            )
        return repo_root

    def test_subproject_without_a_url_inherits_the_root_one(self, tmp_path: Path) -> None:
        repo_root = self._monorepo(tmp_path, sub_url=None)

        urls = _repository_urls_from_claims(_discover_doc_claims(repo_root))

        assert urls[repo_root / "service-a" / "adr" / "adr-001-x.md"] == ("https://example.com/org/repo/blob/main/site")

    def test_subproject_with_its_own_url_keeps_it(self, tmp_path: Path) -> None:
        repo_root = self._monorepo(tmp_path, sub_url="https://example.com/org/service-a/blob/main")

        urls = _repository_urls_from_claims(_discover_doc_claims(repo_root))

        assert urls[repo_root / "service-a" / "adr" / "adr-001-x.md"] == ("https://example.com/org/service-a/blob/main")
        assert urls[repo_root / "adr" / "adr-001-x.md"] == "https://example.com/org/repo/blob/main/site"

    def test_no_url_anywhere_leaves_every_document_without_one(self, tmp_path: Path) -> None:
        repo_root, _ = _tree(tmp_path, "Body.", repository_url=None)

        urls = _repository_urls_from_claims(_discover_doc_claims(repo_root))

        assert set(urls.values()) == {None}

    def test_conflicting_urls_for_one_file_resolve_to_none(self) -> None:
        """Two configs claiming one folder with different URLs is not a choice."""
        claims = {
            Path("a.md"): [
                (None, "p1", "https://example.com/one"),
                (None, "p2", "https://example.com/two"),
            ]
        }

        assert _repository_urls_from_claims(claims) == {Path("a.md"): None}


class TestFixCrossPluginLinksInTree:
    """The whole-tree entry point and the standalone script."""

    def test_documents_without_a_url_are_skipped(self, tmp_path: Path) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md).")
        before = adr.read_text(encoding="utf-8")

        results = fix_cross_plugin_links_in_tree(repo_root, [adr], {adr: None})

        assert results == []
        assert adr.read_text(encoding="utf-8") == before

    def test_results_pair_each_document_with_its_message(self, tmp_path: Path) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md).")

        results = fix_cross_plugin_links_in_tree(repo_root, [adr], {adr: REPOSITORY_URL})

        assert len(results) == 1
        document, message = results[0]
        assert document == adr
        assert message.startswith("LNK-011: Line 14: Rewrote link")

    def test_main_rewrites_the_tree(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md).")

        assert main(["--repo-root", str(repo_root)]) == 0

        assert "https://github.com/acme/handbook/blob/main/shared/reference/glossary.md" in adr.read_text(
            encoding="utf-8"
        )
        assert "1 link(s) rewritten across 1 document(s)" in capsys.readouterr().out

    def test_main_dry_run_leaves_the_tree_alone(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        repo_root, adr = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md).")
        before = adr.read_text(encoding="utf-8")

        assert main(["--repo-root", str(repo_root), "--dry-run"]) == 0

        assert adr.read_text(encoding="utf-8") == before
        assert "1 link(s) would be rewritten" in capsys.readouterr().out

    def test_main_without_a_configured_url_says_so(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        repo_root, _ = _tree(tmp_path, "See [glossary](../../../shared/reference/glossary.md).", repository_url=None)

        assert main(["--repo-root", str(repo_root)]) == 0

        assert "No project.repository_url configured" in capsys.readouterr().out

    def test_main_with_no_documents_says_so(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--repo-root", str(tmp_path)]) == 0

        assert "No documents found" in capsys.readouterr().out
