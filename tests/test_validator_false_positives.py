"""Regression tests for validator false positives.

Covers three classes of false positives:
1. MDX escaping: '<'/'>' before a digit (e.g. '<5ms', '>90%') is safe and must
   NOT be flagged; only '<letter' (a real JSX-tag risk) should be flagged.
2. Links: bare relative links (no leading './', '../', '/') that resolve to an
   existing file are valid and must NOT be reported as "Ambiguous link format".
3. Filenames/IDs: strict naming is only enforced on top-level document files
   (nested support files are skipped), and amendment filenames map to the
   amendment id form (adr-XXX-aNN).
"""

from pathlib import Path

from docuchango.validator import DocValidator, Link, LinkType


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


ADR_FRONTMATTER = """---
title: {title}
status: Accepted
created: 2025-01-01
deciders: Team
tags: [test]
id: {doc_id}
project_id: test-project
doc_uuid: 8b063564-82a5-4a21-943f-e868388d36b9
---

{body}
"""


class TestMdxEscapingFalsePositives:
    def _run_mdx_check(self, tmp_path: Path, body: str):
        adr = tmp_path / "docs-cms" / "adr" / "adr-001-example.md"
        _write(adr, ADR_FRONTMATTER.format(title="Example ADR Title", doc_id="adr-001", body=body))
        v = DocValidator(repo_root=tmp_path, verbose=False)
        v.scan_documents()
        v.check_mdx_compatibility()
        errors: list[str] = []
        for doc in v.documents:
            errors.extend(doc.errors)
        return errors

    def test_less_than_before_digit_not_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "- Plugin overhead budget: <5ms acceptable")
        assert errors == [], f"'<5ms' should be safe, got: {errors}"

    def test_greater_than_before_digit_not_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "- Task decomposition accuracy: >90%")
        assert errors == [], f"'>90%' should be safe, got: {errors}"

    def test_comparison_in_prose_not_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "- Both binaries are <1MB in size")
        assert errors == [], f"'<1MB' should be safe, got: {errors}"

    def test_comparison_with_space_after_lt_not_flagged(self, tmp_path):
        # 'last_seen < threshold' is a comparison, not a tag (space after '<').
        errors = self._run_mdx_check(tmp_path, "- Query stale agents (last_seen < threshold)")
        assert errors == [], f"'< threshold' comparison should be safe, got: {errors}"

    def test_bare_lt_gt_comparison_not_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "- Ensure a < b and c > d always holds")
        assert errors == [], f"'a < b' should be safe, got: {errors}"

    def test_jsx_like_tag_is_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "The <agentName> placeholder is used here.")
        assert any("agentName" in e and "JSX tag" in e for e in errors), f"'<agentName>' should be flagged, got: {errors}"

    def test_placeholder_lowercase_is_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "Send the <token> to the endpoint.")
        assert any("token" in e for e in errors), f"'<token>' should be flagged, got: {errors}"

    def test_placeholder_in_quoted_prose_is_flagged(self, tmp_path):
        # Placeholders inside a quoted example string still break MDX.
        errors = self._run_mdx_check(tmp_path, '4. Build message: "The <agentName> agent needs <scopes>."')
        assert any("agentName" in e for e in errors), errors
        assert any("scopes" in e for e in errors), errors

    def test_generics_syntax_is_flagged(self, tmp_path):
        # Lowercase generic syntax like Map<string, string> is a real MDX risk.
        errors = self._run_mdx_check(tmp_path, "The registry is a Map<string, string> internally.")
        assert any("string" in e for e in errors), errors

    def test_known_html_anchor_not_flagged(self, tmp_path):
        body = '**Related**: <a href="../adr/adr-001-x.md" target="_blank">ADR-001</a>'
        errors = self._run_mdx_check(tmp_path, body)
        assert errors == [], f"valid <a> HTML should be safe, got: {errors}"

    def test_html_with_gt_inside_attribute_not_flagged(self, tmp_path):
        # A '>' inside a quoted attribute value must not confuse the parser.
        body = '<a href="x" title="a > b">link</a>'
        errors = self._run_mdx_check(tmp_path, body)
        assert errors == [], f"'>' inside attribute should be safe, got: {errors}"

    def test_known_html_br_not_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "Line one<br/>line two<br>line three")
        assert errors == [], f"<br>/<br/> should be safe, got: {errors}"

    def test_jsx_component_pascalcase_not_flagged(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "Render <SuspenseWrapper> around it and <Outlet />.")
        assert errors == [], f"PascalCase JSX components should be safe, got: {errors}"

    def test_inline_code_is_ignored(self, tmp_path):
        errors = self._run_mdx_check(tmp_path, "Use the key `introspect.client.<name>` for lookups.")
        assert errors == [], f"inline code should be ignored, got: {errors}"

    def test_multiline_inline_code_span_is_ignored(self, tmp_path):
        # An inline code span that wraps across a line break must still mask its
        # contents (a real false-positive source before the fix).
        body = "set `Authorization: Bearer\n<outbound_user_credential>` and return."
        errors = self._run_mdx_check(tmp_path, body)
        assert errors == [], f"multi-line inline code should be ignored, got: {errors}"

    def test_code_fence_is_ignored(self, tmp_path):
        body = "```go\nfunc F[T any]() {}\nvar x = a < b\n```"
        errors = self._run_mdx_check(tmp_path, body)
        assert errors == [], f"code fence should be ignored, got: {errors}"

    def test_indented_code_fence_is_ignored(self, tmp_path):
        # Indented opening fence (e.g. inside a list) must still be recognized.
        body = "2. Header example\n\n   ```text\n   X-Admin-API-Key: <api-key>\n   ```\n"
        errors = self._run_mdx_check(tmp_path, body)
        assert errors == [], f"indented code fence should be ignored, got: {errors}"


class TestBareRelativeLinks:
    def _make_link(self, tmp_path: Path, target: str) -> Link:
        source = tmp_path / "docs-cms" / "rfcs" / "rfc-001-source.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("stub", encoding="utf-8")
        link = Link(
            source_doc=source,
            target=target,
            line_number=1,
            link_type=LinkType.INTERNAL_DOC,
        )
        v = DocValidator(repo_root=tmp_path, verbose=False)
        v._validate_internal_link(link)
        return link

    def test_bare_relative_link_to_existing_sibling_dir_is_valid(self, tmp_path):
        # Create the target the bare link 'adr/adr-012-...' points to, relative
        # to the source doc's directory (docs-cms/rfcs).
        target_file = tmp_path / "docs-cms" / "rfcs" / "adr" / "adr-012-trust.md"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("stub", encoding="utf-8")

        link = self._make_link(tmp_path, "adr/adr-012-trust.md")
        assert link.is_valid, f"bare relative link should be valid, got: {link.error_message}"
        assert "Ambiguous" not in link.error_message

    def test_bare_relative_link_to_missing_file_reports_not_found(self, tmp_path):
        link = self._make_link(tmp_path, "adr/does-not-exist.md")
        assert not link.is_valid
        assert "File not found" in link.error_message
        assert "Ambiguous" not in link.error_message

    def test_dot_slash_relative_link_still_works(self, tmp_path):
        target_file = tmp_path / "docs-cms" / "rfcs" / "rfc-002-other.md"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("stub", encoding="utf-8")
        link = self._make_link(tmp_path, "./rfc-002-other.md")
        assert link.is_valid

    def test_link_to_existing_directory_is_valid(self, tmp_path):
        # A link to a directory (e.g. '[All ADRs](../adr/)') must not have '.md'
        # appended and reported as broken.
        adr_dir = tmp_path / "docs-cms" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "adr-001-x.md").write_text("stub", encoding="utf-8")
        link = self._make_link(tmp_path, "../adr/")
        assert link.is_valid, f"directory link should be valid, got: {link.error_message}"

    def test_suffixless_link_resolves_with_md(self, tmp_path):
        target_file = tmp_path / "docs-cms" / "rfcs" / "rfc-002-other.md"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("stub", encoding="utf-8")
        link = self._make_link(tmp_path, "./rfc-002-other")
        assert link.is_valid, f"suffixless link should resolve to .md, got: {link.error_message}"


class TestFilenameAndIdScanning:
    def test_nested_support_files_are_skipped(self, tmp_path):
        # Valid top-level PRD
        prd = tmp_path / "docs-cms" / "prd" / "prd-001-example.md"
        _write(
            prd,
            """---
title: Example PRD Title
status: Draft
author: Team
created: 2025-01-01
tags: [test]
id: prd-001
project_id: test-project
doc_uuid: 8b063564-82a5-4a21-943f-e868388d36b9
target_release: v1.0
---

Body.
""",
        )
        # Nested support file that does NOT follow prd-NNN naming and has no
        # valid frontmatter. It must be skipped, producing no errors.
        nested = tmp_path / "docs-cms" / "prd" / "testing" / "api-test-requirements-ears.md"
        _write(nested, "# Just some test requirements\n\nNo frontmatter here.\n")

        v = DocValidator(repo_root=tmp_path, verbose=False)
        v.scan_documents()

        assert not any("Invalid PRD filename" in e for e in v.errors), v.errors
        scanned = {d.file_path.name for d in v.documents}
        assert "api-test-requirements-ears.md" not in scanned, "nested support file should not be scanned as a PRD"

    def test_top_level_invalid_filename_still_reported(self, tmp_path):
        bad = tmp_path / "docs-cms" / "prd" / "not-a-prd.md"
        _write(bad, "# stub\n")
        v = DocValidator(repo_root=tmp_path, verbose=False)
        v.scan_documents()
        assert any("Invalid PRD filename" in e for e in v.errors), v.errors

    def test_amendment_filename_maps_to_amendment_id(self, tmp_path):
        amendment = tmp_path / "docs-cms" / "adr" / "adr-043-amendment-01-registered-clients.md"
        _write(
            amendment,
            ADR_FRONTMATTER.format(
                title="ADR-043 Amendment 01: Registered Clients",
                doc_id="adr-043-a1",
                body="Amendment body.",
            ),
        )
        v = DocValidator(repo_root=tmp_path, verbose=False)
        v.scan_documents()
        v.check_ids()

        for doc in v.documents:
            assert doc.expected_id == "adr-043-a1", doc.expected_id
            assert not any("ID mismatch" in e for e in doc.errors), doc.errors


class TestLinksEscapingRepo:
    def _run(self, tmp_path: Path, body: str, repo_root: Path | None = None):
        # docs live in <repo>/docs-cms; repo_root defaults to tmp_path.
        repo_root = repo_root or tmp_path
        _write(
            repo_root / "docs-cms" / "docs-project.yaml",
            "project:\n  id: test-project\n  name: test-project\n",
        )
        adr = repo_root / "docs-cms" / "adr" / "adr-001-example.md"
        _write(adr, ADR_FRONTMATTER.format(title="Example ADR Title", doc_id="adr-001", body=body))
        v = DocValidator(repo_root=repo_root, verbose=False)
        v.scan_documents()
        v.check_cross_plugin_links()
        errors: list[str] = []
        for doc in v.documents:
            errors.extend(doc.errors)
        return errors

    def test_link_inside_docs_root_not_flagged(self, tmp_path):
        # ../rfcs/... stays within docs-cms/ (and the repo)
        target = tmp_path / "docs-cms" / "rfcs" / "rfc-002-other.md"
        _write(target, "stub")
        errors = self._run(tmp_path, "See [RFC-002](../rfcs/rfc-002-other.md).")
        assert not any("points outside the repository" in e for e in errors), errors

    def test_link_into_source_tree_inside_repo_not_flagged(self, tmp_path):
        # ../../internal/... escapes docs-cms/ but stays INSIDE the repo, which
        # is a legitimate reference and must NOT be flagged.
        errors = self._run(tmp_path, "See [factory](../../internal/orchestrator/factory.go).")
        assert not any("points outside the repository" in e for e in errors), errors

    def test_link_to_repo_root_readme_not_flagged(self, tmp_path):
        errors = self._run(tmp_path, "See the [README](../../README.md).")
        assert not any("points outside the repository" in e for e in errors), errors

    def test_link_escaping_repo_is_flagged(self, tmp_path):
        # Put the repo in a subdirectory so a link can escape it entirely.
        repo = tmp_path / "myrepo"
        errors = self._run(tmp_path, "See [x](../../../outside/secret.md).", repo_root=repo)
        assert any("points outside the repository" in e for e in errors), errors
        assert any("../../../outside/secret.md" in e for e in errors), errors

    def test_link_in_code_fence_ignored(self, tmp_path):
        repo = tmp_path / "myrepo"
        body = "```\n[x](../../../outside/factory.go)\n```"
        errors = self._run(tmp_path, body, repo_root=repo)
        assert not any("points outside the repository" in e for e in errors), errors

