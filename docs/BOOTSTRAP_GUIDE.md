# docs-cms Bootstrap Guide

This guide takes a repository from nothing to a validated `docs-cms/` in six
steps, then explains the pieces you just created. It is the guide
`docuchango bootstrap` prints.

## What is docs-cms?

`docs-cms` is a folder of Markdown documents with structured frontmatter,
kept in git next to the code it describes. It holds four kinds of document:

| Type | Answers | Example |
|------|---------|---------|
| ADR (Architecture Decision Record) | Why did we decide this? | `adr-007-adopt-postgres.md` |
| RFC (Request for Comments) | What are we proposing to change? | `rfc-003-event-sourcing.md` |
| Memo | What did we learn or plan? | `memo-012-load-test-results.md` |
| PRD (Product Requirements Document) | What are we building and for whom? | `prd-002-self-serve-signup.md` |

Docuchango validates and repairs that folder. Humans get one searchable
place for decisions. Coding agents get durable project memory they can read
before acting and extend as they work.

## Setup

### 1. Install

```bash
uv tool install docuchango      # or: pip install docuchango
docuchango --version
```

`uvx docuchango ...` also works without installing anything.

### 2. Initialize

```bash
docuchango init --project-id my-app --project-name "My App"
```

This creates `docs-cms/` with a config file, its JSON schema, a README,
empty `adr/`, `rfcs/`, `memos/` and `prd/` folders, and a template for each
type under `templates/`. If the target folder already has files in it, `init`
stops and changes nothing; `--force` runs anyway and overwrites the files it
generates, so back up a config you have edited before using it. Use `--path`
to put it somewhere other than `./docs-cms`.

### 3. Review the config

Open `docs-cms/docs-project.yaml`. For a first project the only values to
check are:

```yaml
project:
  id: my-app            # copy this value into each document's project_id
  name: My App
  description: Documentation for My App
```

Keeping `project.id` and every document's `project_id` in step is a
convention, not a rule docuchango enforces: `project_id` is required on every
document, but its value is never compared with the config.

Everything else has a working default and is documented inline as comments.
The file points at `docs-project.schema.json`, so editors with a YAML
language server validate it as you type. When you outgrow the defaults, see
[CONFIGURATION.md](CONFIGURATION.md).

### 4. Write the first document

Start with an ADR recording the decision to adopt docs-cms. Copy the
template, rename it with the next number and a short slug, and fill in the
frontmatter:

```bash
cp docs-cms/templates/adr-000-template.md docs-cms/adr/adr-001-adopt-docs-cms.md
uuidgen | tr '[:upper:]' '[:lower:]'     # paste into doc_uuid
date -u +%Y-%m-%dT%H:%M:%SZ              # paste into created
```

```yaml
---
id: adr-001
title: Adopt docs-cms for engineering decisions
status: Accepted
created: 2026-09-14T10:00:00Z
deciders: Platform Team
tags: [documentation, process]
project_id: my-app
doc_uuid: 7c9e6679-7425-40de-944b-e07fc1f90ae7
---
```

Then replace the template body with your context, decision and consequences.

### 5. Validate

```bash
docuchango validate --dry-run    # report only
docuchango validate              # fix what can be fixed, report the rest
```

The dry run shows everything docuchango would change or cannot change. The
second command applies the safe fixes: whitespace, tag normalization, date
formats, code fence languages, missing defaults. Anything left in the report,
such as an `id` that does not match its filename, needs a person.

### 6. Tell your agents

Create `AGENTS.md` at the repository root so coding agents treat `docs-cms/`
as project memory:

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

Agents can print the full agent guide with `docuchango bootstrap --guide agent`.

You now have a working docs-cms. Commit it.

## Add the CI check

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
          fetch-depth: 0
      - uses: astral-sh/setup-uv@v8
      - run: uvx docuchango validate --dry-run --verbose
```

`--dry-run` makes the job fail on problems rather than rewriting files in CI.
`fetch-depth: 0` gives docuchango the git history it uses for timestamps.

## Reference

### Layout

```text
my-app/
├── AGENTS.md
└── docs-cms/
    ├── docs-project.yaml
    ├── docs-project.schema.json
    ├── README.md
    ├── adr/        adr-001-*.md, adr-002-*.md, ...
    ├── rfcs/       rfc-001-*.md, ...
    ├── memos/      memo-001-*.md, ...
    ├── prd/        prd-001-*.md, ...
    └── templates/  adr-000-template.md, rfc-000-template.md,
                    memo-000-template.md, prd-000-template.md
```

### Frontmatter fields

Every type requires:

| Field | Rule |
|-------|------|
| `id` | Lowercase `type-NNN`, must match the filename prefix |
| `title` | Plain title without the id |
| `created` | ISO 8601 date or timestamp |
| `tags` | List of lowercase, hyphenated tags |
| `project_id` | Must equal `project.id` in the config |
| `doc_uuid` | UUID v4, generated once and never changed |

Per type:

| Type | Extra required | `status` values |
|------|----------------|-----------------|
| ADR | `status`, `deciders` | Proposed, Accepted, Implemented, Deprecated, Superseded |
| RFC | `status`, `author` | Draft, Proposed, Accepted, Implemented, Deprecated, Superseded |
| Memo | `author` | no status |
| PRD | `status`, `author`, `target_release` | Draft, In Review, Approved, In Progress, Completed, Cancelled |

`updated` is not stored. Derive it from git when you need it:
`git log -1 --format=%aI <file>`.

### Filenames and ids

- Files: `{type}-{NNN}-{kebab-case-slug}.md`, for example `rfc-042-user-authentication.md`.
- Ids: `{type}-{NNN}`, for example `rfc-042`.
- Lowercase only. No underscores in the prefix.

### Status flows

```text
ADR:  Proposed → Accepted → Implemented
                          → Deprecated
                          → Superseded (by adr-NNN)

RFC:  Draft → Proposed → Accepted → Implemented
                                  → Deprecated
                                  → Superseded

PRD:  Draft → In Review → Approved → In Progress → Completed
                                                 → Cancelled
```

To replace a decision, write a new ADR and set the old one to `Superseded`.
By convention the new document carries `supersedes: adr-NNN` and the old one
`superseded_by: adr-MMM`; extra frontmatter fields like these are allowed.
Do not rewrite history in the old document.

### Choosing a type

- A choice was made and should be remembered: **ADR**.
- A change is being proposed and needs discussion: **RFC**.
- A finding, plan, investigation or status worth keeping: **Memo**.
- Requirements, users and success criteria for something to build: **PRD**.

## Troubleshooting

Schema problems are reported as `Frontmatter field '<name>': <message>`,
where the message comes from the schema itself.

**`ID mismatch: frontmatter has 'adr-000' but filename suggests 'adr-001'`**
The template's `id` was not updated after copying. Set `id` to match the
filename.

**`Broken link './adr-001-example.md' - File not found`**
The template body contains an example link. Replace it with a real target or
remove it.

**`Frontmatter field 'doc_uuid': Value error, doc_uuid must be a valid UUID v4 format. Got: ...`**
Generate one with `uuidgen | tr '[:upper:]' '[:lower:]'`.

**`Frontmatter field 'project_id': Field required`**
Add it, using the `project.id` from `docs-project.yaml` by convention. For
many files at once: `docuchango bulk update --set project_id=my-app`.

**`Frontmatter field 'status': Input should be 'Proposed', 'Accepted', ...`**
Use a value from the table above for that document type. Common variants
such as `accepted` or `Draft` on an ADR are corrected automatically.

**Nothing is scanned**
The folder is not listed in `document_folders`, or the config is not where
you ran the command. Use `--repo-root` to point at the right directory.

## Next

- [CONFIGURATION.md](CONFIGURATION.md): monorepos, mixed schemas, naming
  standards, index files.
- [VALIDATION_REFERENCE.md](VALIDATION_REFERENCE.md): every check and fix.
- [AGENT_GUIDE.md](AGENT_GUIDE.md): how agents should use the docs-cms.
- `examples/docs-cms/`: a complete sample project.
