# Agent Instructions

Use `docs-cms/` as durable project memory. Read relevant ADRs, RFCs, PRDs, and memos before changing architecture, validation, schemas, templates, release process, or agent workflow guidance.

Docuchango maintains its own `docs-cms/`. Product decisions and durable maintenance knowledge belong there. `examples/docs-cms/` is sample user content, not authoritative project memory.

After docs-cms edits, run `docuchango validate` and summarize remaining manual issues.

Do not mark agent-authored architectural decisions `Accepted` without explicit user approval. Use `Proposed` or a memo for inferred content.

Validator registry: `docs-cms/rfcs/rfc-003-validator-roadmap.md` lists every check `docuchango validate` performs or plans to perform, each with a finding ID (for example `FMT-010`) and a status. Read it before adding or changing a validator. When a validator lands, flip its row to `Implemented`, use the finding ID in error messages, tests and the commit message, and update `docs/VALIDATION_REFERENCE.md` in the same change.
