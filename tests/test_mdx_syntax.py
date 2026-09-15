"""MDX-010: escaping the angle brackets MDX-001 reports, and nothing else.

``fixes/mdx_syntax.py`` is the repair for ``MDX-001``. Its contract is not "fix
angle brackets" but "fix exactly the candidates the check reports", so most of
what is asserted here is what the fixer leaves alone: code fences, inline code
spans, the frontmatter block, comparisons such as ``<5ms``, valid HTML and JSX,
autolinks, and text that is already escaped. See the finding registry in
``docs-cms/rfcs/rfc-003-validator-roadmap.md``.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from docuchango.fixes.mdx_syntax import fix_mdx_issues, fix_mdx_syntax
from docuchango.markdown import mdx_tags
from docuchango.validator import DocValidator


def _document(body: str) -> str:
    """A minimal document with a frontmatter block in front of ``body``."""
    return f'---\nid: adr-001\ntitle: "ADR-001: Sample"\n---\n\n{body}\n'


class TestEscapesWhatMdx001Reports:
    """Every pattern ``check_mdx_compatibility`` flags is escaped."""

    @pytest.mark.parametrize(
        ("line", "expected"),
        [
            ("Set the header to <token> first.", "Set the header to &lt;token&gt; first."),
            ("Use <agentName> as the caller.", "Use &lt;agentName&gt; as the caller."),
            ("Read <api_key> from the env.", "Read &lt;api_key&gt; from the env."),
            ("A <time-out> is not the HTML <time>.", "A &lt;time-out&gt; is not the HTML <time>."),
            ("Close it with </token> please.", "Close it with &lt;/token&gt; please."),
            ("Pass <your-secret key> along.", "Pass &lt;your-secret key&gt; along."),
            ("Write to <log-name>.", "Write to &lt;log-name&gt;."),
        ],
    )
    def test_placeholder_is_escaped(self, line: str, expected: str) -> None:
        fixed, messages = fix_mdx_issues(line)
        assert fixed == expected
        assert len(messages) == 1
        assert messages[0].startswith("MDX-010: Line 1: Escaped ")

    def test_message_names_the_line_and_both_forms(self) -> None:
        content = "first line\nSet <token> here."
        _fixed, messages = fix_mdx_issues(content)
        assert messages == ["MDX-010: Line 2: Escaped '<token>' in prose as '&lt;token&gt;'"]

    def test_several_candidates_on_one_line_are_all_escaped(self) -> None:
        fixed, messages = fix_mdx_issues("Send <one> then <two>.")
        assert fixed == "Send &lt;one&gt; then &lt;two&gt;."
        assert len(messages) == 2

    def test_line_numbers_count_the_whole_document(self) -> None:
        _fixed, messages = fix_mdx_issues(_document("Set <token> here."))
        # Frontmatter is four lines, then a blank line, so the body is line 6.
        assert messages == ["MDX-010: Line 6: Escaped '<token>' in prose as '&lt;token&gt;'"]


class TestLeavesAlone:
    """What MDX-001 tolerates, MDX-010 must not touch."""

    @pytest.mark.parametrize(
        "line",
        [
            # Comparisons: '<' followed by a digit or a space is never JSX.
            "tail latency <100 ms at p99",
            "error budget >5 failures per week",
            "holds while a < b and b > c",
            "kept under < threshold at all times",
            # Valid HTML, open and closed.
            "A line break <br /> and a <sup>note</sup>.",
            "<details><summary>More</summary></details>",
            '<div class="callout">text</div>',
            # PascalCase JSX components and explicit self-closing tags.
            "Render <Outlet /> into <SuspenseWrapper>.",
            'Drop in <widget role="img" /> anywhere.',
            # CommonMark autolinks.
            "See <https://example.com> for details.",
            "Mail <team@example.com> about it.",
            # Already escaped: there is no '<' left to match.
            "Already &lt;token&gt; escaped.",
        ],
    )
    def test_line_is_unchanged(self, line: str) -> None:
        fixed, messages = fix_mdx_issues(line)
        assert fixed == line
        assert messages == []

    def test_backtick_fence_is_untouched(self) -> None:
        content = _document('```bash\ncurl -H "Auth: <token>" url\n```\n\nand <token> in prose')
        fixed, messages = fix_mdx_issues(content)
        assert 'curl -H "Auth: <token>" url' in fixed
        assert "and &lt;token&gt; in prose" in fixed
        assert len(messages) == 1

    def test_tilde_fence_is_untouched(self) -> None:
        content = _document("~~~text\n<agentName> writes to <log-name>\n~~~")
        fixed, messages = fix_mdx_issues(content)
        assert fixed == content
        assert messages == []

    def test_nested_fence_stays_code_until_the_outer_fence_closes(self) -> None:
        content = _document("````markdown\n```\n<token>\n```\n````")
        fixed, messages = fix_mdx_issues(content)
        assert fixed == content
        assert messages == []

    def test_inline_code_is_untouched(self) -> None:
        content = "Set `<token>` and ``<other>`` but not <bare>."
        fixed, messages = fix_mdx_issues(content)
        assert fixed == "Set `<token>` and ``<other>`` but not &lt;bare&gt;."
        assert len(messages) == 1

    def test_multi_line_inline_span_is_untouched(self) -> None:
        content = "Set `<token>\nand more` here."
        fixed, messages = fix_mdx_issues(content)
        assert fixed == content
        assert messages == []

    def test_frontmatter_is_untouched(self) -> None:
        content = "---\nid: adr-001\ntitle: <token>\n---\n\nBody <token> here.\n"
        fixed, messages = fix_mdx_issues(content)
        assert "title: <token>" in fixed
        assert "Body &lt;token&gt; here." in fixed
        assert len(messages) == 1

    def test_clean_document_is_returned_verbatim(self) -> None:
        content = _document("Nothing to escape here.")
        fixed, messages = fix_mdx_issues(content)
        assert fixed == content
        assert messages == []

    def test_empty_content(self) -> None:
        assert fix_mdx_issues("") == ("", [])

    def test_unicode_is_preserved(self) -> None:
        fixed, messages = fix_mdx_issues("速度 → <token> ✓ 中文")
        assert fixed == "速度 → &lt;token&gt; ✓ 中文"
        assert len(messages) == 1


class TestIdempotence:
    """A second run must report nothing and change nothing."""

    @pytest.mark.parametrize(
        "content",
        [
            "Set <token> and <other> here.",
            "Already &lt;token&gt; escaped.",
            _document("```\n<token>\n```\n\nprose <token>"),
            _document("Mixed <a-b> with `<c-d>` and <br /> and <https://x.example>."),
        ],
    )
    def test_second_run_is_a_no_op(self, content: str) -> None:
        once, first = fix_mdx_issues(content)
        twice, second = fix_mdx_issues(once)
        assert twice == once
        assert second == []
        assert len(first) == len(mdx_tags(content))

    def test_escaping_does_not_double_escape(self) -> None:
        fixed, _messages = fix_mdx_issues("Set <token> here.")
        assert "&amp;" not in fixed
        assert fixed.count("&lt;") == 1
        assert fixed.count("&gt;") == 1


class TestAlignmentWithTheCheck:
    """The fixer repairs exactly what MDX-001 reports, no more and no less."""

    SAMPLE = _document(
        "Set <token> and <agentName>, keep <br /> and <Outlet />,\n"
        "keep `<inline>` and <https://example.com>, keep <100 ms.\n"
        "\n"
        "```text\n"
        "<fenced>\n"
        "```\n"
    )

    def test_fix_repairs_every_reported_candidate(self) -> None:
        reported = mdx_tags(self.SAMPLE)
        assert [tag.name for tag in reported] == ["token", "agentName"]

        fixed, messages = fix_mdx_issues(self.SAMPLE)
        assert len(messages) == len(reported)
        assert mdx_tags(fixed) == []

    def test_validator_reports_nothing_after_the_fix(self, tmp_path: Path) -> None:
        path = tmp_path / "adr-001-sample.md"
        path.write_text(self.SAMPLE, encoding="utf-8")

        validator = DocValidator(repo_root=tmp_path, verbose=False)
        before = validator._mask_code(self.SAMPLE, strip_frontmatter=True)

        changed, messages = fix_mdx_syntax(path)
        assert changed is True
        assert len(messages) == 2

        after_text = path.read_text(encoding="utf-8")
        # The masking is unchanged apart from the escaped candidates, i.e. the
        # fix did not turn prose into code or vice versa.
        after = validator._mask_code(after_text, strip_frontmatter=True)
        assert len(after) == len(before)
        assert mdx_tags(after_text) == []


class TestFileEntryPoint:
    """``fix_mdx_syntax`` is what Phase 1 of ``validate`` calls."""

    def test_rewrites_the_file_and_reports(self, tmp_path: Path) -> None:
        path = tmp_path / "doc.md"
        path.write_text(_document("Set <token> here."), encoding="utf-8")

        changed, messages = fix_mdx_syntax(path)

        assert changed is True
        assert messages == ["MDX-010: Line 6: Escaped '<token>' in prose as '&lt;token&gt;'"]
        assert "&lt;token&gt;" in path.read_text(encoding="utf-8")

    def test_leaves_a_clean_file_byte_identical(self, tmp_path: Path) -> None:
        path = tmp_path / "doc.md"
        original = _document("Nothing to escape, `<token>` is code.")
        path.write_text(original, encoding="utf-8")
        before = path.read_bytes()

        changed, messages = fix_mdx_syntax(path)

        assert changed is False
        assert messages == []
        assert path.read_bytes() == before

    def test_a_bom_is_dropped_by_the_shared_reader(self, tmp_path: Path) -> None:
        """Reads go through text_io, so a BOM cannot hide the frontmatter."""
        path = tmp_path / "doc.md"
        path.write_text("﻿" + _document("Set <token> here."), encoding="utf-8")

        changed, messages = fix_mdx_syntax(path)

        assert changed is True
        assert len(messages) == 1
        assert not path.read_text(encoding="utf-8").startswith("﻿")

    def test_second_pass_over_a_repaired_file_writes_nothing(self, tmp_path: Path) -> None:
        path = tmp_path / "doc.md"
        path.write_text(_document("Set <token> here."), encoding="utf-8")

        fix_mdx_syntax(path)
        after_first = path.read_bytes()
        changed, messages = fix_mdx_syntax(path)

        assert changed is False
        assert messages == []
        assert path.read_bytes() == after_first


class TestPerformance:
    """The scan is linear; a pathological line must not blow up."""

    def test_long_line_completes_quickly(self) -> None:
        line = "<123 " + "abc " * 200 + "xyz <token> " + "a" * 500

        start = time.time()
        _fixed, messages = fix_mdx_issues(line)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"fix_mdx_issues took too long: {elapsed}s"
        assert len(messages) == 1
