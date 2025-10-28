# docs-cms Examples

This directory contains a complete example `docs-cms` system demonstrating best practices for documentation management and agent collaboration.

## What's Included

### Configuration
- **docs-project.yaml**: Project configuration file

### Sample Documents

#### Architecture Decision Records (ADRs)
- **adr-001-adopt-docs-cms.md**: Decision to adopt docs-cms framework
- **adr-002-agent-collaboration-workflow.md**: Agent collaboration guidelines

#### Request for Comments (RFCs)
- **rfc-001-automated-doc-generation.md**: Proposal for auto-generating API docs

#### Memos
- **memo-001-docs-cms-launch.md**: Launch status and metrics

### Templates
- **adr-template.md**: Template for Architecture Decision Records
- **rfc-template.md**: Template for Request for Comments
- **memo-template.md**: Template for project memos

## How to Use These Examples

### 1. Copy to Your Project

```bash
# Copy entire structure
cp -r examples/docs-cms your-project/docs-cms

# Update project configuration
sed -i 's/example-project/your-project/' your-project/docs-cms/docs-project.yaml

# Update frontmatter in all documents
find your-project/docs-cms -name "*.md" -exec sed -i 's/example-project/your-project/' {} +
```

### 2. Generate New UUIDs

All example documents use placeholder UUIDs. Generate new ones:

```bash
# macOS/Linux
for file in your-project/docs-cms/{adr,rfcs,memos}/*.md; do
    new_uuid=$(uuidgen | tr '[:upper:]' '[:lower:]')
    sed -i "s/doc_uuid: .*/doc_uuid: $new_uuid/" "$file"
done
```

### 3. Customize Content

- Update document content to match your project
- Keep the structure and frontmatter format
- Maintain required fields (id, title, status, etc.)

### 4. Validate

```bash
cd your-project
docuchango validate
```

## Example Walkthrough

### ADR-001: Adopt docs-cms

**Purpose**: Shows how to document the decision to adopt docs-cms

**Key Elements**:
- Clear context explaining the problem
- Specific decision with rationale
- Positive and negative consequences
- Alternatives considered with reasons
- Implementation checklist

**Learn From**:
- How to structure decision documents
- How to present alternatives objectively
- How to link related documents

### ADR-002: Agent Collaboration Workflow

**Purpose**: Demonstrates agent-specific documentation

**Key Elements**:
- Workflow steps for agent interactions
- Code examples and commands
- Clear do's and don'ts
- Status transition rules
- Response formatting guidelines

**Learn From**:
- How to write documentation for AI agents
- How to provide concrete examples
- How to establish clear policies

### RFC-001: Automated Doc Generation

**Purpose**: Example of a substantial proposal

**Key Elements**:
- Problem motivation
- Detailed solution with phases
- Implementation plan with timelines
- Risks and mitigations
- Open questions for discussion
- Success metrics

**Learn From**:
- How to structure large proposals
- How to break work into phases
- How to identify and address risks
- How to define success criteria

### Memo-001: docs-cms Launch

**Purpose**: Shows information sharing format

**Key Elements**:
- Executive summary
- Baseline metrics
- Lessons learned
- Next steps with timelines
- Success criteria
- Related documents

**Learn From**:
- How to document project milestones
- How to capture lessons learned
- How to set measurable goals

## Document Type Guidelines

### When to Use ADRs

✅ **Use for**:
- Technology choices (databases, frameworks, languages)
- Architecture patterns (microservices, event-driven, etc.)
- Infrastructure decisions (cloud provider, CI/CD, etc.)
- Coding standards and conventions

❌ **Don't use for**:
- Proposals (use RFC)
- Status updates (use Memo)
- Temporary information

### When to Use RFCs

✅ **Use for**:
- New features or major changes
- Cross-cutting concerns
- Process improvements
- Design proposals needing feedback

❌ **Don't use for**:
- Final decisions (use ADR)
- Information sharing (use Memo)
- Small changes

### When to Use Memos

✅ **Use for**:
- Meeting notes
- Investigation results
- Status updates
- Technical explanations
- Postmortems

❌ **Don't use for**:
- Decisions (use ADR)
- Proposals (use RFC)

## Customization Tips

### Adding New Document Types

1. Create template in `templates/`
2. Define schema in docuchango (if needed)
3. Add directory (e.g., `postmortems/`)
4. Update `docs-project.yaml`
5. Document usage guidelines

### Adapting for Your Team

**Smaller Teams**:
- Merge ADRs and RFCs (simpler workflow)
- Use lightweight templates
- Focus on key decisions

**Larger Organizations**:
- Add approval workflows
- Include additional metadata (teams, stakeholders)
- Create specialized templates by domain

**Different Industries**:
- Healthcare: Add compliance fields
- Finance: Add regulatory references
- Open Source: Add community discussion links

## Common Patterns

### Pattern: Superseding an ADR

```yaml
# New ADR
---
id: adr-042
title: Updated Database Strategy
status: Accepted
supersedes: adr-015
---

# Old ADR
---
id: adr-015
title: Original Database Strategy
status: Superseded
superseded_by: adr-042
---
```

### Pattern: RFC → ADR Flow

1. Create RFC with `status: Draft`
2. Gather feedback, update RFC
3. Change status to `In Review`
4. After approval: `status: Approved`
5. Create ADR documenting final decision
6. Update RFC: `status: Implemented`, link to ADR

### Pattern: Agent-Generated Draft

```yaml
---
id: adr-043
title: Redis Caching Strategy
status: Proposed  # Agent uses Proposed
---

[AI-Generated Draft - Requires Human Review]

# ADR-043: Redis Caching Strategy
...
```

## Validation

All example documents pass docuchango validation:

```bash
$ cd examples
$ docuchango validate

Scanning docs-cms/...
✓ Found 4 documents
✓ All frontmatter valid
✓ All internal links resolve
✓ All code blocks properly formatted
✓ No validation errors

Summary: 4/4 documents passed validation (100%)
```

## Resources

- **Bootstrap Guide**: `../docs/BOOTSTRAP_GUIDE.md` - Setup instructions
- **Agent Guide**: `../docs/AGENT_GUIDE.md` - Agent collaboration guidelines
- **Schema Reference**: `../docuchango/schemas.py` - Field requirements
- **Main README**: `../README.md` - docuchango documentation

## Contributing Examples

Have a great example document or pattern? Contributions welcome!

1. Ensure it passes `docuchango validate`
2. Follow existing structure and conventions
3. Include clear explanation of what it demonstrates
4. Update this README with your example

## Questions?

- **Setup Issues**: See `BOOTSTRAP_GUIDE.md`
- **Agent Usage**: See `AGENT_GUIDE.md`
- **Validation Errors**: Run `docuchango validate --verbose`
- **Schema Questions**: Check `docuchango/schemas.py`
