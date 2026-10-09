"""Tests for the shared frontmatter delimiter rules in ``docuchango.markdown``."""

import frontmatter
import pytest

from docuchango.markdown import frontmatter_body_bounds, frontmatter_span, is_frontmatter_delimiter


class TestIsFrontmatterDelimiter:
    """The single definition of a ``---`` line, shared by the validator and the fixers."""

    @pytest.mark.parametrize(
        "line",
        ["---", "---\n", "---\r\n", "---\r", "--- ", "---\t", "--- \t\n", "---  \r\n", "----", "------ \r\n"],
    )
    def test_accepts_dashes_with_trailing_whitespace_and_any_line_ending(self, line):
        assert is_frontmatter_delimiter(line)

    @pytest.mark.parametrize(
        "line", ["--", "--- x", "---x", "----x", "- - -", "", "\ufeff---", "title: ---", "  ---", "\t---\n"]
    )
    def test_rejects_anything_else(self, line):
        assert not is_frontmatter_delimiter(line)


class TestFrontmatterBodyBounds:
    """``frontmatter_body_bounds`` finds the block python-frontmatter parses."""

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param("---\nid: doc\n---\n# Body\n", id="lf"),
            pytest.param("---\r\nid: doc\r\n---\r\n# Body\r\n", id="crlf"),
            pytest.param("--- \nid: doc\n---\t\n# Body\n", id="trailing-whitespace"),
            pytest.param("--- \r\nid: doc\r\n---\t\r\n# Body\r\n", id="trailing-whitespace-crlf"),
            pytest.param("----\nid: doc\n-----\n# Body\n", id="more-than-three-dashes"),
        ],
    )
    def test_agrees_with_the_parser(self, content):
        lines = content.splitlines(keepends=True)

        assert frontmatter_body_bounds(lines) == (1, 2)
        assert frontmatter_span(lines) == 3
        assert frontmatter_span(content.split("\n")) == 3
        assert frontmatter.loads(content).metadata == {"id": "doc"}

    def test_indented_dashes_in_a_block_scalar_do_not_end_the_block(self):
        """python-frontmatter only closes the block on a ``---`` in column zero."""
        content = "---\nid: doc\ndescription: |\n  ---\n  text\ncreated: 2020-01-01\n---\n# Body\n"
        lines = content.splitlines(keepends=True)

        assert frontmatter_body_bounds(lines) == (1, 6)
        assert frontmatter_span(content.split("\n")) == 7
        assert str(frontmatter.loads(content).metadata["created"]) == "2020-01-01"

    def test_opening_delimiter_may_be_indented(self):
        """python-frontmatter strips the document before it looks for the opening ``---``."""
        content = "  ---\nid: doc\n---\n"

        assert frontmatter_body_bounds(content.splitlines(keepends=True)) == (1, 2)
        assert frontmatter.loads(content).metadata == {"id": "doc"}

    def test_value_containing_dashes_does_not_end_the_block(self):
        lines = '---\ntitle: "a --- b"\nid: doc\n---\n'.splitlines(keepends=True)

        assert frontmatter_body_bounds(lines) == (1, 3)

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param("", id="empty"),
            pytest.param("# Title\n", id="no-block"),
            pytest.param("---\nid: doc\n", id="unterminated"),
            pytest.param("\n---\nid: doc\n---\n", id="not-on-first-line"),
            pytest.param("\ufeff---\nid: doc\n---\n", id="bom-not-stripped"),
        ],
    )
    def test_no_closed_block_on_the_first_line(self, content):
        assert frontmatter_body_bounds(content.splitlines(keepends=True)) is None

    def test_unterminated_block_spans_the_document(self):
        lines = ["--- ", "id: doc", "more: x"]

        assert frontmatter_span(lines) == 3
