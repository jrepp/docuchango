"""Release-note regressions, including the history behind the v1.19.0 review."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.release_notes import read_commits, render_notes

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_notes.py"
REPO = "jrepp/docuchango"


def test_v1_19_0_retains_every_pr_without_rc_or_commit_duplicates():
    commits = json.loads((Path(__file__).parent / "fixtures/releases/v1.19.0.json").read_text())
    notes = render_notes(commits, REPO, "v1.19.0", "v1.18.1")
    # Independently recorded from the published GitHub-generated PR list.
    expected_prs = {
        64,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        84,
        85,
        86,
        88,
        89,
        90,
        91,
        92,
        93,
        94,
        95,
        96,
        97,
        98,
        99,
        100,
        101,
        102,
        103,
        104,
    }
    actual_prs = [int(number) for number in re.findall(r"/pull/(\d+)\)", notes)]
    assert set(actual_prs) == expected_prs
    assert len(actual_prs) == len(expected_prs)
    assert notes.count("/commit/") == 2  # Direct commits must not disappear.
    assert "-rc." not in notes
    assert "chore(release)" not in notes
    assert "Merge pull request" not in notes
    assert "What's Changed" not in notes
    assert notes.count("## Features\n") == 1
    assert "atomic by default" in notes.split("## Fixes")[0]
    assert "LNK-011" in notes.split("## Fixes")[0]
    assert "nltk" not in notes.split("<details>")[0]
    assert "[v1.18.1…v1.19.0](https://github.com/jrepp/docuchango/compare/v1.18.1...v1.19.0)" in notes


def test_grouping_preserves_breaking_changes_unknown_types_and_references():
    commits = [
        ("a" * 40, "chore(deps)!: remove old Python support (#1)"),
        ("b" * 40, "build: change packaging (#2)\n\nBREAKING CHANGE: new package layout"),
        ("c" * 40, "Merge pull request #3 from owner/fix\n\nfix(cli): preserve API_CASE (#9) (#3)"),
        ("d" * 40, "fix(cli): preserve API_CASE (#9) (#3)"),
        ("e" * 40, "revert: undo a regression (#4)"),
        ("f" * 40, "docs: revise guide (#5)"),
        ("0" * 40, "fix(release): repair publishing (#6)"),
    ]
    notes = render_notes(commits, REPO, "v2.0.0", "v1.0.0")
    breaking = notes.split("## Breaking changes\n")[1].split("## Fixes\n")[0]
    assert "remove old Python support" in breaking
    assert "change packaging" in breaking
    assert notes.count("preserve API_CASE (#9)") == 1
    assert "undo a regression" in notes
    assert "repair publishing" in notes
    assert "revise guide" in notes.split("<details>")[1]


@pytest.mark.parametrize("prerelease", [True, False])
def test_empty_release_has_no_empty_sections(prerelease):
    notes = render_notes([("a" * 40, "chore(release): 1.0.0-rc.1")], REPO, "v1.0.0-rc.1", None, prerelease=prerelease)
    assert "initial release" in notes
    assert "No additional changes" in notes
    assert "##" not in notes
    assert "<details>" not in notes
    assert "/commits/v1.0.0-rc.1" in notes
    assert notes.startswith("Release candidate" if prerelease else "Stable release")


@pytest.fixture
def release_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def git(*args):
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()

    git("init", "-b", "main")
    git("config", "user.name", "Release Test")
    git("config", "user.email", "release@example.com")
    git("config", "commit.gpgsign", "false")
    git("config", "tag.gpgsign", "false")
    git("commit", "--allow-empty", "-m", "feat: old feature (#1)")
    git("tag", "v1.0.0")
    git("switch", "-c", "feature")
    git("commit", "--allow-empty", "-m", "feat: implementation detail")
    git("commit", "--allow-empty", "-m", "fix: address review feedback")
    git("switch", "main")
    git("merge", "--no-ff", "feature", "-m", "Merge pull request #2 from owner/feature\n\nfeat: new capability")
    git("commit", "--allow-empty", "-m", "chore(release): 1.1.0-rc.1")
    git("tag", "v1.1.0-rc.1")
    git("commit", "--allow-empty", "-m", "fix: repair new capability (#3)")
    git("tag", "v1.1.0-rc.2")
    git("commit", "--allow-empty", "-m", "chore(release): 1.1.0")
    git("tag", "v1.1.0")
    return tmp_path


def test_stable_range_includes_whole_rc_series_but_not_branch_internal_commits(release_repo):
    notes = render_notes(read_commits("v1.1.0", "v1.0.0"), REPO, "v1.1.0", "v1.0.0")
    assert "new capability" in notes
    assert "repair new capability" in notes
    assert "old feature" not in notes
    assert "implementation detail" not in notes
    assert "review feedback" not in notes
    assert "rc.1" not in notes


def test_cli_rc_range_is_incremental_and_works_without_project_dependencies(release_repo):
    output = release_repo / "notes.md"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            REPO,
            "--version",
            "v1.1.0-rc.2",
            "--previous-tag",
            "v1.1.0-rc.1",
            "--prerelease",
            "--output",
            str(output),
        ],
        check=True,
    )
    notes = output.read_text()
    assert notes.startswith("Release candidate: changes since v1.1.0-rc.1.")
    assert "/pull/3" in notes
    assert "/pull/2" not in notes


@pytest.mark.parametrize("previous", ["v9.9.9", "v1.1.0"])
def test_missing_or_reversed_range_fails_without_writing_notes(release_repo, previous):
    output = release_repo / "notes.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            REPO,
            "--version",
            "v1.0.0",
            "--previous-tag",
            previous,
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Cannot read release history" in result.stderr
    assert not output.exists()


def test_initial_release_reads_all_history(release_repo):
    notes = render_notes(read_commits("v1.0.0", None), REPO, "v1.0.0", None)
    assert "old feature" in notes
    assert "initial release" in notes
