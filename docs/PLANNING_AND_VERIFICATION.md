# Lightweight Implementation and Verification Planning

This optional example extends the [read-only inspection example](ACCEPTANCE_CRITERIA.md)
from requirements into executable work. It illustrates a proposed contract, not
the current command defaults or a new requirement for Docuchango projects. A small
change can keep this material in its RFC or PR description.

## Keep the artifacts' purposes distinct

| Artifact | Question it answers |
|----------|---------------------|
| Acceptance criterion | Which feature behavior must hold? |
| Technical contract | Which interface or internal guarantee delivers that behavior? |
| Implementation plan | Which reviewable changes deliver it, with which dependencies? |
| Test plan | Which scenarios, risks, and environments need verification? |
| Test case | Which setup, action, and observations make a scenario executable? |
| Automated test | How does the repository execute those checks? |
| Definition of Done | Which shared delivery checks apply, such as review or lint? |

A test case can be code rather than a separate document. One criterion may need
several scenarios, and one scenario may exercise several related criteria. Do not
force a one-to-one mapping or duplicate a test under API and end-to-end labels
when it exercises the same behavior through the same interface.

## Inspect existing work before planning

Read the relevant code, tests, and repository instructions. Identify actual paths,
helpers, fixtures, and test commands. Distinguish intended behavior from observed
implementation. If behavior already exists, plan verification rather than silently
proposing to build it again. Code can establish current behavior but cannot approve
a change to product scope.

Record conflicts between requirements, design, and existing behavior for their
owners. Classify a deliverable as blocked only if it cannot proceed without a
missing decision. Other work may proceed on explicit, justified assumptions or
remain ready for verification. Do not infer that every deliverable is blocked
because one question is unresolved.

## Implementation-plan example

Source baseline: the PRD/RFC excerpts in the linked worked example. For real work,
record the source path and revision where needed. The interface details remain
proposals until agreed.

| Step | Outcome | Criteria | Dependencies | Verification included in step |
|------|---------|----------|--------------|-------------------------------|
| 1 | Inspect a valid document without writes | AC-3 | Confirm command interface | CLI integration: success status, no findings, unchanged bytes |
| 2 | Report a repairable issue without applying it | AC-1 | Step 1 reporting path | CLI integration: finding identifier, unchanged bytes |
| 3 | Preserve every source file when validation fails | AC-2 | Steps 1–2 | Mixed-validity fixture: failure status and all-file byte comparison |

These are reviewable behavior changes, not one task per file or helper. Each step
includes its relevant tests and repository checks. If the actual implementation
couples them tightly, combine the steps rather than create artificial boundaries.

### Example step: report an issue without writing

- **Input:** AC-1 and the agreed reporting contract.
- **Change:** Reuse the existing inspection/reporting path where available; avoid
  invoking repair writes in read-only mode.
- **Verification:** Seed a known repairable fixture, capture its bytes, invoke the
  agreed read-only command, and inspect both findings and file bytes.
- **Done when:** The expected finding is reported, the bytes are unchanged, the
  relevant tests and lint pass, and applicable user guidance reflects the behavior.
- **Blocker:** If the exit-status contract remains undecided, identify its owner
  and dependent assertion rather than inventing a status code.

Use the repository's real commands in a concrete plan. Do not paste an imagined
test invocation from an example. Include testing and review effort when estimating;
state uncertainty rather than apply universal day counts or multipliers.

## Optional test-plan example

**Scope:** File-based read-only inspection. Applying repairs and reading standard
input are outside this example. Their exclusion does not remove the requirement
to preserve files when inspection fails.

**Environment:** An isolated temporary project with known fixtures and the built
CLI for the revision under test. Reuse the repository's fixture and CLI-runner
conventions. No live user documentation is modified to test the checker.

| Scenario | Criteria | Setup and action | Expected observation |
|----------|----------|------------------|----------------------|
| S-1: Valid input | AC-3 | Inspect a valid document | Success, no findings, identical before/after bytes |
| S-2: Repairable issue | AC-1 | Inspect a document containing a known repairable issue | Expected finding, identical before/after bytes |
| S-3: Mixed-validity project | AC-2; preservation aspect of AC-1 | Inspect a valid document, a repairable document, and invalid metadata together | Failure and relevant findings; all original bytes unchanged |

### Executable case for S-3

1. Create the isolated project and all three fixtures with known content.
2. Snapshot each file's bytes before invocation.
3. Run the agreed read-only inspection command through the existing CLI harness.
4. Assert the agreed failure exit status and the expected finding identifiers.
5. Compare every source file with its snapshot, then clean up the temporary project.

The byte comparison is the test oracle for preservation: parsed-YAML equality
would miss formatting changes. Checking only that one write helper was not called
would miss another write path. Use intermediate assertions where needed to detect
an invalid setup; do not defer every assertion mechanically to the end.

## Coverage and evidence

| State | Meaning |
|-------|---------|
| Planned | Scenario identified, execution not established |
| Partial | Some behavior checked, with the missing assertion or case named |
| Verified | Evidence identifies the tested revision, environment, command, and result |
| Blocked / not run | Specific missing decision, dependency, or execution limit recorded |

After implementation, link criteria/scenarios to their actual test names. Store
run results in CI or a release record rather than copying a permanent “passed”
claim into the RFC. Skipped tests are not passes. A changed requirement or source
revision may require rechecking evidence that was valid for an earlier version.

Shared Definition of Done checks (peer review, lint, documentation, release work)
remain separate from feature acceptance. Cite the delivery convention for a task
that has no feature AC instead of borrowing an unrelated ID.

Use the [review guide](REVIEW_GUIDE.md) to disposition gaps. Do not fabricate metrics,
API details, environments, or extra scenarios to achieve a count. Quantitative
tests need agreed targets and measurement conditions before they can establish a
pass/fail result. Select depth based on risk and preserve project conventions.
