---
id: "prd-001"
title: "Docuchango: Documentation Validation and Repair Framework"
status: Launched
author: Engineering Team
created: 2025-01-20
updated: 2025-01-26
tags: ["validation", "documentation", "framework", "product"]
project_id: "docuchango"
doc_uuid: "e5f6a7b8-c9d0-4e9f-2a3b-4c5d6e7f8a9b"
---

# PRD-001: Docuchango - Documentation Validation and Repair Framework

## Product Vision

Docuchango is a Python CLI tool that validates and repairs Docusaurus-based documentation, ensuring consistency, correctness, and quality for technical documentation used in human-agent collaboration workflows.

## Problem Statement

Teams using Docusaurus for technical documentation face challenges:

1. **Validation Gaps**: No automated checking of frontmatter, links, and formatting
2. **Manual Fixes**: Developers spend hours fixing whitespace, code fences, and metadata
3. **Broken Links**: Internal links break as documentation evolves
4. **Inconsistent Structure**: Different document types lack standardization
5. **CI/CD Integration**: Hard to enforce documentation quality in pipelines
6. **Human-Agent Workflows**: LLMs need consistent, well-structured docs

### Current Solutions and Gaps

| Solution | Pros | Cons |
|----------|------|------|
| Manual review | Thorough | Time-consuming, error-prone |
| Markdown linters | Fast | Don't validate frontmatter or links |
| Docusaurus build | Catches syntax | Runs late, poor error messages |
| Custom scripts | Flexible | Not reusable, hard to maintain |

**Gap**: No comprehensive tool for Docusaurus documentation validation with automatic fixes.

## Target Users

### Primary Users

1. **Technical Writers** (40%)
   - Create and maintain documentation
   - Need fast validation feedback
   - Want auto-fix for common issues

2. **Software Engineers** (35%)
   - Write ADRs, RFCs, technical docs
   - Need CI/CD integration
   - Want minimal configuration

3. **DevOps/Platform Engineers** (15%)
   - Maintain documentation infrastructure
   - Need reliable validation in pipelines
   - Want clear error reporting

### Secondary Users

4. **AI/LLM Systems** (10%)
   - Consume structured documentation
   - Need consistent schema and format
   - Benefit from validated metadata

## Goals and Success Metrics

### Business Goals

1. Reduce documentation review time by 50%
2. Decrease broken link incidents by 80%
3. Enable human-agent collaboration workflows
4. Establish docuchango as standard for Docusaurus validation

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Adoption | 100+ weekly installs | PyPI stats |
| Validation speed | < 1s for 100 docs | Benchmarks |
| Test coverage | > 90% | pytest-cov |
| Issue resolution | < 24h response | GitHub issues |
| User satisfaction | > 4.5/5 stars | User surveys |

### Anti-Goals

- Not a replacement for Docusaurus itself
- Not a general-purpose markdown linter
- Not a content quality checker (grammar, style)
- Not a CI/CD platform

## User Stories

### Epic 1: Validation

**US-1.1**: As a technical writer, I want to validate all docs with one command so I can catch errors before committing.

```bash
docuchango validate --repo-root /path/to/docs
```

**US-1.2**: As an engineer, I want clear error messages so I can fix issues quickly.

```text
❌ docs-cms/adr/adr-001-test.md:
   - Missing required field: 'deciders'
   - Invalid status: 'WIP' (must be one of: Proposed, Accepted, Deprecated, Superseded)
   - Tag 'Invalid Tag' must be lowercase-with-hyphens
```

**US-1.3**: As a DevOps engineer, I want validation in CI so bad docs never merge.

```yaml
- name: Validate docs
  run: |
    pip install docuchango
    docuchango validate --repo-root .
```

### Epic 2: Auto-Fix

**US-2.1**: As a technical writer, I want auto-fix for common issues so I don't waste time on formatting.

```bash
docuchango fix all --repo-root /path/to/docs
```

**US-2.2**: As an engineer, I want to fix only specific issues so I have control.

```bash
docuchango fix whitespace --repo-root .
docuchango fix code-fences --repo-root .
```

### Epic 3: Link Validation

**US-3.1**: As a technical writer, I want broken link detection so readers don't hit 404s.

```text
✓ Validating links...
  ❌ adr-001-test.md:15 - Link target not found: ../rfcs/missing.md
  ✓ adr-002-test.md:23 - Valid internal link
```

**US-3.2**: As an engineer, I want relative link support so refactoring is safe.

### Epic 4: Templates

**US-4.1**: As a technical writer, I want document templates so I start with correct structure.

```bash
cp templates/adr-template.md docs-cms/adr/adr-042-my-decision.md
```

**US-4.2**: As an engineer, I want template validation so my docs follow standards.

## Feature Requirements

### Must-Have (MVP)

1. **Frontmatter Validation**
   - Validate required fields
   - Check field formats (UUID, dates, tags)
   - Support multiple document types (ADR, RFC, Memo)

2. **Link Validation**
   - Check internal relative links
   - Validate absolute paths
   - Skip external links (no network calls)

3. **Auto-Fix**
   - Remove trailing whitespace
   - Add missing code fence languages
   - Add blank lines before code fences
   - Add missing frontmatter fields

4. **CLI**
   - `docuchango validate`
   - `docuchango fix`
   - Colorized output
   - Exit codes for CI

5. **Documentation**
   - README with quick start
   - Templates for all doc types
   - API documentation

### Should-Have (V1.1)

6. **Template System**
   - ADR, RFC, Memo, PRD, FRD, PRDFAQ templates
   - UUID generation helper
   - Template README

7. **Advanced Validation**
   - Check code block languages are valid
   - Validate consistent numbering (ADR-001, ADR-002...)
   - Check for duplicate IDs

8. **Reporting**
   - JSON output for machine parsing
   - Summary statistics
   - Verbose mode

### Nice-to-Have (V2.0)

9. **Interactive Mode**
   - Prompt to fix issues one by one
   - Show diffs before applying

10. **Document Generation**
    - `docuchango new adr "My Decision"`
    - Auto-generate UUID and metadata
    - Interactive prompts for fields

11. **Git Integration**
    - Validate only changed files
    - Pre-commit hook support

## Technical Requirements

### Performance

- Validate 100 documents in < 1 second
- Fix 100 documents in < 2 seconds
- Low memory footprint (< 100MB)

### Compatibility

- Python 3.9+
- Works on macOS, Linux, Windows
- No OS-specific dependencies

### Dependencies

- Minimal core dependencies (Pydantic, Click, python-frontmatter)
- All deps available on PyPI
- No compiled extensions (pure Python)

### Testing

- 90%+ test coverage
- Unit tests with pytest
- Integration tests with real docs
- CI runs on all Python versions (3.9-3.12)

## Design Considerations

### User Experience

- **Fast Feedback**: Show errors as they're found
- **Clear Messages**: Explain what's wrong and how to fix
- **Progressive Enhancement**: Basic usage is simple, advanced features available
- **Consistent CLI**: Follow Unix conventions (exit codes, flags)

### Extensibility

- Plugin system for custom validators (future)
- Configurable via pyproject.toml or .docuchango.yml
- Support custom document types via config

### Error Handling

- Never crash on malformed input
- Show partial results if some docs fail
- Clear error messages with file:line references

## Go-to-Market Strategy

### Phase 1: Launch (Jan 2025)

- Publish to PyPI
- Create GitHub repo
- Write README and docs
- Post to Reddit (r/Python, r/documentation)

### Phase 2: Adoption (Feb 2025)

- Blog post with examples
- Submit to Awesome Lists
- Create demo video
- Reach out to Docusaurus community

### Phase 3: Growth (Mar+ 2025)

- Conference talks
- Integration with popular tools
- Plugin ecosystem

## Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low adoption | High | Medium | Strong docs, easy onboarding |
| Performance issues | Medium | Low | Benchmarks, optimization |
| Breaking changes in Pydantic | Medium | Low | Pin major version, test upgrades |
| Competition emerges | Low | Medium | Move fast, best UX |

## Open Questions

1. Should we support config files for custom rules?
2. Should we integrate with VSCode/IDE?
3. Should we provide a web UI for validation results?
4. Should we support other markdown formats (not Docusaurus)?

## Timeline

- **Week 1**: Core validation logic
- **Week 2**: Auto-fix functionality
- **Week 3**: Templates and documentation
- **Week 4**: Testing and polish
- **Launch**: End of January 2025

## Appendix

### Related Documents

- [RFC-001: Document Template System](../rfcs/rfc-001-document-template-system.md)
- [ADR-001: Pydantic Schema Validation](../adr/adr-001-pydantic-schema-validation.md)
- [ADR-002: Click CLI Framework](../adr/adr-002-click-cli-framework.md)
- [PRDFAQ-001: Docuchango Launch](../prdfaq/prdfaq-001-launch.md)

### Competitive Analysis

| Tool | Strength | Weakness | Differentiation |
|------|----------|----------|-----------------|
| markdownlint | Fast, widely used | No frontmatter validation | Docuchango validates YAML |
| remark-lint | Pluggable | Complex setup | Docuchango works out of box |
| vale | Style checking | Not schema-aware | Docuchango validates structure |
| Custom scripts | Flexible | Not reusable | Docuchango is packaged |
