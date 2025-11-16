# Frontmatter CMS Issues - Probability Analysis

## High Probability (>70%) - Implement Auto-Fixes

### 1. Inconsistent Tag Formatting (90%)
**Issue:** Tags in different formats (string vs array, mixed case, spaces)
- `tags: backend` (should be array)
- `tags: ["Backend", "frontend"]` (inconsistent case)
- `tags: ["API Design", "api-design"]` (spaces vs dashes)

**Auto-fix:**
- Convert string tags to arrays
- Normalize to lowercase with dashes
- Remove duplicates
- Sort alphabetically

### 2. Missing Required Fields (85%)
**Issue:** Documents missing critical fields
- Missing `doc_uuid` (required for cross-references)
- Missing `project_id` (required for multi-project setups)
- Missing `tags` field (should be empty array, not absent)

**Auto-fix:**
- Generate UUID if missing
- Set default project_id from config
- Add empty tags array if missing

### 3. Trailing/Leading Whitespace in Values (80%)
**Issue:** Values with extra whitespace
- `title: " My Document "`
- `status: "Accepted "`
- `deciders: "Team Lead "`

**Auto-fix:**
- Trim all string values
- Preserve intentional spacing in content

### 4. Inconsistent Field Ordering (75%)
**Issue:** Fields in random order across documents
- Makes diffs harder to review
- Inconsistent with templates

**Auto-fix:**
- Reorder fields to match template
- Standard order: id, title, status, created, updated, date, deciders, tags, project_id, doc_uuid

### 5. Boolean Values as Strings (70%)
**Issue:** Boolean fields stored as strings
- `deprecated: "true"` (should be `true`)
- `draft: "false"` (should be `false`)

**Auto-fix:**
- Convert string "true"/"false" to boolean
- Handle case variations (True, TRUE, etc.)

## Medium Probability (40-70%) - Implement Auto-Fixes

### 6. Empty String vs Null vs Missing (60%)
**Issue:** Inconsistent handling of empty values
- `description: ""` vs `description: null` vs field missing
- Affects validation and queries

**Auto-fix:**
- Remove fields with empty strings (prefer missing)
- Convert null to missing for optional fields
- Keep empty arrays for list fields

### 7. Numeric Values as Strings (55%)
**Issue:** Numbers stored as strings
- `priority: "1"` (should be `1`)
- `version: "2"` (should be `2`)

**Auto-fix:**
- Convert numeric strings to numbers
- Preserve semantic versions as strings ("1.2.3")

### 8. Inconsistent Author/Deciders Format (50%)
**Issue:** Author fields in different formats
- `deciders: "John Doe"` (single string)
- `deciders: "John, Jane"` (comma-separated)
- `deciders: ["John", "Jane"]` (array - correct)

**Auto-fix:**
- Convert single string to array
- Split comma-separated strings
- Trim whitespace from names

### 9. Duplicate Field Definitions (45%)
**Issue:** Same field defined multiple times (YAML allows this)
- Last value wins, creates confusion
- Usually copy-paste errors

**Auto-fix:**
- Detect and remove duplicate keys
- Keep the last occurrence (YAML behavior)
- Warn user in verbose mode

### 10. Related Document References (40%)
**Issue:** Cross-references in wrong format
- `supersedes: adr-001` (string, should be array)
- `related: ["adr-001", "ADR-002"]` (inconsistent case)
- Missing doc_uuid references

**Auto-fix:**
- Normalize to arrays
- Standardize case to lowercase
- Validate referenced docs exist
- Add doc_uuid lookups

## Low Probability (20-40%) - Manual Fix Recommended

### 11. Title/ID Mismatch Content (35%)
**Issue:** Title describes different content than document
- Likely needs human review
- Could check for similarity

### 12. Outdated Status (30%)
**Issue:** Status doesn't reflect current state
- "In Review" but merged 6 months ago
- Needs context to determine correct status

### 13. Missing Descriptions/Summaries (25%)
**Issue:** Optional description fields empty
- Could generate from first paragraph
- Quality concerns with auto-generation

### 14. Inconsistent Terminology (20%)
**Issue:** Same concepts described differently
- "API" vs "api" vs "Application Programming Interface"
- Needs taxonomy/glossary

## Very Low Probability (<20%) - Detection Only

### 15. Invalid YAML Syntax (15%)
**Issue:** Broken YAML that doesn't parse
- Usually caught immediately
- Validation catches this

### 16. Encoding Issues (10%)
**Issue:** Non-UTF-8 characters
- Rare in modern editors
- Usually editor/system issue

### 17. Merge Conflict Markers (5%)
**Issue:** Git merge markers in frontmatter
- `<<<<<<< HEAD`
- Very rare, usually caught by CI

## Implementation Priority

### Phase 1 (This PR) - High Impact, High Confidence
1. ✅ Invalid status values (already implemented)
2. ✅ Invalid date formats (already implemented)
3. ✅ Missing frontmatter blocks (already implemented)
4. **Tags normalization** - NEW
5. **Missing required fields** - ENHANCE EXISTING
6. **Whitespace trimming** - NEW
7. **Field ordering** - NEW

### Phase 2 (Next PR) - Medium Impact
8. Boolean string conversion
9. Empty value normalization
10. Numeric string conversion
11. Author/deciders format

### Phase 3 (Future) - Lower Impact
12. Duplicate field detection
13. Related document references
14. Status consistency checks

## Auto-Fix Confidence Levels

**High Confidence (Safe to auto-fix):**
- Tags normalization (reversible, clear rules)
- Whitespace trimming (no semantic change)
- Boolean/numeric conversions (type-safe)
- Missing required fields with defaults (additive)

**Medium Confidence (Auto-fix with warnings):**
- Field reordering (changes diff, but semantically same)
- Empty value normalization (could affect queries)
- Duplicate field removal (might not be obvious which to keep)

**Low Confidence (Suggest fixes only):**
- Status consistency (needs context)
- Title/content mismatch (subjective)
- Missing descriptions (quality concerns)
