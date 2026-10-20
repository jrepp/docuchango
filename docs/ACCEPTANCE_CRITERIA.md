# From Requirements to Acceptance Evidence

Use this guide when writing a PRD, FRD, or RFC. It connects product behavior to
technical contracts and verification without requiring new metadata or a separate
acceptance-criteria document. A small change may need only one requirement and a
few scenarios; expand the structure when the risks justify it.

## Why connect the documents?

A well-structured RFC can describe a plausible implementation without satisfying
the intended user outcome. Tests can then confirm that implementation rather than
the requirement. References make it easier to find both missing coverage and
technical behavior introduced without an agreed source.

- **PRD/FRD:** Which user outcome is required, under what conditions?
- **RFC:** Which technical contract and design satisfy that outcome?
- **Verification:** What evidence distinguishes correct behavior from failure?

Keep one authoritative requirement statement. Reference it rather than duplicating
it in each artifact. Stable IDs help reviewers find the same behavior after edits;
do not renumber existing criteria simply to insert another one.

## Worked example: inspecting documentation without changing it

The following PRD and RFC excerpts are an illustrative proposal, not a statement
of the current CLI defaults or an accepted change to them. Use a project's actual
agreed requirements when applying this format.

### PRD excerpt

**User story:** As a documentation author, I want to inspect problems before
applying repairs so that I can choose when my files change.

| Requirement | Outcome | Scope |
|-------------|---------|-------|
| FR-1 | Inspection reports documentation problems without modifying source files. | In this example |
| FR-2 | The author can explicitly apply proposed repairs. | Deferred to a separate repair RFC |

#### AC-1: Report a repairable issue without writing

Source: FR-1

- **Given** a document containing a known repairable formatting issue
- **When** the author runs inspection in read-only mode
- **Then** the issue is reported
- **And** the document remains byte-for-byte unchanged

#### AC-2: Preserve files when inspection fails

Source: FR-1

- **Given** a project with a valid document and a document with invalid metadata
- **When** the author runs inspection in read-only mode
- **Then** the invalid metadata is reported and inspection indicates failure
- **And** both documents remain byte-for-byte unchanged

#### AC-3: Inspect a valid document

Source: FR-1

- **Given** a document satisfying the configured checks
- **When** the author runs inspection in read-only mode
- **Then** inspection indicates success without reporting a problem
- **And** the document remains byte-for-byte unchanged

These criteria describe observable behavior. “Add a read-only flag” would describe
an implementation task without establishing any of these preservation guarantees.

### RFC excerpt

**Scope:** Implements FR-1 and AC-1 through AC-3 from the PRD excerpt above.
FR-2 is deferred; this design does not authorize applying repairs.

**Proposed technical contract for review:** For this example, inspection emits
the applicable documented finding ID, returns exit status `1` when findings
remain, and returns `0` when no findings remain. These interface details are
proposals until agreed; they must not be inferred from the user story alone.

**Design:** Parse and check documents without invoking write operations in the
inspection path. Preserve source bytes, not merely equivalent parsed metadata.
The design can change internally as long as the agreed interface and preservation
guarantees hold.

| Source | Criterion | Design responsibility | Planned verification |
|--------|-----------|-----------------------|----------------------|
| PRD excerpt / FR-1 | AC-1 | Read-only inspection and reporting | CLI integration: repairable fixture, finding ID, byte comparison |
| PRD excerpt / FR-1 | AC-2 | Failure reporting without partial writes | CLI integration: mixed-validity project, exit status, all-file byte comparison |
| PRD excerpt / FR-1 | AC-3 | Successful inspection without writes | CLI integration: valid fixture, exit status, empty findings, byte comparison |

**Verification detail:** Capture the file bytes before invocation, run the CLI,
then compare the bytes and the agreed output/exit status. A test checking only
that a write helper was not called would miss writes performed through another
path. A test comparing parsed YAML alone would miss unwanted formatting changes.

**Open question:** Should standard input be supported? The CLI design owner must
decide before adding acceptance criteria for streams. This is outside the file-only
scope above and does not block those criteria.

### Recording evidence

The table describes planned coverage. During implementation, link each criterion
to its test or manual verification procedure. Keep execution results in CI or a
release record, with the revision and environment evaluated. A populated table
does not establish that tests exist, pass, or detect the intended failure.

Successful tests demonstrate the specified behavior. Whether authors find the
workflow useful is a separate product question that needs user feedback or other
outcome evidence.

## Writing guidance

### Separate requirements from technical decisions

Reference the source for each technical constraint. If the source does not settle
a behavior, label it as proposed or record an open question. Agents and reviewers
should not manufacture requirements just to complete a template.

An exact response shape or an internal ordering rule can be necessary, but explain
why. Do not freeze helper names, file layouts, or incidental implementation choices
as acceptance criteria. Verify internal constraints with unit or integration tests
when they cannot be observed at the public interface.

### Select meaningful failure and boundary scenarios

Ask what must remain true during invalid input, partial failure, retries,
concurrency, empty results, and compatibility transitions where relevant. State
allowed side effects and recovery behavior. “Returns an error” is not enough if
the operation might already have changed persistent state.

Do not add a concurrency scenario to a static documentation change solely because
it appears in the template. Coverage should follow risks, not scenario counts.

### Make quantitative criteria reproducible

For a performance target, specify the metric and percentile, workload/concurrency,
dataset, environment, observation period, and measurement method. Cite the source
or rationale for the target. A p95 result does not demonstrate a p99 requirement;
different operation-level budgets must explain their relationship to broader goals.

If the target or workload is unknown, record an open question instead of inventing
a number. A passing test suite is delivery evidence, not proof of adoption or user
satisfaction.

### Resolve accidental ambiguity

“Return a warning or reject the request” leaves the outcome undecided. Name an
owner, affected criterion, and next step. State whether the question blocks that
work, rather than blocking all implementation automatically.

Multiple outcomes may be intentional, especially under concurrency. In that case,
define the allowed outcome set and the invariant that holds for each. The goal is
an evaluable contract, not forced determinism where the design does not require it.

## Review checklist

- Can the user outcome be understood without reading implementation code?
- Does each in-scope requirement have design and verification coverage?
- Are deferrals explicit, and new technical decisions clearly labeled?
- Could the proposed check detect the specific incorrect behavior it targets?
- Are measurement conditions and the source of each numerical target stated?
- Are IDs stable and references maintained without competing requirement copies?
- Is the amount of documentation proportionate to the change?

These are authoring aids, not additional `docuchango validate` rules. The presence
of Given / When / Then keywords does not prove that a scenario is meaningful.

## Templates

- Bundled PRD: `docuchango/templates/prd-000-template.md`
- Bundled RFC: `docuchango/templates/rfc-000-template.md`
- [Detailed PRD](../templates/prd-template.md)
- [Detailed RFC](../templates/rfc-template.md)
- [Detailed FRD](../templates/frd-template.md)

`docuchango init` copies the bundled templates into a new project's `templates/`
directory. They contain self-contained guidance; this longer example is a
repository reference. Existing documents do not require migration.
