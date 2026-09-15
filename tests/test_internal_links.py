"""LNK-010: candidate-based internal link rewriting.

``docuchango.fixes.internal_links`` rewrites a broken link when exactly one
document in the scanned set carries the target's filename. These tests cover
the fixer in isolation; ``tests/test_link_validation.py`` covers the same rule
end to end through ``docuchango validate``, and
``tests/fixtures/findings/LNK-010-*`` pins the CLI output.
"""

from __future__ import annotations

from pathlib import Path

from docuchango.fixes.internal_links import (
    build_index,
    fix_internal_links,
    fix_links_in_tree,
    main,
)
from docuchango.links import document_index

DOC = """---
id: rfc-001
title: "RFC-001: Linking"
---

# RFC-001: Linking

{body}
"""


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DOC.format(body=body), encoding="utf-8")
    return path


def _tree(tmp_path: Path, body: str, *targets: str) -> tuple[Path, Path, list[Path]]:
    """A repo with one linking RFC and a target document per ``targets``."""
    source = _write(tmp_path / "docs-cms" / "rfcs" / "rfc-001-linking.md", body)
    documents = [source] + [_write(tmp_path / rel, "Target.") for rel in targets]
    return tmp_path, source, documents


def _fix(tmp_path: Path, source: Path, documents: list[Path], dry_run: bool = False) -> tuple[bool, list[str]]:
    return fix_internal_links(source, build_index(documents, tmp_path), tmp_path, dry_run=dry_run)


class TestUniqueCandidate:
    """Exactly one scanned document matches, so the link is rewritten."""

    def test_candidate_at_a_different_depth(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the decision](./adr-003-decision.md).",
            "docs-cms/adr/adr-003-decision.md",
        )

        changed, messages = _fix(root, source, documents)

        assert changed
        assert messages == ["LNK-010: Line 8: Rewrote link './adr-003-decision.md' to '../adr/adr-003-decision.md'"]
        assert "(../adr/adr-003-decision.md)" in source.read_text(encoding="utf-8")

    def test_candidate_deeper_than_the_linking_document(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the note](./memo-004-note.md).",
            "docs-cms/rfcs/archive/memo-004-note.md",
        )

        changed, messages = _fix(root, source, documents)

        assert changed
        assert "to './archive/memo-004-note.md'" in messages[0]

    def test_candidate_in_a_subproject_folder(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the service decision](./adr-002-service.md).",
            "services/service-d/adr/adr-002-service.md",
        )

        changed, messages = _fix(root, source, documents)

        assert changed
        assert "to '../../services/service-d/adr/adr-002-service.md'" in messages[0]

    def test_anchor_is_preserved(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [context](./adr-003-decision.md#context).",
            "docs-cms/adr/adr-003-decision.md",
        )

        changed, _ = _fix(root, source, documents)

        assert changed
        assert "(../adr/adr-003-decision.md#context)" in source.read_text(encoding="utf-8")

    def test_query_is_preserved(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [context](./adr-003-decision.md?plain=1).",
            "docs-cms/adr/adr-003-decision.md",
        )

        _fix(root, source, documents)

        assert "(../adr/adr-003-decision.md?plain=1)" in source.read_text(encoding="utf-8")

    def test_suffix_less_target_matches_the_markdown_file(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the decision](./adr-003-decision).",
            "docs-cms/adr/adr-003-decision.md",
        )

        changed, _ = _fix(root, source, documents)

        assert changed
        assert "(../adr/adr-003-decision.md)" in source.read_text(encoding="utf-8")

    def test_bare_relative_target_is_rewritten(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the decision](adr/adr-003-decision.md).",
            "docs-cms/adr/adr-003-decision.md",
        )

        changed, _ = _fix(root, source, documents)

        assert changed
        assert "(../adr/adr-003-decision.md)" in source.read_text(encoding="utf-8")

    def test_two_broken_links_on_one_line(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [one](./adr-003-decision.md) and [two](./adr-004-other.md).",
            "docs-cms/adr/adr-003-decision.md",
            "docs-cms/adr/adr-004-other.md",
        )

        changed, messages = _fix(root, source, documents)

        assert changed
        assert len(messages) == 2
        body = source.read_text(encoding="utf-8")
        assert "[one](../adr/adr-003-decision.md)" in body
        assert "[two](../adr/adr-004-other.md)" in body


class TestLinksLeftAlone:
    """Every case LNK-010 declines, leaving the link to LNK-001."""

    def test_zero_candidates(self, tmp_path: Path) -> None:
        root, source, documents = _tree(tmp_path, "See [gone](./adr-999-missing.md).")
        before = source.read_text(encoding="utf-8")

        changed, messages = _fix(root, source, documents)

        assert not changed
        assert messages == []
        assert source.read_text(encoding="utf-8") == before

    def test_two_candidates(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [setup](./setup.md).",
            "docs-cms/guides/setup.md",
            "docs-cms/handbook/setup.md",
        )
        before = source.read_text(encoding="utf-8")

        changed, messages = _fix(root, source, documents)

        assert not changed
        assert messages == []
        assert source.read_text(encoding="utf-8") == before

    def test_link_inside_a_code_fence(self, tmp_path: Path) -> None:
        body = "```markdown\nSee [the decision](./adr-003-decision.md).\n```"
        root, source, documents = _tree(tmp_path, body, "docs-cms/adr/adr-003-decision.md")
        before = source.read_text(encoding="utf-8")

        changed, messages = _fix(root, source, documents)

        assert not changed
        assert messages == []
        assert source.read_text(encoding="utf-8") == before

    def test_link_inside_an_inline_code_span(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "Write `[the decision](./adr-003-decision.md)` in your document.",
            "docs-cms/adr/adr-003-decision.md",
        )
        before = source.read_text(encoding="utf-8")

        changed, _ = _fix(root, source, documents)

        assert not changed
        assert source.read_text(encoding="utf-8") == before

    def test_link_that_already_resolves(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the decision](../adr/adr-003-decision.md).",
            "docs-cms/adr/adr-003-decision.md",
        )

        changed, messages = _fix(root, source, documents)

        assert not changed
        assert messages == []

    def test_external_and_anchor_links(self, tmp_path: Path) -> None:
        body = "[site](https://example.com/adr-003-decision.md) and [top](#context) and [mail](mailto:a@b.c)"
        root, source, documents = _tree(tmp_path, body, "docs-cms/adr/adr-003-decision.md")

        changed, _ = _fix(root, source, documents)

        assert not changed

    def test_reference_style_link_is_not_rewritten(self, tmp_path: Path) -> None:
        body = "See [the decision][adr] for details.\n\n[adr]: ./adr-003-decision.md"
        root, source, documents = _tree(tmp_path, body, "docs-cms/adr/adr-003-decision.md")

        changed, _ = _fix(root, source, documents)

        assert not changed

    def test_target_with_a_link_title_is_not_rewritten(self, tmp_path: Path) -> None:
        body = 'See [the decision](./adr-003-decision.md "The Decision").'
        root, source, documents = _tree(tmp_path, body, "docs-cms/adr/adr-003-decision.md")

        changed, _ = _fix(root, source, documents)

        assert not changed

    def test_candidate_outside_the_repository_root_is_not_a_candidate(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        outside = _write(tmp_path / "outside" / "adr-003-decision.md", "Target.")
        source = _write(repo / "docs-cms" / "rfcs" / "rfc-001-linking.md", "See [it](./adr-003-decision.md).")

        changed, messages = fix_internal_links(source, build_index([source, outside], repo), repo)

        assert not changed
        assert messages == []


class TestIdempotence:
    """A second run has nothing left to do."""

    def test_second_run_is_a_no_op(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the decision](./adr-003-decision.md#context).",
            "docs-cms/adr/adr-003-decision.md",
        )

        changed, _ = _fix(root, source, documents)
        assert changed
        after_first = source.read_text(encoding="utf-8")

        changed, messages = _fix(root, source, documents)

        assert not changed
        assert messages == []
        assert source.read_text(encoding="utf-8") == after_first


class TestDryRun:
    """``--dry-run`` reports the rewrite without writing it."""

    def test_dry_run_reports_but_does_not_write(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the decision](./adr-003-decision.md).",
            "docs-cms/adr/adr-003-decision.md",
        )
        before = source.read_text(encoding="utf-8")

        changed, messages = _fix(root, source, documents, dry_run=True)

        assert changed
        assert len(messages) == 1
        assert source.read_text(encoding="utf-8") == before


class TestIndex:
    """The candidate index."""

    def test_document_index_groups_by_filename(self, tmp_path: Path) -> None:
        index = document_index([tmp_path / "a" / "x.md", tmp_path / "b" / "x.md", tmp_path / "a" / "y.md"])

        assert sorted(index) == ["x.md", "y.md"]
        assert index["x.md"] == sorted(index["x.md"])
        assert len(index["x.md"]) == 2

    def test_build_index_drops_documents_outside_the_root(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        (repo / "adr").mkdir(parents=True)
        inside = repo / "adr" / "in.md"
        inside.write_text("x", encoding="utf-8")
        outside = tmp_path / "out.md"
        outside.write_text("x", encoding="utf-8")

        index = build_index([inside, outside], repo)

        assert set(index) == {"in.md"}


class TestTreeAndMain:
    """The whole-tree helper and the standalone entry point."""

    def test_fix_links_in_tree_reports_each_rewrite(self, tmp_path: Path) -> None:
        root, source, documents = _tree(
            tmp_path,
            "See [the decision](./adr-003-decision.md).",
            "docs-cms/adr/adr-003-decision.md",
        )

        results = fix_links_in_tree(root, documents)

        assert [path for path, _ in results] == [source]
        assert "Rewrote link './adr-003-decision.md'" in results[0][1]

    def test_main_takes_a_repo_root(self, tmp_path: Path, capsys) -> None:
        config = tmp_path / "docs-cms" / "docs-project.yaml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            "version: '1'\n"
            "project:\n  id: p\n  name: P\n  description: d\n"
            "structure:\n  adr_dir: adr\n  rfc_dir: rfcs\n  memo_dir: memos\n"
            "  document_folders: [adr, rfcs, memos]\n",
            encoding="utf-8",
        )
        source = _write(tmp_path / "docs-cms" / "rfcs" / "rfc-001-linking.md", "See [it](./adr-003-decision.md).")
        _write(tmp_path / "docs-cms" / "adr" / "adr-003-decision.md", "Target.")

        assert main(["--repo-root", str(tmp_path)]) == 0

        assert "(../adr/adr-003-decision.md)" in source.read_text(encoding="utf-8")
        assert "1 link(s) rewritten" in capsys.readouterr().out

    def test_main_dry_run_leaves_files_untouched(self, tmp_path: Path, capsys) -> None:
        config = tmp_path / "docs-cms" / "docs-project.yaml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            "version: '1'\n"
            "project:\n  id: p\n  name: P\n  description: d\n"
            "structure:\n  adr_dir: adr\n  rfc_dir: rfcs\n  memo_dir: memos\n"
            "  document_folders: [adr, rfcs, memos]\n",
            encoding="utf-8",
        )
        source = _write(tmp_path / "docs-cms" / "rfcs" / "rfc-001-linking.md", "See [it](./adr-003-decision.md).")
        _write(tmp_path / "docs-cms" / "adr" / "adr-003-decision.md", "Target.")
        before = source.read_text(encoding="utf-8")

        assert main(["--repo-root", str(tmp_path), "--dry-run"]) == 0

        assert source.read_text(encoding="utf-8") == before
        assert "1 link(s) would be rewritten" in capsys.readouterr().out

    def test_main_on_a_tree_with_no_documents(self, tmp_path: Path, capsys) -> None:
        assert main(["--repo-root", str(tmp_path)]) == 0
        assert "No documents found" in capsys.readouterr().out
