"""Requirement traceability: the parser and the opt-in TRC-001..005 check.

The reproductions a review supplied against the first version are kept here
by name, so the defects they exposed stay fixed.
"""

from pathlib import Path

import pytest

from docuchango.markdown import mask_code
from docuchango.schemas import DocsProjectConfig, RFCFrontmatter
from docuchango.traceability import _cells, has_disposition, parse_traceability
from docuchango.validator import DocValidator

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "docuchango" / "templates"
DETAILED_TEMPLATES = REPO_ROOT / "templates"

ID_TABLE = "| ID | Requirement | Priority |\n|---|---|---|\n"
COVERAGE = (
    "| Source requirement | Acceptance criterion | Disposition | Design | Verification |\n|---|---|---|---|---|\n"
)


def _parse(text: str):
    return parse_traceability(mask_code(text, strip_frontmatter=True))


class TestDefinitions:
    @pytest.mark.parametrize("column", ["Scope", "Status", "Priority"])
    @pytest.mark.parametrize("value", ["Deferred", "Deferred to v2", "Out of scope (future)", "Descoped: agreed"])
    def test_trc004_trc005_explicit_deferral_columns(self, column, value):
        trace = _parse(f"| ID | Requirement | {column} |\n|---|---|---|\n| FR-1 | Export | {value} |\n")
        assert trace.is_deferred("FR-1")

    @pytest.mark.parametrize("value", ["Not deferred", "Deferredness", "Must", "Potentially deferred"])
    def test_trc004_trc005_non_deferral_values(self, value):
        trace = _parse(ID_TABLE + f"| FR-1 | Export | {value} |\n")
        assert not trace.is_deferred("FR-1")

    def test_heading_bullet_and_id_table(self):
        trace = _parse(
            ID_TABLE + "| FR-1 | One | Must |\n| **NFR-1** | Two | Must |\n\n"
            "### AC-1: Heading form\n\nRequirement: FR-1\n\n"
            "- [ ] **AC-2** (Requirement: FR-1, FR-2): bullet form\n"
            "1. **FR-2**: numbered form\n"
        )
        assert sorted(trace.definitions) == ["AC-1", "AC-2", "FR-1", "FR-2", "NFR-1"]
        assert trace.definitions["AC-1"][0].requirements == ["FR-1"]
        assert trace.definitions["AC-2"][0].requirements == ["FR-1", "FR-2"]

    def test_review_1_dotted_ids_are_distinct(self):
        trace = _parse("### AC-1.1: First\n\n### AC-1.2: Second\n\nSee AC-1.\n")
        assert sorted(trace.definitions) == ["AC-1.1", "AC-1.2"]
        assert [r.id for r in trace.references] == ["AC-1"]

    def test_review_2_any_document_defines_by_form(self):
        """There is no per-schema switch: an RFC's local FR-1 is a definition."""
        trace = _parse(ID_TABLE + "| FR-1 | Local requirement | Must |\n\n### AC-1: Local\n\nRequirement: FR-1\n")
        assert sorted(trace.definitions) == ["AC-1", "FR-1"]

    def test_coverage_and_source_tables_cite_rather_than_define(self):
        trace = _parse(
            COVERAGE + "| FR-1 | AC-1 | Covered | s | t |\n\n| Source | Criterion |\n|---|---|\n| FR-2 | AC-2 |\n"
        )
        assert trace.definitions == {}
        assert [r.id for r in trace.references] == ["FR-1", "AC-1", "FR-2", "AC-2"]

    def test_table_without_an_id_header_does_not_define(self):
        """A risks table that happens to start a row with an ID is a citation (second-pass finding)."""
        trace = _parse(
            ID_TABLE + "| FR-1 | One | Must |\n\n| Risk | Mitigation |\n|---|---|\n| FR-1 | could regress |\n"
        )
        assert len(trace.definitions["FR-1"]) == 1
        assert [r.id for r in trace.references] == ["FR-1"]

    def test_deferred_row(self):
        trace = _parse(
            ID_TABLE + "| FR-1 | One | Must |\n| FR-2 | Two | Deferred to v2 |\n| FR-3 | Three | Out of scope |\n"
        )
        assert not trace.is_deferred("FR-1")
        assert trace.is_deferred("FR-2") and trace.is_deferred("FR-3")

    def test_own_definition_is_not_a_reference_but_repeats_are(self):
        trace = _parse("### AC-1: Title mentions AC-1 again\n\nSee AC-1.\n")
        assert [r.line for r in trace.references] == [1, 3]

    def test_code_and_html_comments_are_ignored(self):
        trace = _parse("Real AC-1 and `AC-2` inline. <!-- AC-3 -->\n\n```\nAC-4\n```\n<!--\nAC-5\n-->\n")
        assert [r.id for r in trace.references] == ["AC-1"]

    def test_nfr_does_not_yield_fr(self):
        trace = _parse("NFR-1, UAC-9, AC-7a.\n")
        assert [r.id for r in trace.references] == ["NFR-1"]


class TestRequirementClause:
    def test_trc005_qualified_requirement_clause_preserves_source(self):
        trace = _parse("### AC-1: Local\nRequirement: prd-001::FR-1, prd-002::NFR-1\n")
        assert trace.definitions["AC-1"][0].requirements == ["prd-001::FR-1", "prd-002::NFR-1"]

    def test_review_5_a_criterion_cannot_name_a_criterion(self):
        trace = _parse("### AC-1: First\n\nRequirement: AC-2\n\n### AC-2: Second\n\nRequirement: FR-1\n")
        assert trace.definitions["AC-1"][0].requirements == []
        assert trace.definitions["AC-2"][0].requirements == ["FR-1"]

    def test_clause_is_bounded_to_its_line_and_bracket(self):
        trace = _parse(
            "### AC-1: x\n\nRequirement: FR-1 and FR-2 (see FR-3)\n\n- **Given** a user with FR-4 access\n"
            "- [ ] **AC-2** (Requirement: NFR-1): **Given** FR-5 **Then** ok\n"
        )
        assert trace.definitions["AC-1"][0].requirements == ["FR-1", "FR-2"]
        assert trace.definitions["AC-2"][0].requirements == ["NFR-1"]

    def test_span_stops_at_sibling_heading_and_next_unindented_line(self):
        trace = _parse("### AC-1: One\n\n### Notes\n\nRequirement: FR-3\n\n- **AC-2**: two\n\nRequirement: FR-9\n")
        assert trace.definitions["AC-1"][0].requirements == []
        assert trace.definitions["AC-2"][0].requirements == []


class TestCoverageRows:
    @pytest.mark.parametrize(
        ("row", "expected"),
        [
            ("|| AC-1 | Covered | design | test |", ["", "AC-1", "Covered", "design", "test"]),
            (r"| FR-1 | Accept A \| B | Deferred |", ["FR-1", r"Accept A \| B", "Deferred"]),
            ("| a ||", ["a", ""]),
            (r"| a \\| b |", [r"a \\", "b"]),
        ],
    )
    def test_trc003_table_cell_boundaries(self, row, expected):
        assert _cells(row) == expected

    def test_trc003_empty_source_cell_keeps_disposition_column(self):
        trace = _parse(COVERAGE + "|| AC-1 | Covered | design | test |\n")
        assert trace.rows_without_disposition == []

    def test_trc004_trc005_escaped_pipe_preserves_deferral(self):
        trace = _parse(ID_TABLE + r"| FR-1 | Accept A \| B | Deferred |" + "\n")
        assert trace.is_deferred("FR-1")

    @pytest.mark.parametrize(
        ("cell", "expected"),
        [
            ("Covered", True),
            ("**Deferred** (reason)", True),
            ("unresolved", True),
            ("", False),
            ("[Covered / deferred / unresolved]", False),
            ("TBD", False),
            ("Covered (unit/integration tests)", True),
            ("Deferred: [decision](../adr/adr-002.md)", True),
            ("**Covered** (unit/integration tests)", True),
            ("Covered/deferred", False),
            ("**Covered** / **Unresolved**", False),
            ("Coveredness", False),
        ],
    )
    def test_disposition_cell(self, cell, expected):
        assert has_disposition(cell) is expected

    def test_review_4_disposition_is_read_from_its_column(self):
        trace = _parse(COVERAGE + "| FR-1 | AC-1 | | Covered by parser | test |\n| FR-1 | AC-2 | Covered | | |\n")
        assert trace.rows_without_disposition == [(3, ["FR-1", "AC-1"])]

    def test_table_without_disposition_column_is_not_a_coverage_table(self):
        trace = _parse("## Verification Plan\n\n| AC | Test |\n|---|---|\n| AC-1 | test_x |\n")
        assert trace.rows_without_disposition == []


class TestRanges:
    def test_range_operators(self):
        trace = _parse("AC-1 through AC-3, FR-2 to FR-4, AC-5..AC-6, NFR-1–NFR-2\n")
        assert [(r.prefix, r.lo, r.hi) for r in trace.ranges] == [
            ("AC", 1, 3),
            ("FR", 2, 4),
            ("AC", 5, 6),
            ("NFR", 1, 2),
        ]

    def test_mixed_prefix_dotted_and_hyphen_are_not_ranges(self):
        trace = _parse("FR-1 to AC-3; AC-1.1 through AC-1.3; AC-1-AC-3\n")
        assert trace.ranges == []


def _project(tmp_path: Path, optin: bool = True) -> Path:
    root = tmp_path / "docs-cms"
    (root / "prd").mkdir(parents=True)
    (root / "rfcs").mkdir()
    flag = "      check_traceability: true\n" if optin else ""
    (root / "docs-project.yaml").write_text(
        'version: "1"\nproject:\n  id: p\n  name: p\n'
        "structure:\n  document_folders: [prd, rfcs]\n  doc_types:\n"
        f"    prd:\n      schema: prd\n      folders: [prd]\n{flag}"
        f"    rfc:\n      schema: rfc\n      folders: [rfcs]\n{flag}"
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


def _rfc(root: Path, number: int, body: str, implements: str | None = None) -> None:
    imp = f"implements: {implements}\n" if implements else ""
    (root / "rfcs" / f"rfc-{number:03d}-x.md").write_text(
        f"---\nid: rfc-{number:03d}\ntitle: RFC {number}\nstatus: Draft\nauthor: a\ncreated: 2026-01-01\n"
        f"tags: []\n{imp}project_id: p\ndoc_uuid: bbbbbbbb-0000-4000-8000-{number:012d}\n---\n\n{body}",
        encoding="utf-8",
    )


def _findings(root: Path) -> list[str]:
    validator = DocValidator(repo_root=root.parent, verbose=False)
    validator.scan_documents()
    validator.extract_links()
    validator.check_traceability()
    return [e for doc in validator.documents for e in doc.errors if e.startswith("TRC-")]


GOOD_PRD = ID_TABLE + "| FR-1 | One | Must |\n\n### AC-1: One\n\nRequirement: FR-1\n"
GOOD_RFC = COVERAGE + "| FR-1 | AC-1 | Covered | d | t |\n"


class TestCheck:
    def test_trc003_slash_explanations_and_empty_cells_validate_end_to_end(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, COVERAGE + "|| AC-1 | Covered (unit/integration tests) | design | test |\n", "[prd-001]")
        assert _findings(root) == []

    def test_trc004_trc005_escaped_description_keeps_deferred_scope(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n" + ID_TABLE + r"| FR-2 | Accept A \| B | Deferred |" + "\n")
        _rfc(root, 1, GOOD_RFC, "[prd-001]")
        assert _findings(root) == []

    @pytest.mark.parametrize("reference", ["FR-1", "prd-002::FR-1"])
    def test_trc001_empty_declared_source_does_not_fall_back(self, tmp_path, reference):
        root = _project(tmp_path)
        _prd(root, 1, "Requirements not numbered yet.\n")
        _prd(root, 2, GOOD_PRD)
        _rfc(root, 1, f"See {reference}.\n", "[prd-001]")
        findings = _findings(root)
        assert len(findings) == 1
        assert "TRC-001" in findings[0] and "implemented document (prd-001-x.md)" in findings[0]

    @pytest.mark.parametrize("background", ["FR-1 and AC-1", "AC-1 through AC-1"])
    def test_trc004_background_cannot_cover_an_implementer(self, tmp_path, background):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "Design pending.\n", "[prd-001]")
        _rfc(root, 2, f"Background: {background}.\n")
        findings = _findings(root)
        assert len(findings) == 2
        assert all(f.startswith("TRC-004") for f in findings)

    @pytest.mark.parametrize(
        "description", ["Deferred execution must preserve files", "This requirement is not deferred"]
    )
    def test_trc004_trc005_description_does_not_defer_requirement(self, tmp_path, description):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n" + ID_TABLE + f"| FR-2 | {description} | Must |\n")
        _rfc(root, 1, GOOD_RFC, "[prd-001]")
        findings = _findings(root)
        assert len(findings) == 2
        assert any(f.startswith("TRC-004") and "FR-2" in f for f in findings)
        assert any(f.startswith("TRC-005") and "FR-2" in f for f in findings)

    def test_trc001_qualified_references_resolve_colliding_ids(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _prd(root, 2, GOOD_PRD)
        _rfc(
            root,
            1,
            COVERAGE + "| prd-001::FR-1 | prd-001::AC-1 | Covered | d | t |\n"
            "| prd-002::FR-1 | prd-002::AC-1 | Covered | d | t |\n",
            "[prd-001, prd-002]",
        )
        assert _findings(root) == []

    def test_trc001_qualified_reference_cannot_bypass_declared_scope(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _prd(root, 2, GOOD_PRD)
        _rfc(root, 1, GOOD_RFC + "\nSee prd-002::AC-1.\n", "[prd-001]")
        findings = _findings(root)
        assert len(findings) == 1
        assert findings[0].startswith("TRC-001") and "prd-002::AC-1" in findings[0]

    def test_trc001_qualified_unknown_source_is_reported(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "See prd-999::AC-1.\n")
        findings = _findings(root)
        assert len(findings) == 1 and "TRC-001" in findings[0] and "prd-999::AC-1" in findings[0]

    def test_trc004_qualified_ranges_and_indirect_coverage(self, tmp_path):
        root = _project(tmp_path)
        for number in (1, 2):
            _prd(root, number, GOOD_PRD + "\n### AC-2: Two\nRequirement: FR-1\n")
        _rfc(
            root,
            1,
            "Covers prd-001::AC-1 through prd-001::AC-2.\nCovers prd-002::AC-1 through prd-002::AC-2.\n",
            "[prd-001, prd-002]",
        )
        assert _findings(root) == []

    def test_clean_pair_is_silent(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, GOOD_RFC, "[prd-001]")
        assert _findings(root) == []

    def test_off_by_default(self, tmp_path):
        root = _project(tmp_path, optin=False)
        _prd(root, 1, "### AC-1: no requirement\n")
        _rfc(root, 1, "AC-9\n")
        assert _findings(root) == []

    def test_review_3_a_background_link_claims_nothing(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n### AC-2: Two\n\nRequirement: FR-1\n")
        _rfc(root, 1, "Background: [related proposal](../prd/prd-001-x.md).\n")
        assert _findings(root) == []

    def test_implements_claims_the_document(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n### AC-2: Two\n\nRequirement: FR-1\n")
        _rfc(root, 1, GOOD_RFC, "[prd-001]")
        findings = _findings(root)
        assert (
            len(findings) == 1
            and "TRC-004" in findings[0]
            and "AC-2 is not covered or deferred by rfc-001-x.md" in findings[0]
        )

    def test_implements_scalar_and_unknown_id(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, GOOD_RFC, "prd-001")
        _rfc(root, 2, GOOD_RFC, "[prd-009]")
        findings = _findings(root)
        assert len(findings) == 3
        assert "frontmatter implements names 'prd-009'" in findings[0]
        assert all("cannot resolve because no implements target resolved" in f for f in findings[1:])

    def test_review_2_standalone_rfc_defines_its_own_requirements(self, tmp_path):
        root = _project(tmp_path)
        _rfc(root, 1, GOOD_PRD + "\n" + GOOD_RFC)
        assert _findings(root) == []

    def test_unlinked_rfc_resolves_against_the_one_definer(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, GOOD_RFC)
        assert _findings(root) == []

    def test_two_definers_without_implements_is_ambiguous(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _prd(root, 2, GOOD_PRD)
        _rfc(root, 1, GOOD_RFC)
        findings = _findings(root)
        assert all("TRC-001" in f and "add frontmatter implements" in f for f in findings) and len(findings) == 2

    def test_implements_disambiguates(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _prd(root, 2, GOOD_PRD)
        _rfc(root, 1, GOOD_RFC, "[prd-002]")
        assert _findings(root) == []

    def test_requirement_covered_when_its_criterion_is_cited(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "- AC-1: covered by the export path.\n", "[prd-001]")
        assert _findings(root) == []

    def test_deferred_requirement_needs_no_criterion_or_coverage(self, tmp_path):
        root = _project(tmp_path)
        _prd(
            root,
            1,
            ID_TABLE + "| FR-1 | One | Must |\n| FR-2 | Two | Deferred |\n\n### AC-1: One\n\nRequirement: FR-1\n",
        )
        _rfc(root, 1, GOOD_RFC, "[prd-001]")
        assert _findings(root) == []

    def test_range_resolves_against_definitions(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n### AC-2: Two\n\nRequirement: FR-1\n\n### AC-4: Four\n\nRequirement: FR-1\n")
        _rfc(root, 1, "Covers AC-1 through AC-4.\n", "[prd-001]")
        assert _findings(root) == []

    def test_range_endpoint_must_still_resolve(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "Covers AC-1 through AC-4.\n", "[prd-001]")
        findings = _findings(root)
        assert len(findings) == 1 and "TRC-001" in findings[0] and "AC-4 is not defined" in findings[0]

    def test_nfr_is_orphan_checked_but_needs_no_criterion(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n| ID | Requirement | Target |\n|---|---|---|\n| NFR-1 | Fast | p95 2s |\n")
        _rfc(root, 1, GOOD_RFC, "[prd-001]")
        findings = _findings(root)
        assert len(findings) == 1 and "TRC-004" in findings[0] and "NFR-1" in findings[0]
        _rfc(root, 1, GOOD_RFC + "| NFR-1 | measured | Covered | d | benchmark |\n", "[prd-001]")
        assert _findings(root) == []

    def test_unclaimed_prd_is_not_a_wall_of_trc004(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD + "\n### AC-2: Two\n\nRequirement: FR-1\n")
        assert _findings(root) == []

    def test_prd_without_criteria_is_not_asked_for_them(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, ID_TABLE + "| FR-1 | One | Must |\n| FR-2 | Two | Must |\n")
        assert _findings(root) == []

    def test_each_unresolved_id_is_reported_once(self, tmp_path):
        root = _project(tmp_path)
        _prd(root, 1, GOOD_PRD)
        _rfc(root, 1, "AC-4 then AC-4 then AC-4\n", "[prd-001]")
        assert len([f for f in _findings(root) if f.startswith("TRC-001")]) == 1


def test_config_flag_and_implements_field():
    config = DocsProjectConfig.model_validate(
        {
            "version": "1",
            "project": {"id": "p", "name": "p"},
            "structure": {"doc_types": {"prd": {"schema": "prd", "folders": ["prd"], "check_traceability": True}}},
        }
    )
    assert config.structure.doc_types is not None
    assert config.structure.doc_types["prd"].check_traceability is True
    plain = DocsProjectConfig.model_validate(
        {"version": "1", "project": {"id": "p", "name": "p"}, "structure": {"doc_types": {"adr": {"schema": "adr"}}}}
    )
    assert plain.structure.doc_types is not None
    assert plain.structure.doc_types["adr"].check_traceability is False
    rfc = RFCFrontmatter.model_validate(
        {
            "title": "Long enough title",
            "status": "Draft",
            "author": "a",
            "created": "2026-01-01",
            "tags": ["x"],
            "id": "rfc-001",
            "project_id": "p",
            "doc_uuid": "bbbbbbbb-0000-4000-8000-000000000001",
            "implements": ["prd-001"],
        }
    )
    assert rfc.implements == ["prd-001"]


class TestShippedTemplates:
    """The templates' own ID placeholders must parse the way the guide says."""

    def test_prd_template_defines_a_traceable_criterion(self):
        trace = _parse((TEMPLATES / "prd-000-template.md").read_text(encoding="utf-8"))
        assert {"FR-1", "FR-2", "FR-3", "NFR-1", "AC-1"} <= set(trace.definitions)
        assert trace.definitions["AC-1"][0].requirements == ["FR-1"]

    def test_detailed_prd_and_frd_use_the_same_requirement_keyword(self):
        for name in ("prd-template.md", "frd-template.md"):
            trace = _parse((DETAILED_TEMPLATES / name).read_text(encoding="utf-8"))
            criteria = [d for defs in trace.definitions.values() for d in defs if d.id.startswith("AC-")]
            assert criteria, name
            assert all(d.requirements for d in criteria), name

    def test_rfc_templates_placeholder_row_is_flagged_and_implements_hinted(self):
        for path in (TEMPLATES / "rfc-000-template.md", DETAILED_TEMPLATES / "rfc-template.md"):
            text = path.read_text(encoding="utf-8")
            trace = _parse(text)
            assert trace.rows_without_disposition, f"{path}: unfilled placeholder row should be flagged"
            assert "implements:" in text, path

    def test_worked_example_in_the_guide_is_internally_consistent(self):
        trace = _parse((REPO_ROOT / "docs" / "ACCEPTANCE_CRITERIA.md").read_text(encoding="utf-8"))
        assert sorted(trace.definitions) == ["AC-1", "AC-2", "AC-3", "FR-1", "FR-2"]
        assert trace.is_deferred("FR-2"), "the example defers FR-2 in its Scope column"
        assert [trace.definitions[i][0].requirements for i in ("AC-1", "AC-2", "AC-3")] == [["FR-1"]] * 3
