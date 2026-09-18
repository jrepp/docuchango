"""Render GitHub release notes from the changes that landed on the release branch.

Use first-parent history so a merged PR is listed once, without its intermediate
commits. Unlike the semantic-release changelog, this also includes squash commits
whose changes were already seen on a merged branch during an earlier RC.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from pathlib import Path

VERSION = r"v?\d+\.\d+\.\d+(?:-[\w.]+)?"
CONVENTIONAL = re.compile(r"^(?P<kind>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<title>.+)$")
MERGE_PR = re.compile(r"^Merge pull request #(\d+)\b")
SQUASH_PR = re.compile(r"\s+\(#(\d+)\)$")
RELEASE_COMMIT = re.compile(rf"^chore\(release\): {VERSION}$")
CATEGORIES = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "security": "Security",
    "docs": "Documentation",
    "build": "Build and CI",
    "ci": "Build and CI",
    "test": "Tests",
    "refactor": "Maintenance",
    "style": "Maintenance",
    "chore": "Maintenance",
}
VISIBLE = ("Breaking changes", "Security", "Features", "Fixes", "Performance", "Other changes")
MAINTENANCE = ("Documentation", "Dependencies", "Build and CI", "Tests", "Maintenance")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


def read_commits(version: str, previous_tag: str | None) -> list[tuple[str, str]]:
    """Resolve exact tags and reject invalid ranges instead of publishing empty notes."""
    end = git("rev-parse", "--verify", f"refs/tags/{version}^{{commit}}").strip()
    revision = end
    if previous_tag:
        start = git("rev-parse", "--verify", f"refs/tags/{previous_tag}^{{commit}}").strip()
        git("merge-base", "--is-ancestor", start, end)
        revision = f"{start}..{end}"
    fields = git("log", "--first-parent", "--reverse", "--format=%H%x00%B%x00", revision, "--").split("\0")
    return [(fields[i].strip(), fields[i + 1].strip()) for i in range(0, len(fields) - 1, 2)]


def render_notes(
    commits: list[tuple[str, str]], repo: str, version: str, previous_tag: str | None, *, prerelease: bool = False
) -> str:
    """Group landed changes, retaining source links and all non-release commits."""
    url = f"https://github.com/{repo}"
    groups: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()
    for sha, message in commits:
        lines = message.splitlines()
        if not lines:
            continue
        title = lines[0]
        if RELEASE_COMMIT.fullmatch(title):
            continue
        merge = MERGE_PR.match(title)
        squash = SQUASH_PR.search(title)
        number = merge[1] if merge else squash[1] if squash else None
        if merge:
            title = next((line.strip() for line in lines[1:] if line.strip()), title)
        elif squash:
            title = title[: squash.start()]
        # A merge title can itself carry the PR suffix. Remove only its own ID,
        # preserving issue references and other PR numbers in the description.
        if number:
            title = re.sub(rf"\s+\(#{number}\)$", "", title)
        identity = f"pr:{number}" if number else f"commit:{sha}"
        if identity in seen:
            continue
        seen.add(identity)
        match = CONVENTIONAL.match(title)
        category = "Other changes"
        if match:
            kind, scope = match["kind"], match["scope"]
            category = CATEGORIES.get(kind, "Other changes")
            if kind in {"chore", "build"} and scope in {"deps", "deps-dev"}:
                category = "Dependencies"
            title = match["title"]
        if (match and match["breaking"]) or re.search(r"^BREAKING[ -]CHANGE:", message, re.MULTILINE):
            category = "Breaking changes"
        # Preserve code/identifier case; just remove conventional-commit syntax.
        reference = f"[#{number}]({url}/pull/{number})" if number else f"[`{sha[:7]}`]({url}/commit/{sha})"
        groups[category].append(f"- {title} ({reference})")

    channel = "Release candidate" if prerelease else "Stable release"
    intro = f"{channel}: changes since {previous_tag}." if previous_tag else f"{channel}: initial release."
    parts = [intro]
    for category in VISIBLE:
        if groups[category]:
            parts.append(f"## {category}\n\n" + "\n".join(groups[category]))
    maintenance = [f"### {category}\n\n" + "\n".join(groups[category]) for category in MAINTENANCE if groups[category]]
    if maintenance:
        parts.append(
            "<details>\n<summary>Documentation and maintenance</summary>\n\n"
            + "\n\n".join(maintenance)
            + "\n\n</details>"
        )
    if not seen:
        parts.append("No additional changes in this release.")
    if previous_tag:
        parts.append(f"**Full changelog:** [{previous_tag}…{version}]({url}/compare/{previous_tag}...{version})")
    else:
        parts.append(f"**Full history:** [{version}]({url}/commits/{version})")
    return "\n\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--version", required=True, help="Release tag")
    parser.add_argument(
        "--previous-tag", default="", help="Previous RC for an RC, previous stable for a stable release"
    )
    parser.add_argument("--prerelease", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    previous_tag = args.previous_tag if args.previous_tag not in {"", "none"} else None
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        parser.error("--repo must be owner/repository")
    for tag in (args.version, previous_tag):
        if tag and not re.fullmatch(VERSION, tag):
            parser.error(f"Invalid release tag: {tag}")
    try:
        commits = read_commits(args.version, previous_tag)
    except subprocess.CalledProcessError as error:
        parser.exit(1, f"Cannot read release history; check tags, ancestry and fetch-depth: 0.\n{error.stderr or ''}")
    args.output.write_text(
        render_notes(commits, args.repo, args.version, previous_tag, prerelease=args.prerelease), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
