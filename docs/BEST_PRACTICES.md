# Best Practices for Agent-CMS Interaction

This guide establishes best practices for AI agents working with docs-cms to ground their knowledge and collaborate effectively with humans.

## Core Principles

### 1. The CMS is Your Ground Truth

**Always read docs-cms before acting:**

```bash
# Start every task by scanning relevant docs
grep -ri "topic" docs-cms/
cat docs-cms/adr/adr-relevant.md
```

**Why**: docs-cms contains authoritative project decisions, context, and constraints. Acting without this context leads to:
- Recommendations that contradict decisions
- Repeating discussions already settled
- Missing important context and rationale

**Example - Bad**:
```
User: "Should we use REST or GraphQL?"
Agent: "GraphQL is more modern and flexible, I'd recommend that."
```

**Example - Good**:
```
User: "Should we use REST or GraphQL?"
Agent: *searches docs-cms*
Agent: "According to ADR-023 (API Design Strategy), we use REST because
our clients are diverse and REST provides better compatibility with
legacy systems. GraphQL was considered but didn't meet our needs.

See: docs-cms/adr/adr-023-api-design.md:45"
```

### 2. Propose, Don't Decide

**Agents suggest, humans approve architectural decisions:**

✅ **Good**:
```yaml
---
id: adr-042
status: Proposed  # ← Agent proposes
---

# ADR-042: Adopt Redis for Caching

[Detailed analysis and recommendation]

🤖 AI-Generated Draft - Requires Human Review
```

❌ **Bad**:
```yaml
---
id: adr-042
status: Accepted  # ← Agent shouldn't accept without human
---
```

**Why**: Architectural decisions have long-term consequences. Humans should review and approve significant changes.

### 3. Validate Everything

**Never commit without validation:**

```bash
# Before every commit
docuchango validate --verbose

# If errors, fix them
docuchango fix

# Verify clean
docuchango validate
```

**Why**: Invalid documents break tooling, confuse other agents, and reduce trust in the CMS.

### 4. Reference Specifically

**Always cite sources with precision:**

**Good**:
```
According to ADR-015 (Authentication Strategy), OAuth2 refresh tokens
expire after 7 days, which balances security with user convenience.

Implementation: src/auth/oauth.py:145
Documentation: docs-cms/adr/adr-015-authentication-strategy.md:67
```

**Bad**:
```
We use OAuth2 for authentication. Refresh tokens expire eventually.
```

**Why**: Specific references enable verification and deeper understanding.

### 5. Keep Documentation Current

**Update docs when code changes:**

```bash
# Code change affecting architecture
vim src/auth/oauth.py

# Update corresponding documentation
vim docs-cms/adr/adr-015-authentication-strategy.md

# Commit together
git add src/auth/oauth.py docs-cms/adr/adr-015-authentication-strategy.md
git commit -m "Update OAuth token handling and documentation"
```

**Why**: Stale documentation is worse than no documentation. It misleads and erodes trust.

## Document Lifecycle

### Creating Documents

#### Step 1: Search First

Always check if documentation already exists:

```bash
# Search by topic
grep -ri "authentication" docs-cms/

# Search by tag
grep -l "tags:.*security" docs-cms/**/*.md

# Check recent changes
git log --oneline docs-cms/ | head -20
```

**Why**: Avoid duplicates and build on existing knowledge.

#### Step 2: Choose Document Type

| If you're... | Use... |
|--------------|--------|
| Documenting a decision | ADR |
| Proposing a change | RFC |
| Sharing information | Memo |

**Decision tree**:
```
Has a decision been made?
├─ Yes → ADR
└─ No → Is it a proposal?
    ├─ Yes → RFC
    └─ No → Memo
```

#### Step 3: Copy Template

```bash
# Copy appropriate template
cp docs-cms/templates/adr-template.md docs-cms/adr/adr-042-topic.md

# Generate UUID
uuidgen | tr '[:upper:]' '[:lower:]'
```

#### Step 4: Fill Completely

**All required fields must be filled:**

```yaml
---
id: adr-042                    # ✓ Unique identifier
title: Adopt Redis Caching     # ✓ Clear, specific
status: Proposed               # ✓ Valid status for new docs
date: 2025-10-27              # ✓ Today's date
tags: [caching, redis, perf]  # ✓ Relevant tags
project_id: my-project        # ✓ Your project
doc_uuid: 7c9e6679...         # ✓ Generated UUID v4
---
```

#### Step 5: Write Quality Content

**Good ADR Content**:
- Clear context explaining the problem
- Specific decision with concrete examples
- Both positive and negative consequences
- Alternatives with why they weren't chosen
- Implementation steps if applicable

**Good RFC Content**:
- Compelling motivation
- Detailed proposed solution
- Implementation plan with phases
- Risks and mitigations
- Success metrics

**Good Memo Content**:
- Clear purpose
- Key points upfront
- Supporting details
- Next actions

#### Step 6: Link Related Docs

```markdown
## Related Decisions

- [ADR-015](./adr-015-authentication.md): Authentication strategy
- [RFC-012](../rfcs/rfc-012-user-mgmt.md): User management proposal
- [Memo-023](../memos/memo-023-security.md): Security review findings
```

#### Step 7: Validate and Commit

```bash
# Validate
docuchango validate

# Fix any issues
docuchango fix

# Commit
git add docs-cms/adr/adr-042-redis-caching.md
git commit -m "Add ADR-042 (Proposed): Adopt Redis for application caching

Analysis shows Redis can reduce API latency by 60% while maintaining
data consistency. Proposes phased rollout starting with read-heavy
endpoints.

🤖 Generated with Claude Code - NEEDS REVIEW"
```

### Updating Documents

#### Minor Updates (No Review Needed)

**Examples**:
- Fix typos
- Add clarifying examples
- Update code snippets
- Add related links

**Process**:
```bash
vim docs-cms/adr/adr-015-authentication.md
docuchango validate
git commit -m "ADR-015: Add OAuth refresh token code example"
```

#### Major Changes (Review Required)

**Examples**:
- Reversing a decision
- Significantly changing approach
- Deprecating a decision

**Process**:
```bash
# Create new ADR
cp docs-cms/templates/adr-template.md docs-cms/adr/adr-043-updated-auth.md

# Fill out new ADR
vim docs-cms/adr/adr-043-updated-auth.md
# Set: supersedes: adr-015

# Update old ADR
vim docs-cms/adr/adr-015-authentication.md
# Set: status: Superseded
# Set: superseded_by: adr-043

# Commit both
git add docs-cms/adr/adr-0{15,43}-*.md
git commit -m "ADR-043: Update authentication strategy (supersedes ADR-015)"
```

### Status Transitions

**ADR Status Flow**:
```
Proposed → Accepted → Implemented
        ↓
        Rejected
        ↓
        Superseded
```

**Agent Responsibilities**:
- ✅ Create with `status: Proposed`
- ✅ Mark as `Implemented` when deployed
- ❌ Change to `Accepted` (human decision)
- ❌ Mark as `Rejected` (human decision)
- ✅ Create superseding ADR (with human review)

**RFC Status Flow**:
```
Draft → In Review → Approved → Implemented
      ↓
      Rejected
      ↓
      Withdrawn
```

**Agent Responsibilities**:
- ✅ Create with `status: Draft`
- ✅ Incorporate feedback and update
- ❌ Change to `Approved` (human decision)
- ❌ Mark as `Rejected` (human decision)
- ✅ Mark as `Implemented` when complete

## Grounding Responses in Documentation

### Pattern: User Questions

**User asks**: "Why did we choose PostgreSQL?"

**Agent process**:
1. Search docs-cms:
   ```bash
   grep -ri "postgresql\|postgres" docs-cms/adr/
   ```

2. Read relevant ADR:
   ```bash
   cat docs-cms/adr/adr-008-database-choice.md
   ```

3. Respond with reference:
   ```
   According to ADR-008 (Database Selection), we chose PostgreSQL
   because:

   1. **ACID Compliance**: Critical for financial transactions
   2. **JSON Support**: Needed for flexible metadata storage
   3. **Proven Track Record**: Team has extensive PostgreSQL experience
   4. **Community & Tools**: Rich ecosystem and mature tooling

   MySQL was considered but lacked the JSON capabilities we needed.
   MongoDB was rejected due to consistency concerns for financial data.

   See: docs-cms/adr/adr-008-database-choice.md:34
   ```

### Pattern: Architectural Guidance

**User asks**: "How should I implement user authentication?"

**Agent process**:
1. Search for auth-related ADRs:
   ```bash
   grep -ri "auth\|oauth\|jwt" docs-cms/adr/
   ```

2. Find relevant decisions:
   ```bash
   cat docs-cms/adr/adr-015-authentication-strategy.md
   cat docs-cms/adr/adr-019-session-management.md
   ```

3. Provide grounded guidance:
   ```
   Based on our architectural decisions:

   **Authentication (ADR-015)**:
   - Use OAuth2 with JWT tokens
   - Implement refresh token rotation
   - Token lifetime: Access 15min, Refresh 7 days

   **Session Management (ADR-019)**:
   - Store sessions in Redis for fast lookup
   - Invalidate on password change
   - Support concurrent sessions with limits

   **Implementation**:
   ```python
   from src.auth import OAuthHandler  # Per ADR-015

   handler = OAuthHandler(
       access_ttl=900,    # 15 minutes
       refresh_ttl=604800 # 7 days
   )
   ```

   Related code:
   - `src/auth/oauth.py` - OAuth implementation
   - `src/auth/sessions.py` - Session management
   - `tests/test_auth.py` - Authentication tests

   References:
   - docs-cms/adr/adr-015-authentication-strategy.md
   - docs-cms/adr/adr-019-session-management.md
   ```

### Pattern: Code Review Comments

**When reviewing code**:

**Good review comment**:
```
Per ADR-023 (API Design), all API responses should follow the standard
envelope format:

```json
{
  "data": {...},
  "meta": {
    "timestamp": "2025-10-27T...",
    "request_id": "..."
  }
}
```

Your response is missing the `meta` field. Please add it per the standard.

Reference: docs-cms/adr/adr-023-api-design.md:78
```

**Bad review comment**:
```
API responses should probably have metadata or something.
```

## Identifying Documentation Gaps

### Signs of Missing Documentation

1. **Code without corresponding ADR**
   - Large architectural components
   - Framework choices
   - Design patterns

2. **Repeated questions**
   - Same question asked multiple times
   - Indicates missing documentation

3. **Inconsistent implementations**
   - Different parts of codebase do things differently
   - Suggests missing standards

4. **Tribal knowledge**
   - Information only known by certain people
   - Not written down anywhere

### Filling Gaps

**When you discover a gap**:

1. **Verify it's truly missing**:
   ```bash
   grep -ri "topic" docs-cms/
   git log --all -- "docs-cms/*topic*"
   ```

2. **Create draft documentation**:
   ```bash
   cp docs-cms/templates/adr-template.md docs-cms/adr/adr-042-undocumented-decision.md
   ```

3. **Mark as needing review**:
   ```yaml
   ---
   status: Proposed
   ---

   [AI-Generated Draft - Inferred from Codebase - Requires Review]
   ```

4. **Commit with explanation**:
   ```bash
   git commit -m "Add ADR-042 draft: Document observed authentication pattern

   This decision appears to have been made but not documented. The ADR
   is inferred from:
   - src/auth/oauth.py implementation
   - Test patterns in tests/test_auth.py
   - Comments in code

   REQUIRES HUMAN REVIEW to confirm accuracy and complete context.

   🤖 Generated with Claude Code - NEEDS REVIEW"
   ```

## Common Pitfalls

### 1. Not Searching First

❌ **Mistake**: Creating duplicate documentation

✅ **Solution**: Always search before creating:
```bash
grep -ri "topic" docs-cms/
git log --all -- "docs-cms/**/*topic*"
```

### 2. Incomplete Frontmatter

❌ **Mistake**: Missing required fields

```yaml
---
id: adr-042
title: Something
# Missing: status, date, tags, project_id, doc_uuid
---
```

✅ **Solution**: Use templates and validate:
```bash
cp docs-cms/templates/adr-template.md docs-cms/adr/adr-042-topic.md
# Fill all fields
docuchango validate
```

### 3. Vague References

❌ **Mistake**: "The docs say to use OAuth"

✅ **Solution**: Cite specifically:
```
According to ADR-015 (Authentication Strategy), section 3.2,
OAuth2 with JWT tokens provides stateless authentication.

See: docs-cms/adr/adr-015-authentication-strategy.md:67
```

### 4. Accepting Own Proposals

❌ **Mistake**: Agent sets `status: Accepted`

```yaml
---
id: adr-042
status: Accepted  # ← Agent shouldn't do this
---
```

✅ **Solution**: Use `Proposed` and wait for human review:
```yaml
---
id: adr-042
status: Proposed  # ← Correct
---

🤖 AI-Generated - Requires Human Approval
```

### 5. Breaking Links

❌ **Mistake**: Moving/renaming without updating links

✅ **Solution**: Search for references first:
```bash
# Before moving adr-015-auth.md
grep -r "adr-015" docs-cms/

# Update all references, then move
```

### 6. Skipping Validation

❌ **Mistake**: Committing without validation

✅ **Solution**: Always validate:
```bash
# Before committing
docuchango validate
docuchango fix  # if needed
docuchango validate  # verify

git commit -m "..."
```

### 7. Overwriting Human Decisions

❌ **Mistake**: Changing accepted ADR without superseding

✅ **Solution**: Create new ADR that supersedes:
```bash
# Don't edit ADR-015 status directly
# Instead, create ADR-043 that supersedes it
```

## Integration Patterns

### Pattern: Code Comments Reference Docs

```python
class CacheService:
    """Application-level caching using Redis.

    Implements the caching strategy defined in ADR-042.

    Design:
    - TTL-based expiration per ADR-042:3.1
    - Cache invalidation on writes per ADR-042:3.2
    - Monitoring and alerting per ADR-042:4.1

    See: docs-cms/adr/adr-042-redis-caching.md
    """

    def get(self, key: str) -> Any:
        """Retrieve value from cache.

        TTL handling per ADR-042 section 3.1.
        """
        pass
```

### Pattern: Test References Docs

```python
def test_oauth_refresh_token_rotation():
    """Test refresh token rotation per ADR-015.

    According to ADR-015 (Authentication Strategy), refresh tokens
    must be rotated on each use to prevent replay attacks.

    See: docs-cms/adr/adr-015-authentication-strategy.md:89
    """
    # Test implementation
```

### Pattern: PR Description References Docs

```markdown
## Summary
Implement Redis caching for API responses

## Related Decisions
- Implements [ADR-042](docs-cms/adr/adr-042-redis-caching.md)
- Follows [ADR-019](docs-cms/adr/adr-019-session-management.md) for session caching

## Changes
- Add `CacheService` class per ADR-042:3.1
- Configure Redis connection per ADR-042:2.2
- Add cache invalidation per ADR-042:3.2

## Testing
- Unit tests cover ADR-042 requirements
- Integration tests verify cache behavior
- Performance tests show 60% latency reduction (ADR-042 success metric)
```

## Metrics and Health

### Monitor These Metrics

**Documentation Coverage**:
```bash
# Count documented decisions
find docs-cms/adr -name "*.md" | wc -l

# Count proposals awaiting review
grep -l "status: Proposed" docs-cms/adr/*.md | wc -l
```

**Validation Health**:
```bash
# Check validation pass rate
docuchango validate --verbose
```

**Staleness**:
```bash
# Find docs not updated in 6 months
find docs-cms -name "*.md" -mtime +180
```

**Reference Coverage**:
```bash
# Count code files referencing docs-cms
grep -r "docs-cms/" src/ | wc -l
```

### Success Indicators

✅ **Healthy docs-cms**:
- 95%+ validation pass rate
- All major decisions documented
- Docs updated within 1 month of code changes
- Multiple references from code to docs
- Active proposals and discussions

❌ **Unhealthy docs-cms**:
- Frequent validation failures
- Major decisions undocumented
- Docs 6+ months stale
- No references from code
- No new proposals

## Summary Checklist

Before committing any docs-cms change, verify:

- [ ] Searched for existing documentation
- [ ] Chose appropriate document type
- [ ] Copied from template
- [ ] Filled all required frontmatter fields
- [ ] Generated valid UUID v4
- [ ] Wrote clear, specific content
- [ ] Added code examples where relevant
- [ ] Linked related documents
- [ ] Used appropriate status
- [ ] Ran `docuchango validate`
- [ ] Fixed any validation errors
- [ ] Committed with descriptive message
- [ ] Marked agent-generated docs for review

## Resources

- **Bootstrap Guide**: `BOOTSTRAP_GUIDE.md` - Setup instructions
- **Agent Guide**: `AGENT_GUIDE.md` - Detailed agent instructions
- **Examples**: `examples/docs-cms/` - Sample documents
- **Schemas**: `docuchango/schemas.py` - Field requirements

Remember: The docs-cms is your project memory. Treat it with respect, keep it current, and use it as your ground truth.
