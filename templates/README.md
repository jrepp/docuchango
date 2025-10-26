# Document Templates

Templates for creating structured documentation with proper frontmatter validation.

## Available Templates

### Decision Documents

- **adr-template.md** - Architecture Decision Record
  - Use for documenting significant architectural decisions
  - Includes context, options analysis, and decision rationale

- **rfc-template.md** - Request for Comments
  - Use for proposing new features or significant changes
  - Includes detailed design, alternatives, and implementation plan

### Product Documents

- **prd-template.md** - Product Requirements Document
  - Use for defining product vision and requirements
  - Includes goals, user stories, and success metrics

- **frd-template.md** - Feature Requirements Document
  - Use for detailed feature specifications
  - Includes user stories, acceptance criteria, and technical details

- **prdfaq-template.md** - Product FAQ (Press Release + FAQ)
  - Use for product announcements and stakeholder communication
  - Includes press release format and comprehensive FAQ

### General Documents

- **memo-template.md** - Technical Memo
  - Use for documenting technical findings, analyses, or decisions
  - Includes executive summary and action items

- **generic-doc-template.md** - Generic Documentation
  - Use for guides, tutorials, or reference documentation
  - Minimal required frontmatter

## Usage

1. Copy the appropriate template
2. Rename with proper ID/number (e.g., adr-042-feature-name.md)
3. Update all frontmatter fields:
   - Replace XXX with actual number
   - Update dates to current date
   - Replace placeholder UUIDs (generate with `uuidgen`)
   - Update project_id to match your project
4. Fill in content sections
5. Validate with: `docuchango validate`

## Frontmatter Requirements

### ADR (Architecture Decision Record)
Required: `id`, `title`, `status`, `date`, `deciders`, `tags`, `project_id`, `doc_uuid`

### RFC (Request for Comments)
Required: `id`, `title`, `status`, `author`, `created`, `updated`, `tags`, `project_id`, `doc_uuid`

### Memo
Required: `id`, `title`, `author`, `date`, `created`, `updated`, `tags`, `project_id`, `doc_uuid`

### PRD/FRD/PRDFAQ
Required: `id`, `title`, `status`, `author`, `created`, `updated`, `tags`, `project_id`, `doc_uuid`

### Generic
Required: `title`, `project_id`, `doc_uuid`
Optional: `description`, `sidebar_position`, `tags`, `id`

## Generating UUIDs

```bash
# macOS/Linux
uuidgen | tr '[:upper:]' '[:lower:]'

# Python
python -c "import uuid; print(uuid.uuid4())"

# Node.js
node -e "console.log(require('crypto').randomUUID())"
```

## Validation

All templates are designed to pass docuchango validation:

```bash
# Validate a single document
docuchango validate --repo-root /path/to/docs

# Fix common issues
docuchango fix all --repo-root /path/to/docs
```

## Template Customization

To customize templates for your organization:

1. Copy templates to your project
2. Modify frontmatter fields as needed
3. Update content structure
4. Commit to your repository
5. Share with team

## Related

- [Docuchango Documentation](https://github.com/jrepp/docuchango)
- [Pydantic Schema Definitions](../docuchango/schemas.py)
