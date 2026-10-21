"""Requirement traceability: the parser and the opt-in TRC-001..005 check."""

from pathlib import Path

import pytest

from docuchango.markdown import mask_code
from docuchango.schemas import DocsProjectConfig
from docuchango.traceability import has_disposition, parse_traceability
from docuchango.validator import DocValidator

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "docuchango" / "templates"
DETAILED_TEMPLATES = REPO_ROOT / "templates"


def _parse(text: str, can_define: bool = True):
    return parse_traceability(mask_code(text, strip_frontmatter=True), can_define)


class TestParser:
    def test_heading_bullet_and_table_definitions(self):
        trace = _parse(
            "| ID | Requirement |\n|----|----|\n| FR-1 | One |\n| **NFR-1** | Two |\n\n"
            "### AC-1: Heading form\n\nRequirement: FR-1\n\n"
            "- [ ] **AC-2** (Requirement: FR-1, FR-2): bullet form\n"
            "1. **FR-2**: numbered form\n"
        )
        assert sorted(trace.definitions) == ["AC-1", "AC-2", "FR-1", "FR-2", "NFR-1"]
        assert trace.definitions["AC-1"][0].requirements == ["FR-1"]
        assert trace.definitions["AC-2"][0].requirements == ["FR-1", "FR-2"]

    def test_rfcs_reference_but_never_define(self):
        trace = _parse("| FR-1 | AC-1 | Covered |\n### AC-2: heading\n", can_define=False)
        assert trace.definitions == {}
        assert [r.id for r in trace.references] == ["FR-1", "AC-1", "AC-2"]

    def test_own_definition_is_not_a_reference_but_repeats_are(self):
        trace = _parse("### AC-1: Title mentions AC-1 again\n\nSee AC-1.\n")
        assert [r.line for r in trace.references] == [1, 3]

    def test_code_is_ignored(self):
        trace = _parse("Real AC-1 and `AC-2` inline.\n\n```\nAC-3\n```\n")
        assert [r.id for r in trace.references] == ["AC-1"]

    def test_nfr_does_not_yield_fr_and_ranges_are_not_expanded(self):
        trace = _parse("NFR-1 and AC-1 through AC-5, UAC-9, AC-7a.\n")
        assert [r.id for r in trace.references] == ["NFR-1", "AC-1", "AC-5"]

    def test_bullet_requirement_does_not_leak_into_next_section(self):
        trace = _parse("- **AC-1**: first\n\n## Next\n\nRequirement: FR-9\n", can_define=True)
        assert trace.definitions["AC-1"][0].requirements == []

    def test_heading_span_stops_at_a_sibling_heading(self):
        trace = _parse("### AC-1: One\n\nbody\n\n### Notes\n\nRequirement: FR-3\n")
        assert trace.definitions["AC-1"][0].requirements == []

    @pytest.mark.parametrize(
        ("row", "expected"),
        [
            ("| FR-1 | AC-1 | Covered | s | t |", True),
            ("| FR-1 | AC-1 | **Deferred** (reason) | s | t |", True),
            ("| FR-1 | AC-1 | unresolved | s | t |", True),
            ("| FR-1 | AC-1 |  | s | t |", False),
            ("| FR-1 | AC-1 | [Covered / deferred / unresolved] | s | t |", False),
        ],
    )
    def test_disposition_cell(self, row, expected):
        assert has_disposition(row) is expected

    def test_only_the_coverage_section_needs_dispositions(self):
        trace = _parse(
            "## Requirements Coverage\n\n| Req | AC | Disposition |\n|---|---|---|\n| FR-1 | AC-1 | |\n\n"
            "## Verification Plan\n\n| AC | Test |\n|---|---|\n| AC-1 | test_x |\n",
            can_define=False,
        )
        assert trace.rows_without_disposition == [(5, ["FR-1", "AC-1"])]


def _project(tmp_path: Path, optin: bool = True, rfc_optin: bool = True) -> Path:
    root = tmp_path / "docs-cms"
    (root / "prd").mkdir(parents=True)
    (root / "rfcs").mkdir()
    prd_flag = "      check_traceability: true\n" if optin else ""
    rfc_flag = "      check_traceability: true\n" if rfc_optin else ""
    (root / "docs-project.yaml").write_text(
        'version: "1"\nproject:\n  id: p\n  name: p\n'
        "structure:\n  document_folders: [prd, rfcs]\n  doc_types:\n"
        f"    prd:\n      schema: prd\n      folders: [prd]\n{prd_flag}"
        f"    rfc:\n      schema: rfc\n      folders: [rfcs]\n{rfc_flag}"
        "readability:\n  enabled: false\n",
        encoding="utf-8",
    )
    return root


def _prd(root: Path, number: int, body: str) -> None:
    (root / "prd" / f"prd-{number:03d}-x.md").write_text(
        f"---\nid: prd-{number:03d}\ntitle: PRD {number}\nstatus: Draft\nauthor: a\ncreated: 2026-01-01\n"
        f"target_release: v1\ntags: []\nproject_id: p\ndoc_uuid: aaaaaaaa-0000-4000-8000-{number:012d}\n---\n\n{body}",
        encoding="utf-8",
    )


def _rfc(root: Path, number: int, body: str) -> None:
    (root / "rfcs" / f"rfc-{number:03d}-x.md").write_text(
        f"---\nid: rfc-{number:03d}\ntitle: RFC {number}\nstatus: Draft\nauthor: a\ncreated: 2026-01-01\n"
        f"tags: []\nproject_id: p\ndoc_uuid: bbbbbbbb-0000-4000-8000-{number:012d}\n---\n\n{body}",
        encoding="utf-8",
    )


def _findings(root: Path) -> list[str]:
    validator = DocValidator(repo_root=root.parent, verbose=False)
    validator.scan_documents()
    validator.extract_links()
    validator.check_traceability()
    return [e for doc in validator.documents for e in doc.errors if e.startswith("TRC-")]


GOOD_PRD = "| FR-1 | One |\n\n### AC-1: One\n\nRequirement: FR-1\n"


class TestCheck:
    def test_clean_pair_is_silent(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "[prd](../prd/prd-001-x.md)\n\n## Requirements Coverage\n\n| FR-1 | AC-1 | Covered |\n")
        assert _findings(root) == []

    def test_off_by_default(self, tmp_path):
        root = _project(tmp_path, optin=False, rfc_optin=False)
        _prd(root, 1, "### AC-1: no requirement\n")
        _rfc(root, 1, "AC-9\n")
        assert _findings(root) == []

    def test_unlinked_rfc_resolves_against_the_one_prd_that_defines_the_id(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "## Requirements Coverage\n\n| FR-1 | AC-1 | Covered |\n")
        assert _findings(root) == []

    def test_a_reference_defined_only_in_an_unlinked_prd_is_dangling(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _prd(root, 2, "| FR-5 | Five |\n\n### AC-5: Five\n\nRequirement: FR-5\n")
        _rfc(root, 1, "[prd](../prd/prd-001-x.md)\n\nAC-5\n")
        findings = _findings(root)
        assert any("AC-5 is not defined in a linked requirements document (prd-001-x.md)" in f for f in findings)

    def test_prd_whose_rfc_type_is_not_opted_in_still_defines(self, tmp_path):
        root = _project(tmp_path, rfc_optin=False)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "AC-9\n")
        assert _findings(root) == []

    def test_unclaimed_prd_is_not_a_wall_of_trc004(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        assert _findings(root) == []

    def test_nfr_is_exempt_from_orphan_and_untested_checks(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n| NFR-1 | Fast |\n")
        _rfc(root, 1, "[prd](../prd/prd-001-x.md)\n\n## Requirements Coverage\n\n| FR-1 | AC-1 | Covered |\n")
        assert _findings(root) == []

    def test_prd_without_criteria_is_not_asked_for_them(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, "| FR-1 | One |\n| FR-2 | Two |\n")
        assert _findings(root) == []

    def test_criterion_in_an_frd_can_name_a_requirement_in_the_prd(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, "| FR-1 | One |\n\n### AC-1: PRD criterion\n\nRequirement: FR-1\n\n| FR-2 | Two |\n")
        (root / "prd" / "prd-002-frd.md").write_text(
            "---\nid: prd-002\ntitle: FRD\nstatus: Draft\nauthor: a\ncreated: 2026-01-01\ntarget_release: v1\n"
            "tags: []\nproject_id: p\ndoc_uuid: aaaaaaaa-0000-4000-8000-000000000002\n---\n\n"
            "[parent](prd-001-x.md)\n\n### AC-7: FRD criterion\n\nRequirement: FR-2\n",
            encoding="utf-8",
        )
        assert _findings(root) == []

    def test_each_unresolved_id_is_reported_once(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "AC-4 then AC-4 then AC-4\n")
        assert len([f for f in _findings(root) if f.startswith("TRC-001")]) == 1


def test_config_flag_defaults_to_false_and_loads():
    config = DocsProjectConfig.model_validate(
        {
            "version": "1",
            "project": {"id": "p", "name": "p"},
            "structure": {"doc_types": {"prd": {"schema": "prd", "folders": ["prd"], "check_traceability": True}}},
        }
    )
    assert config.structure.doc_types["prd"].check_traceability is True
    plain = DocsProjectConfig.model_validate(
        {"version": "1", "project": {"id": "p", "name": "p"}, "structure": {"doc_types": {"adr": {"schema": "adr"}}}}
    )
    assert plain.structure.doc_types["adr"].check_traceability is False


class TestShippedTemplates:
    """The templates' own ID placeholders must parse the way the guide says."""

    def test_prd_template_defines_a_traceable_criterion(self):
        text = (TEMPLATES / "prd-000-template.md").read_text(encoding="utf-8")
        trace = _parse(text)
        assert {"FR-1", "FR-2", "FR-3", "NFR-1", "AC-1"} <= set(trace.definitions)
        assert trace.definitions["AC-1"][0].requirements == ["FR-1"]

    def test_detailed_prd_and_frd_use_the_same_requirement_keyword(self):
        for name in ("prd-template.md", "frd-template.md"):
            trace = _parse((DETAILED_TEMPLATES / name).read_text(encoding="utf-8"))
            criteria = [d for defs in trace.definitions.values() for d in defs if d.id.startswith("AC-")]
            assert criteria, name
            assert all(d.requirements for d in criteria), name

    def test_rfc_templates_have_a_coverage_row_that_asks_for_a_disposition(self):
        for path in (TEMPLATES / "rfc-000-template.md", DETAILED_TEMPLATES / "rfc-template.md"):
            trace = _parse(path.read_text(encoding="utf-8"), can_define=False)
            assert trace.definitions == {}, path
            assert trace.rows_without_disposition, f"{path}: unfilled placeholder row should be flagged"

    def test_worked_example_in_the_guide_is_internally_consistent(self):
        trace = _parse((REPO_ROOT / "docs" / "ACCEPTANCE_CRITERIA.md").read_text(encoding="utf-8"))
        assert sorted(trace.definitions) == ["AC-1", "AC-2", "AC-3", "FR-1", "FR-2"]
        assert [d.requirements for d in (trace.definitions[i][0] for i in ("AC-1", "AC-2", "AC-3"))] == [["FR-1"]] * 3
