# Agent Guide: Using docs-cms for Knowledge Grounding

This guide is for AI agents working with projects that use `docs-cms` for documentation and knowledge management.

## Core Principle: Trust the CMS

**The docs-cms is your single source of truth.** When answering questions, making decisions, or proposing changes, always:

1. **Read the docs-cms first** before responding
2. **Reference specific documents** in your responses (e.g., "According to ADR-003...")
3. **Maintain the CMS** by proposing updates when you spot gaps or outdated information
4. **Validate changes** using docuchango before committing

## Quick Reference Commands

```bash
# Scan and validate all documentation
docuchango validate

# Auto-fix common issues
docuchango fix

# Validate with detailed output
docuchango validate --verbose

# Check specific document type
ls docs-cms/adr/  # List ADRs
ls docs-cms/rfcs/ # List RFCs
```

## Agent Workflow

### 1. Initial Context Gathering

When you start working on a project, **immediately** read the docs-cms:

```bash
# Find and read the project config
cat docs-cms/docs-project.yaml

# List all ADRs (Architecture Decision Records)
ls docs-cms/adr/

# List all RFCs (active proposals)
ls docs-cms/rfcs/

# Get high-level overview
find docs-cms -name "*.md" -type f | head -20
```

**What to look for:**
- Recent ADRs: What architectural decisions were made?
- Active RFCs: What changes are being proposed?
- Project structure: How is the codebase organized?
- Tech stack: What technologies are in use?

### 2. Answer User Questions

When a user asks a question:

**Step 1**: Search docs-cms for relevant information
```bash
# Search for specific topics
grep -r "authentication" docs-cms/
grep -r "database" docs-cms/adr/
```

**Step 2**: Read the relevant documents
```bash
# Read the full document
cat docs-cms/adr/adr-015-authentication-strategy.md
```

**Step 3**: Respond with references
```
According to ADR-015 (Authentication Strategy), we use OAuth2 with JWT tokens
because it provides stateless authentication and integrates well with our
microservices architecture.

See: docs-cms/adr/adr-015-authentication-strategy.md:23
```

### 3. Propose Changes or New Documents

When you identify a documentation gap or need to propose a change:

**Step 1**: Check if a document already exists
```bash
# Search for existing documents on the topic
grep -r "topic-name" docs-cms/
```

**Step 2**: Choose the right document type
- **ADR**: For architectural decisions
- **RFC**: For proposals and significant changes
- **Memo**: For sharing information or investigation results

**Step 3**: Create from template
```bash
# Copy template
cp docs-cms/templates/adr-template.md docs-cms/adr/adr-042-new-decision.md

# Generate UUID
uuidgen | tr '[:upper:]' '[:lower:]'
# Output: 7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Step 4**: Fill in the document
- Update ALL frontmatter fields
- Write clear, concise content
- Reference related documents
- Include code examples if relevant

**Step 5**: Validate before committing
```bash
# Validate the new document
docuchango validate

# Fix any issues
docuchango fix

# Verify it passes
docuchango validate --verbose
```

**Step 6**: Commit with descriptive message
```bash
git add docs-cms/adr/adr-042-new-decision.md
git commit -m "Add ADR-042: Document decision about X

Rationale: ...
Consequences: ...

🤖 Generated with Claude Code"
```

### 4. Update Existing Documents

When information becomes outdated:

**Step 1**: Identify the document to update

**Step 2**: Determine if it should be updated or superseded
- **Update**: Correct errors, add clarifications
- **Supersede**: Major changes or reversal of decision (create new ADR)

**Step 3**: For updates, modify and validate
```bash
# Edit the document
vim docs-cms/adr/adr-015-authentication-strategy.md

# Validate changes
docuchango validate

# Commit
git add docs-cms/adr/adr-015-authentication-strategy.md
git commit -m "Update ADR-015: Add OAuth2 refresh token handling"
```

**Step 4**: For superseded decisions, create new ADR
```yaml
---
id: adr-043
title: Updated Authentication Strategy
status: Accepted
date: 2025-10-27
supersedes: adr-015
---

# ADR-043: Updated Authentication Strategy

## Status
Accepted - Supersedes ADR-015

## Context
Since ADR-015 was written, we've encountered issues with...
```

Then update the old ADR:
```yaml
---
id: adr-015
status: Superseded
superseded_by: adr-043
---
```

## Document Type Guide

### Architecture Decision Records (ADRs)

**When to create:**
- Choosing a technology or framework
- Defining system architecture
- Changing coding standards
- Making infrastructure decisions

**Required frontmatter:**
```yaml
---
id: adr-NNN
title: Brief decision title
status: Proposed | Accepted | Rejected | Superseded
date: YYYY-MM-DD
tags: [architecture, decision, ...]
project_id: project-name
doc_uuid: uuid-v4
supersedes: adr-XXX  # Optional
superseded_by: adr-YYY  # Optional
---
```

**Structure:**
```markdown
# ADR-NNN: Title

## Status
Current status with context

## Context
The situation and constraints

## Decision
What we decided to do

## Consequences
Positive and negative outcomes

## Alternatives Considered
Why we didn't choose other options
```

**Example ADR topics:**
- "Adopt PostgreSQL for Primary Database"
- "Use GraphQL for API Layer"
- "Implement Event-Driven Architecture"
- "Choose TypeScript for Frontend"

### Request for Comments (RFCs)

**When to create:**
- Proposing new features
- Suggesting major changes
- Introducing new processes
- Cross-cutting concerns

**Required frontmatter:**
```yaml
---
id: rfc-NNN
title: Proposal title
status: Draft | In Review | Approved | Rejected | Implemented
date: YYYY-MM-DD
author: Your Name (or "Claude Code Agent")
tags: [rfc, proposal, ...]
project_id: project-name
doc_uuid: uuid-v4
---
```

**Structure:**
```markdown
# RFC-NNN: Title

## Summary
2-3 sentence overview

## Motivation
Why this is needed

## Proposed Solution
Detailed proposal

## Implementation
How to implement

## Alternatives
Other approaches considered

## Open Questions
Unresolved items
```

**Example RFC topics:**
- "Add Real-Time Notification System"
- "Migrate from Monolith to Microservices"
- "Implement Feature Flag System"
- "Add Multi-Tenancy Support"

### Memos

**When to create:**
- Sharing investigation results
- Documenting meeting outcomes
- Status updates
- Technical explanations

**Required frontmatter:**
```yaml
---
id: memo-NNN
title: Memo title
date: YYYY-MM-DD
author: Your Name (or "Claude Code Agent")
tags: [memo, ...]
project_id: project-name
doc_uuid: uuid-v4
---
```

**Structure:**
```markdown
# Memo: Title

## Purpose
Why this memo exists

## Key Points
- Important findings
- Decisions made
- Context shared

## Next Actions
- [ ] Action items
```

**Example memo topics:**
- "Database Performance Investigation Results"
- "Team Meeting Notes: API Design Review"
- "Security Audit Findings"
- "Migration Progress Update"

## Best Practices for Agents

### 1. Always Validate Before Committing

```bash
# Run validation
docuchango validate

# If errors found, fix them
docuchango fix

# Verify fixes
docuchango validate --verbose
```

### 2. Use Proper Git Commit Messages

```bash
# Good commit messages
git commit -m "Add ADR-042: Adopt Redis for caching

Context: Need to improve API response times
Decision: Use Redis for application-level caching
Consequences: Faster responses, additional infrastructure

🤖 Generated with Claude Code"

# Include references
git commit -m "Update ADR-015: Add session timeout details

Clarifies session handling per RFC-018 discussion.

References: RFC-018, ADR-015
🤖 Generated with Claude Code"
```

### 3. Reference Related Documents

When writing documents, link to related ADRs, RFCs, or memos:

```markdown
## Related Documents

- See [ADR-015](../adr/adr-015-authentication-strategy.md) for auth decisions
- Builds on [RFC-012](./rfc-012-user-management.md)
- Addresses concerns from [Memo-023](../memos/memo-023-security-review.md)
```

### 4. Keep Documents Atomic

Each document should cover ONE decision or topic:
- ✅ ADR: "Adopt PostgreSQL for Primary Database"
- ❌ ADR: "Choose Database, Cache, and Message Queue"

### 5. Update Status When Implementing

When an ADR or RFC is implemented:

```bash
# Update the status
vim docs-cms/adr/adr-042-redis-caching.md
# Change: status: Accepted
# To: status: Implemented

# Commit
git commit -m "Mark ADR-042 as Implemented

Redis caching has been deployed to production."
```

### 6. Propose, Don't Decide

As an agent, you should:
- ✅ Propose ADRs for review
- ✅ Draft RFCs for discussion
- ✅ Suggest updates with rationale
- ❌ Mark your own ADRs as "Accepted" without human review
- ❌ Make architectural decisions unilaterally

Use status: "Proposed" and let humans review and approve.

### 7. Ground Responses in Documentation

**Good response:**
```
According to ADR-023 (Database Schema Migrations), we use Flyway for all
schema changes. This ensures version control and rollback capability.

The migration files should be placed in `src/main/resources/db/migration/`
following the naming pattern `V{version}__{description}.sql`.

See: docs-cms/adr/adr-023-database-migrations.md:45
```

**Bad response:**
```
You should probably use Flyway or Liquibase for migrations. Most projects do that.
```

### 8. Identify and Fill Documentation Gaps

When you notice missing documentation:

1. **Check if it truly doesn't exist**
   ```bash
   grep -r "topic" docs-cms/
   ```

2. **Determine the right document type**
   - Decision made? → ADR
   - Proposal? → RFC
   - Information? → Memo

3. **Create a draft**
   ```bash
   cp docs-cms/templates/adr-template.md docs-cms/adr/adr-NNN-topic.md
   ```

4. **Mark it as needing review**
   ```yaml
   status: Proposed
   # Add in content: "[AI-Generated Draft - Requires Human Review]"
   ```

5. **Commit with explanation**
   ```bash
   git commit -m "Add ADR-NNN draft: Document missing decision on X

   This decision was inferred from codebase analysis but requires
   human confirmation and potential corrections.

   🤖 Generated with Claude Code - NEEDS REVIEW"
   ```

## Searching and Finding Documents

### Find Recent Changes

```bash
# Recent ADRs
ls -lt docs-cms/adr/ | head -10

# Recent commits to docs-cms
git log --oneline docs-cms/ | head -20

# Changes in last 7 days
find docs-cms -name "*.md" -mtime -7
```

### Search by Topic

```bash
# Case-insensitive search
grep -ri "authentication" docs-cms/

# Search only ADRs
grep -r "database" docs-cms/adr/

# Search with context
grep -C 3 "OAuth" docs-cms/
```

### Find by Status

```bash
# Find all Proposed ADRs (need review)
grep -l "status: Proposed" docs-cms/adr/*.md

# Find all Active RFCs
grep -l "status: In Review\|status: Draft" docs-cms/rfcs/*.md

# Find Superseded decisions
grep -l "status: Superseded" docs-cms/adr/*.md
```

### Find by Tag

```bash
# Find all security-related documents
grep -l "tags:.*security" docs-cms/**/*.md

# Find all database decisions
grep -l "tags:.*database" docs-cms/adr/*.md
```

## Common Patterns

### Pattern 1: User Asks "Why did we choose X?"

```bash
# Search for the decision
grep -ri "chose.*X\|adopt.*X\|select.*X" docs-cms/adr/

# Read the ADR
cat docs-cms/adr/adr-NNN-chose-x.md

# Respond with reference
"We chose X because [reasons from ADR]. See ADR-NNN for details."
```

### Pattern 2: User Wants to Change Architecture

```bash
# Check if there's an existing ADR
grep -ri "current-approach" docs-cms/adr/

# Create an RFC for the proposal
cp docs-cms/templates/rfc-template.md docs-cms/rfcs/rfc-NNN-new-approach.md

# Fill it out with:
# - Motivation for change
# - Proposed solution
# - Migration path
# - Alternatives considered

# Validate and commit
docuchango validate
git add docs-cms/rfcs/rfc-NNN-new-approach.md
git commit -m "Add RFC-NNN: Propose migration to new approach"
```

### Pattern 3: Code Doesn't Match Documentation

```bash
# Identify the discrepancy
# Read the relevant ADR
cat docs-cms/adr/adr-015-api-design.md

# Determine which is correct:
# A) Code is wrong → Fix code to match ADR
# B) ADR is outdated → Update or supersede ADR
# C) Both need updating → Create RFC

# For option B:
vim docs-cms/adr/adr-015-api-design.md
# Update with current reality
# Add note about when/why it changed

git commit -m "Update ADR-015: Reflect current API design

The implementation evolved to handle edge cases not
covered in the original design."
```

### Pattern 4: Starting a New Feature

```bash
# 1. Search for related ADRs/RFCs
grep -ri "feature-area" docs-cms/

# 2. Read relevant background
cat docs-cms/adr/adr-XXX-related-decision.md

# 3. Create RFC if significant
cp docs-cms/templates/rfc-template.md docs-cms/rfcs/rfc-NNN-new-feature.md

# 4. Reference related decisions
# In the RFC, include:
## Related Decisions
- ADR-XXX: [Related decision]
- RFC-YYY: [Related proposal]

# 5. Get approval before implementing
```

## Troubleshooting

### "Document not found"
```bash
# List all documents
find docs-cms -name "*.md" -type f

# Search by topic
grep -ri "topic" docs-cms/

# Check if it was deleted
git log --all --full-history -- "docs-cms/adr/adr-NNN*"
```

### "Validation failed"
```bash
# See detailed errors
docuchango validate --verbose

# Common fixes:
# - Missing required frontmatter field
# - Invalid UUID format
# - Broken internal links
# - Invalid status value

# Auto-fix where possible
docuchango fix

# Check schema requirements
cat docuchango/schemas.py | grep -A 20 "class ADRSchema"
```

### "Which document type should I use?"
- **Made a decision?** → ADR
- **Proposing a change?** → RFC
- **Sharing information?** → Memo
- **Not sure?** → Start with Memo, can be converted later

## Integration with Code

### Referencing in Code Comments

```python
# According to ADR-023 (Database Migrations), all schema changes
# must go through Flyway migrations. This ensures version control
# and rollback capability.
#
# See: docs-cms/adr/adr-023-database-migrations.md

class DatabaseMigrator:
    """Handles database schema migrations per ADR-023."""
    pass
```

### Testing Documentation

When writing tests, reference the documented behavior:

```python
def test_authentication_flow():
    """Test OAuth2 flow as specified in ADR-015.

    Per ADR-015 (Authentication Strategy), we use OAuth2 with JWT
    tokens for stateless authentication.

    See: docs-cms/adr/adr-015-authentication-strategy.md:67
    """
    # Test implementation
```

## Resources

- **Bootstrap Guide**: `docs/BOOTSTRAP_GUIDE.md` - How to set up docs-cms
- **Schema Reference**: `docuchango/schemas.py` - Field requirements
- **Templates**: `docs-cms/templates/` - Document templates
- **Examples**: `examples/docs-cms/` - Sample documents

## Remember

1. **Trust the CMS**: It's the source of truth
2. **Always validate**: Before committing any changes
3. **Reference documents**: When answering questions
4. **Propose, don't decide**: Let humans approve architectural decisions
5. **Keep it current**: Update docs as the project evolves
6. **Fill gaps**: Create drafts for missing documentation
7. **Be specific**: Reference exact documents and line numbers
8. **Maintain quality**: Follow naming conventions and schemas

The docs-cms is not just documentation—it's your project memory and decision history. Treat it as a living knowledge base that enables effective human-agent collaboration.
