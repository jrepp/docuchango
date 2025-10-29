# Documentation CMS

This directory contains structured technical documentation using the docs-cms pattern.

## Directory Structure

```
docs-cms/
├── docs-project.yaml      # Project configuration
├── adr/                   # Architecture Decision Records
│   └── adr-000-template.md
├── rfcs/                  # Request for Comments
│   └── rfc-000-template.md
├── memos/                 # Technical Memos
│   └── memo-000-template.md
├── prd/                   # Product Requirements Documents
│   └── prd-000-template.md
└── templates/             # Document templates
```

## Document Types

### ADR (Architecture Decision Records)
Architecture decisions that have been made or are being considered. Use these to document significant architectural choices and their rationale.

**Filename format**: `adr-NNN-short-description.md` (lowercase, dashes)

### RFC (Request for Comments)
Proposals for new features, changes, or processes that need team review and discussion.

**Filename format**: `rfc-NNN-short-description.md` (lowercase, dashes)

### Memos
Technical notes, findings, research, or informal documentation that doesn't fit the ADR/RFC structure.

**Filename format**: `memo-NNN-short-description.md` (lowercase, dashes)

### PRD (Product Requirements Documents)
Product requirements and feature specifications.

**Filename format**: `prd-NNN-short-description.md` (lowercase, dashes)

## Getting Started

1. **Copy a template** from the `templates/` folder
2. **Rename the file** with the next available number and a descriptive slug
3. **Update the frontmatter** with project-specific information
4. **Write your content** following the template structure

## Validation

Run validation to check your documents:

```bash
# Validate all documents
docuchango validate

# Validate with verbose output
docuchango validate --verbose

# Auto-fix common issues
docuchango validate --fix
```

## Configuration

Edit `docs-project.yaml` to customize:
- Project metadata
- Folder names
- Which folders to scan
- Maintainer information

## Best Practices

- Use meaningful, descriptive slugs in filenames
- Keep frontmatter fields up to date
- Use lowercase with dashes for IDs and filenames
- Update the `updated` field when making changes
- Use appropriate tags for categorization
- Link to related documents using relative paths

## Need Help?

```bash
# Display bootstrap guide
docuchango bootstrap

# Display agent guide
docuchango bootstrap --guide agent

# Display best practices
docuchango bootstrap --guide best-practices
```
