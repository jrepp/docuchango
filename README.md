# Docuchango

[![PyPI version](https://badge.fury.io/py/docuchango.svg)](https://pypi.org/project/docuchango/)
[![CI](https://github.com/jrepp/docuchango/workflows/CI/badge.svg)](https://github.com/jrepp/docuchango/actions)
[![codecov](https://codecov.io/gh/jrepp/docuchango/branch/main/graph/badge.svg)](https://codecov.io/gh/jrepp/docuchango)
[![Python Version](https://img.shields.io/badge/python-3.10%E2%80%933.15-blue)](https://www.python.org/downloads/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

![Docuchango logo](docs-cms/imgs/docuchango.png)

Docuchango keeps a folder of engineering documents valid. Give it a `docs-cms/`
directory of ADRs, RFCs, memos and PRDs, and it checks the frontmatter against
a schema, verifies every link, cleans up the Markdown, and fixes what it can
without asking. It is built for repositories where humans and coding agents
write documentation together and need it to stay trustworthy.

- **Structured by default.** Every document has an id, a title, a created
  date, tags, a project id and a UUID, enforced by Pydantic schemas per
  document type. ADRs, RFCs and PRDs also carry a status.
- **Fixes, not just findings.** Status variants, recognizable date formats,
  whitespace and tags are repaired in place, code fences gain a language and
  a closing fence, and a missing `tags`, `project_id` or `doc_uuid` is filled
  in with a default - all on a real run; `--dry-run` reports these as plain
  issues rather than previewing them. What it cannot fill in safely, such as
  `title` or `deciders`, it reports, and extra blank lines are reported but
  never collapsed. A fixing run is atomic by default: if any issue remains
  once fixing finishes, every fix from that run is withheld and the tree is
  left exactly as it was. The report still lists the withheld fixes, and they
  land once the remaining issues are resolved. Pass `--no-atomic` to keep
  partial fixes on disk instead.
- **Agent-ready.** Ships a guide that tells coding agents how to read,
  cite and extend the docs. Point `AGENTS.md` at it and you are done.
- **Fast and CI-friendly.** Scanning and fixing a hundred documents takes
  well under a second; exit codes work in pre-commit hooks and pull request
  checks. A Docusaurus build, if your repo has one, is checked too unless
  you pass `--skip-build`, and takes as long as the build does.

## Two-minute start

You need Python 3.10 to 3.15. With [uv](https://docs.astral.sh/uv/) nothing
else has to be installed:

```bash
# 1. Create the folder structure, config and templates
uvx docuchango init --project-id my-app --project-name "My App"

# 2. Write your first decision record from the template
cp docs-cms/templates/adr-000-template.md docs-cms/adr/adr-001-adopt-docs-cms.md
#    ...edit the frontmatter, and replace the template's example reference
#    link in the body or the next step will report it as broken...

# 3. Check it, then let it repair what it can
uvx docuchango validate --dry-run
uvx docuchango validate
```

Prefer a permanent install? `pip install docuchango` or
`uv tool install docuchango` gives you the `docuchango` command directly.

`init` creates this layout:

```text
docs-cms/
├── docs-project.yaml         # project config (id, folders, rules)
├── docs-project.schema.json  # editor validation for the config
├── README.md
├── adr/                      # Architecture Decision Records
├── rfcs/                     # Requests for Comments
├── memos/                    # Findings, plans, status notes
├── prd/                      # Product Requirements Documents
└── templates/                # adr-000, rfc-000, memo-000, prd-000
```

Here is a real `--dry-run` against an example `docs-cms/` with two ADRs, one
with a fixable date format and the other with a copy-paste mistake:

```text
$ docuchango validate --dry-run

🔍 Validating Documentation
DRY RUN - No changes will be made

Scanned 2 files

✓ Fixes would be applied: 1
  docs-cms/adr/adr-001-adopt-postgres.md
    • [Frontmatter metadata] Converted created from '2026/09/01' to '2026-09-01'

✗ Remaining issues: 2
  docs-cms/adr/adr-002-event-bus.md
    • ID mismatch: frontmatter has 'adr-003' but filename suggests 'adr-002'
    • Line 15: Broken link './adr-005-missing.md' - File not found: /tmp/docuchango-example/docs-cms/adr/adr-005-missing.md

1 fixable, 1 with issues

❌ Validation failed
```

Run it again without `--dry-run` and the date format is fixed. The other two
findings need a human, so they stay in the report either way.

## What a document looks like

Every file is Markdown with a YAML frontmatter block. This is a complete ADR
header:

```yaml
---
id: adr-001                 # lowercase, matches the filename
title: Adopt docs-cms
status: Accepted            # ADR: Proposed, Accepted, Rejected, Implemented, Deprecated, Superseded
created: 2026-09-14
deciders: Platform Team
tags: [documentation, process]
project_id: my-app          # from docs-project.yaml
doc_uuid: 7c9e6679-7425-40de-944b-e07fc1f90ae7   # generate once, never change
---
```

Each type adds a field or two:

| Type | Folder | Extra required fields | Status values |
|------|--------|----------------------|---------------|
| ADR  | `adr/`   | `deciders` | Proposed, Accepted, Rejected, Implemented, Deprecated, Superseded |
| RFC  | `rfcs/`  | `author`   | Draft, Proposed, Accepted, Rejected, Implemented, Deprecated, Superseded |
| Memo | `memos/` | `author`   | none required |
| PRD  | `prd/`   | `author`, `target_release` | Draft, In Review, Approved, In Progress, Completed, Cancelled |

Generate a UUID with `uuidgen | tr '[:upper:]' '[:lower:]'` or
`python -c "import uuid; print(uuid.uuid4())"`.

## Everyday commands

| Command | What it does |
|---------|--------------|
| `docuchango init` | Create `docs-cms/` with config, schema and templates |
| `docuchango validate` | Check every document and fix what can be fixed |
| `docuchango validate --dry-run` | Report only, change nothing |
| `docuchango validate --verbose` | Show every check, useful in CI logs |
| `docuchango bulk update --type adr --set status=Accepted` | Change a frontmatter field across many documents |
| `docuchango bulk timestamps` | Derive `created` dates from git history |
| `docuchango migrate --project-id my-app` | Upgrade legacy frontmatter to the current schema |
| `docuchango bootstrap` | Print the setup guide; `--guide agent` prints the agent guide |

`validate`, the `bulk` commands and `migrate` all accept `--dry-run`. `init`
does not: it refuses to write into a folder that already has files in it
unless you pass `--force`, which overwrites the files it generates.
`dcc-validate` is a short alias for `docuchango validate`.

## Working with coding agents

Docuchango treats `docs-cms/` as the project's durable memory. Tell your
agents the same thing by adding an `AGENTS.md` at the repository root:

```markdown
# Agent Instructions

Use `docs-cms/` as durable project memory. Read the relevant ADRs, RFCs,
PRDs and memos before changing architecture, schemas or process.

Record new durable knowledge as a docs-cms document, not as loose notes.
ADRs for decisions, RFCs for proposals, PRDs for requirements, memos for
findings. Do not mark an agent-authored decision `Accepted` without explicit
human approval; use `Proposed` or write a memo.

After editing docs-cms, run `docuchango validate` and report anything it
could not fix.
```

The full agent guide covers searching, citing and proposing documents. Print
it with `docuchango bootstrap --guide agent`, or read
[docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md).

## Validate in CI

```yaml
name: Validate docs
on:
  pull_request:
    paths: ['docs-cms/**']
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # git history lets docuchango derive timestamps
      - uses: astral-sh/setup-uv@v8
      - run: uvx docuchango validate --dry-run --verbose --skip-build
```

This example only validates the documents themselves. If your repository
also has a `docusaurus/` directory, `validate` runs its TypeScript check and
`npm run build` unless you pass `--skip-build`; add the site's Node setup
(`npm ci` or equivalent) to this job before dropping the flag.

`--dry-run` never writes to the working tree. The job fails when an issue
remains in the committed files, whether or not `validate` could fix it for
you - a bad status value fails the build even though it is auto-correctable,
while an unusually formatted but schema-accepted date does not, because
nothing rejects it. Run `docuchango validate` (no `--dry-run`) locally or in
a pre-commit hook to clear fixable issues before they reach CI. That run is
atomic: if an issue outside its reach remains, it writes nothing and reports
the fixes it withheld alongside the issue you still need to resolve, so you
never end up with an unrelated fix mixed into your working tree.

## Going further

- [Bootstrap guide](docs/BOOTSTRAP_GUIDE.md): step-by-step setup for a new or
  existing repository, document types, status flows, troubleshooting.
- [Configuration](docs/CONFIGURATION.md): monorepos, multiple doc roots,
  mixed schemas, naming standards, index files, readability thresholds.
- [Validation reference](docs/VALIDATION_REFERENCE.md): everything docuchango
  detects, what it fixes automatically, and what it leaves to you.
- [Agent guide](docs/AGENT_GUIDE.md) and
  [Best practices](docs/BEST_PRACTICES.md): how agents should read, cite and
  extend a docs-cms.
- [Templates](templates/) and a complete [example docs-cms](examples/docs-cms/).
- [Docuchango's own docs-cms](docs-cms/): the decisions behind the tool.

## Python API

```python
from docuchango.validator import DocValidator
from docuchango.schemas import ADRFrontmatter

# DocValidator only reports; fixing is the `validate` command's own pass.
validator = DocValidator(repo_root=".", verbose=True)
validator.scan_documents()
validator.check_code_blocks()
validator.check_formatting()

adr = ADRFrontmatter(**frontmatter_data)
```

## Development

```bash
uv sync                      # install with dev dependencies
uv run pytest                # tests
uv run pytest --cov=docuchango
uv run ruff format . && uv run ruff check .
uv run mypy docuchango tests
actionlint                   # GitHub Actions workflows
uv build
```

Releases are automated from conventional commits. See
[PUBLISHING.md](PUBLISHING.md).

## Requirements

- Python 3.10 to 3.15
- macOS, Linux or Windows

## License

Mozilla Public License 2.0. See [LICENSE](LICENSE).

## Links

- [GitHub](https://github.com/jrepp/docuchango)
- [PyPI](https://pypi.org/project/docuchango)
- [Issues](https://github.com/jrepp/docuchango/issues)
