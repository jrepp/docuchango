"""Fixture-driven regression harness for the finding registry in RFC-003.

Every check that ``docuchango validate`` performs has a stable finding ID
(``FM-002``, ``LNK-001``, ``FMT-010``, ...) registered in the table in
``docs-cms/rfcs/rfc-003-validator-roadmap.md``. This module turns that
registry into an executable contract:

* Each directory under ``tests/fixtures/findings/`` is a miniature repository
  that reproduces exactly one finding, plus an ``expected.yaml`` describing
  what ``validate`` should say about it.
* Every fixture is run twice through the real Click command -- once with
  ``--dry-run`` and once without -- against a throwaway copy under
  ``tmp_path``.
* A fixture whose registry row is still ``Planned`` is collected as a *strict*
  xfail, so a planned check can ship its fixture early and the suite turns red
  the moment the check lands without the registry row being flipped.
* ``test_every_implemented_id_has_a_fixture`` keeps the registry and the suite
  from drifting apart in the other direction.

Adding a failure case is dropping in a directory; adding a validator is a
fixture plus a registry row. See ``tests/fixtures/findings/README.md``.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner, Result

from docuchango.cli import validate

REPO_ROOT = Path(__file__).resolve().parent.parent
FINDINGS_DIR = Path(__file__).resolve().parent / "fixtures" / "findings"
REGISTRY_DOC = REPO_ROOT / "docs-cms" / "rfcs" / "rfc-003-validator-roadmap.md"

#: Directory names are ``<AREA>-<NNN>`` with an optional ``-slug`` suffix, so
#: one finding ID can own several cases (``FM-002-invalid-status``,
#: ``FM-002-missing-title``).
CASE_DIR_RE = re.compile(r"^(?P<finding_id>[A-Z]+-\d{3})(?:-(?P<slug>.+))?$")

#: Rows of the registry table in RFC-003.
REGISTRY_ROW_RE = re.compile(
    r"^\|\s*(?P<finding_id>[A-Z]+-\d{3})\s*\|"
    r"\s*(?P<check>[^|]*?)\s*\|"
    r"\s*(?P<status>Implemented|Planned|Rejected)\s*\|"
    r"\s*(?P<mode>[^|]*?)\s*\|"
    r"\s*(?P<where>[^|]*?)\s*\|\s*$"
)

#: A fixture that supplies no ``docs-project.yaml`` of its own gets this one.
DEFAULT_PROJECT_CONFIG = """version: "1"
project:
  id: fixture-project
  name: Fixture Project
  description: Synthetic project used by the finding regression fixtures
structure:
  adr_dir: adr
  rfc_dir: rfcs
  memo_dir: memos
  document_folders:
    - adr
    - rfcs
    - memos
security:
  allow_external_paths: false
readability:
  enabled: false
"""


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RegistryRow:
    """One row of the finding registry in RFC-003."""

    finding_id: str
    check: str
    status: str
    mode: str
    where: str

    @property
    def is_implemented(self) -> bool:
        return self.status == "Implemented"


def load_registry() -> dict[str, RegistryRow]:
    """Parse the finding registry table out of RFC-003."""
    rows: dict[str, RegistryRow] = {}
    for line in REGISTRY_DOC.read_text(encoding="utf-8").splitlines():
        match = REGISTRY_ROW_RE.match(line)
        if not match:
            continue
        row = RegistryRow(
            finding_id=match.group("finding_id"),
            check=match.group("check"),
            status=match.group("status"),
            mode=match.group("mode"),
            where=match.group("where"),
        )
        rows[row.finding_id] = row
    return rows


REGISTRY = load_registry()


# --------------------------------------------------------------------------
# Case discovery
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FindingCase:
    """One fixture directory plus the expectations recorded alongside it."""

    name: str
    path: Path
    finding_id: str | None
    expected: dict[str, Any]

    @property
    def summary(self) -> str:
        return str(self.expected.get("summary", "")).strip()

    @property
    def messages(self) -> list[str]:
        return list(self.expected.get("messages") or [])

    @property
    def fix_messages(self) -> list[str]:
        return list(self.expected.get("fix_messages") or [])

    @property
    def forbidden(self) -> list[str]:
        return list(self.expected.get("forbidden") or [])

    @property
    def fixed(self) -> bool:
        return bool(self.expected.get("fixed", False))

    @property
    def dry_run_exit_code(self) -> int:
        return int(self.expected["dry_run_exit_code"])

    @property
    def exit_code(self) -> int:
        return int(self.expected["exit_code"])

    @property
    def requires(self) -> list[str]:
        """Optional third-party modules this case needs (e.g. ``textstat``)."""
        return list(self.expected.get("requires") or [])

    @property
    def registry_row(self) -> RegistryRow | None:
        return REGISTRY.get(self.finding_id) if self.finding_id else None

    @property
    def is_planned(self) -> bool:
        row = self.registry_row
        return row is not None and not row.is_implemented


def discover_cases(include_unkeyed: bool = False) -> list[FindingCase]:
    """Collect fixture directories under ``tests/fixtures/findings``.

    Directories whose name starts with an underscore are support cases such as
    ``_baseline`` and are not keyed to a finding ID; they are returned only
    when ``include_unkeyed`` is set.
    """
    cases: list[FindingCase] = []
    if not FINDINGS_DIR.is_dir():
        return cases
    for path in sorted(FINDINGS_DIR.iterdir()):
        if not path.is_dir():
            continue
        expected_path = path / "expected.yaml"
        if not expected_path.is_file():
            continue
        match = CASE_DIR_RE.match(path.name)
        finding_id = match.group("finding_id") if match else None
        if finding_id is None and not include_unkeyed:
            continue
        expected = yaml.safe_load(expected_path.read_text(encoding="utf-8")) or {}
        cases.append(FindingCase(name=path.name, path=path, finding_id=finding_id, expected=expected))
    return cases


KEYED_CASES = discover_cases()
ALL_CASES = discover_cases(include_unkeyed=True)


def covered_finding_ids() -> set[str]:
    """The set of finding IDs that own at least one fixture directory."""
    return {case.finding_id for case in KEYED_CASES if case.finding_id is not None}


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):  # pragma: no cover - defensive
        return False


def _requires_marks(case: FindingCase) -> list[Any]:
    return [
        pytest.mark.skipif(not _module_available(module), reason=f"{case.name} needs the {module} package")
        for module in case.requires
    ]


def _planned_reason(case: FindingCase) -> str:
    row = case.registry_row
    assert row is not None
    return f"{case.finding_id} is {row.status} in RFC-003. Flip the registry row to Implemented once the check lands."


def _params(cases: list[FindingCase], planned_mark: str) -> list[Any]:
    """Build parametrize arguments, marking the cases that are still Planned.

    ``planned_mark`` is ``"xfail"`` for the detection test -- the strict xfail
    is exactly the tripwire that turns red when a planned check starts working
    -- and ``"skip"`` for the tests whose subject (repair behaviour) has no
    meaning before the check exists.
    """
    params = []
    for case in cases:
        marks = _requires_marks(case)
        if case.is_planned:
            reason = _planned_reason(case)
            if planned_mark == "xfail":
                marks.append(pytest.mark.xfail(strict=True, reason=reason))
            else:
                marks.append(pytest.mark.skip(reason=reason))
        params.append(pytest.param(case, id=case.name, marks=marks))
    return params


#: Detection: a Planned finding must NOT be reported yet, so a strict xfail.
DETECTION_PARAMS = _params(ALL_CASES, planned_mark="xfail")
#: Repair semantics: undefined before the check exists, so Planned cases skip.
FIX_PARAMS = _params(ALL_CASES, planned_mark="skip")
#: Idempotence holds for every fixture regardless of registry status.
IDEMPOTENCE_PARAMS = [pytest.param(c, id=c.name, marks=_requires_marks(c)) for c in ALL_CASES]


# --------------------------------------------------------------------------
# Running a case
# --------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Collapse whitespace so Rich's console wrapping cannot break matching."""
    return re.sub(r"\s+", " ", text)


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def _stage(case: FindingCase, tmp_path: Path) -> Path:
    """Copy a fixture into ``tmp_path`` as a standalone repository root.

    ``tmp_path`` is deliberately not resolved: on macOS it goes through the
    ``/var`` symlink, which is exactly the shape of ``--repo-root`` that
    ``validate`` must handle without raising.
    """
    root = tmp_path / "repo"
    shutil.copytree(case.path, root)
    (root / "expected.yaml").unlink(missing_ok=True)
    if not any(root.rglob("docs-project.yaml")):
        target = root / "docs-cms" if (root / "docs-cms").is_dir() else root
        (target / "docs-project.yaml").write_text(DEFAULT_PROJECT_CONFIG, encoding="utf-8")
    return root


def _run_validate(root: Path, dry_run: bool) -> Result:
    args = ["--repo-root", str(root), "--skip-build"]
    if dry_run:
        args.append("--dry-run")
    # A wide console keeps Rich from hard-wrapping long finding messages.
    return CliRunner().invoke(validate, args, env={"COLUMNS": "200"}, catch_exceptions=False)


def _assert_contains(output: str, needles: list[str], case: FindingCase, context: str) -> None:
    normalized = _normalize(output)
    missing = [n for n in needles if _normalize(n) not in normalized]
    assert not missing, (
        f"{case.name} ({context}): expected message(s) not reported: {missing}\n--- output ---\n{output}"
    )


#: Implemented findings that a Markdown-only fixture cannot exercise today,
#: each with the reason and where the check is covered instead. Adding to this
#: set is a deliberate act, and ``test_known_gaps_are_still_gaps`` makes sure
#: an entry is removed once a fixture appears.
KNOWN_GAPS: set[str] = {
    # Phase 1 fills these in before Phase 2 could ever report them, so a
    # fixture can only ever observe the repair, never the finding. Covered by
    # tests/test_whitespace_fixes.py and tests/test_frontmatter_fixes.py.
    "FM-005",
    "FM-006",
    # Needs Node.js and the @mdx-js/mdx toolchain on PATH. The harness stays
    # hermetic; covered by tests/test_mdx_syntax.py at the unit level.
    "MDX-002",
    # Needs a configured `documents.indexes` entry and an index file whose
    # buckets can drift. Covered by tests/test_document_indexes.py.
    "IDX-001",
    # Both need a real Docusaurus site and are skipped by --skip-build, which
    # every fixture run passes.
    "BLD-001",
    "BLD-002",
}


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case", DETECTION_PARAMS)
def test_finding_dry_run_reports_it(case: FindingCase, tmp_path: Path) -> None:
    """``validate --dry-run`` reports the finding and changes nothing on disk."""
    root = _stage(case, tmp_path)
    before = _tree_snapshot(root)

    result = _run_validate(root, dry_run=True)

    assert result.exit_code == case.dry_run_exit_code, (
        f"{case.name}: --dry-run exit code {result.exit_code}, expected {case.dry_run_exit_code}\n{result.output}"
    )
    _assert_contains(result.output, case.messages, case, "--dry-run")
    for needle in case.forbidden:
        assert _normalize(needle) not in _normalize(result.output), (
            f"{case.name}: --dry-run reported a message it should not: {needle!r}\n{result.output}"
        )
    assert _tree_snapshot(root) == before, f"{case.name}: --dry-run modified files on disk"


@pytest.mark.parametrize("case", FIX_PARAMS)
def test_finding_fix_behaviour(case: FindingCase, tmp_path: Path) -> None:
    """``validate`` repairs the finding, or keeps reporting it, as declared."""
    root = _stage(case, tmp_path)

    result = _run_validate(root, dry_run=False)

    assert result.exit_code == case.exit_code, (
        f"{case.name}: exit code {result.exit_code}, expected {case.exit_code}\n{result.output}"
    )
    _assert_contains(result.output, case.fix_messages, case, "fix")

    normalized = _normalize(result.output)
    if case.fixed:
        still_there = [m for m in case.messages if _normalize(m) in normalized]
        assert not still_there, (
            f"{case.name}: expected validate to repair the finding, but it is still reported: "
            f"{still_there}\n{result.output}"
        )
    else:
        _assert_contains(result.output, case.messages, case, "fix (report-only)")


@pytest.mark.parametrize("case", IDEMPOTENCE_PARAMS)
def test_finding_fix_is_idempotent(case: FindingCase, tmp_path: Path) -> None:
    """Running ``validate`` twice reaches a fixed point."""
    root = _stage(case, tmp_path)

    _run_validate(root, dry_run=False)
    after_first = _tree_snapshot(root)
    _run_validate(root, dry_run=False)

    assert _tree_snapshot(root) == after_first, f"{case.name}: a second validate run changed files again"


# --- registry / suite consistency -----------------------------------------


def test_registry_is_parseable() -> None:
    """RFC-003 still contains a registry table this harness can read."""
    assert REGISTRY, f"no finding rows parsed out of {REGISTRY_DOC}"
    assert "FM-001" in REGISTRY
    assert REGISTRY["FM-001"].status == "Implemented"


def test_every_implemented_id_has_a_fixture() -> None:
    """Every ``Implemented`` registry row is covered by at least one fixture.

    ``KNOWN_GAPS`` is the honest list of checks that cannot be reproduced by
    dropping Markdown into a directory. Adding to it is a deliberate act.
    """
    covered = covered_finding_ids()
    implemented = {fid for fid, row in REGISTRY.items() if row.is_implemented}
    missing = sorted(implemented - covered - KNOWN_GAPS)
    assert not missing, (
        "Implemented findings with no fixture directory under tests/fixtures/findings: "
        f"{missing}. Add one (see tests/fixtures/findings/README.md) or record it in KNOWN_GAPS."
    )


def test_every_fixture_maps_to_a_registry_row() -> None:
    """No fixture directory names a finding ID that RFC-003 does not list."""
    unknown = sorted(covered_finding_ids() - set(REGISTRY))
    assert not unknown, f"fixture directories name finding IDs missing from RFC-003: {unknown}"


def test_known_gaps_are_still_gaps() -> None:
    """KNOWN_GAPS does not keep excusing a finding that now has a fixture."""
    covered = covered_finding_ids()
    stale = sorted(KNOWN_GAPS & covered)
    assert not stale, f"these IDs now have fixtures and should be removed from KNOWN_GAPS: {stale}"


def test_baseline_fixture_exists() -> None:
    """The false-positive guard is collected."""
    names = {case.name for case in ALL_CASES}
    assert "_baseline" in names, "the _baseline fixture guards against checks that fire on every document"
