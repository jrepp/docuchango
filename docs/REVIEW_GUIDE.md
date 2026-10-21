# Evidence-Based Review and Design Maintenance

Use this guide to review a PRD, RFC, ADR, memo, or a focused amendment. The depth
should fit the change. These are authoring practices, not new validator checks,
approval statuses, or required metadata.

## Establish what is being reviewed

Identify the document, its revision, the requested change, and the governing
requirements or decisions. Distinguish current implementation from proposed design.
For a focused amendment, compare both versions; an inherited problem is not a new
defect merely because the reviewer noticed it now.

State what sources were read and what could not be assessed. Missing evidence is
not evidence of absence. Before claiming a design omits something, inspect its
scope, explicit deferrals, relevant sibling documents, and terminology. A source
may be stale; neither a newer-looking date nor the current code automatically
establishes authority over the agreed requirement.

## Verify claims at their sources

Read the supporting passage before deciding whether the document represents it
accurately. For claims about current code, inspect defining sites for named paths,
interfaces, enum values, and defaults. A symbol mention or a plausible convention
does not establish actual behavior. Mark not-yet-built behavior as planned.

Distinguish:

- **Observation:** what a source or execution actually shows, with context.
- **Interpretation:** what the author infers from that observation.
- **Recommendation:** what should change, with rationale and assumptions.

Include relevant contradictory evidence and observation limits. Do not convert
one report into a recurring pattern or paraphrase an inference as a direct quote.
For consequential choices, ask what evidence would reverse the recommendation.

## Write actionable findings

| Finding element | What to record |
|-----------------|----------------|
| Location | Exact section or code reference and the claim being questioned |
| Governing evidence | Requirement, decision, source passage, or reproducible observation |
| Condition and consequence | When the concern matters and what could go wrong |
| Classification | Established defect, scope/priority decision, factual question, or suggestion |
| Correction | Smallest supported change, or the evidence/decision still needed |

For an omission, cite the relevant promise and explain the scope searched. Do not
invent a quote for absent text. Confirm each finding against its evidence before
acting; agreement between reviewers is not a substitute for verification.

An established defect can justify a fix. Known facts with competing scope or
priority choices need a decision. Missing facts need investigation or an author
answer. Advice without a governing requirement is a suggestion, not a defect.

### Disposition and resolution

| Disposition | Appropriate use | Completion evidence |
|-------------|-----------------|---------------------|
| Fix | Evidence determines a needed correction | Changed passage and relevant recheck |
| Decline | Claim disproved, preference not adopted, or outside agreed scope | Reason and supporting evidence or scope decision |
| Defer | Valid concern intentionally handled separately | Follow-up reference or owner/next step; not described as fixed |
| Needs evidence/decision | Remedy cannot yet be established | Specific missing fact or decision; remains open |

Replying, editing, and verifying are separate actions. A reply does not prove a
fix landed. Recheck the changed passage and affected examples, tables, and tests
before reporting a fixed finding resolved. Record an agreed decline or deferral
honestly instead of labeling it implemented. An ignore marker alone establishes
neither correctness nor completed remediation.

Do not broaden a focused change to satisfy every suggestion. For example, adding
one schema value may require matching fixer behavior, but does not automatically
authorize new aliases or a redesign of every document lifecycle.

## Review amendments for preserved meaning

Apply the [meaning-preservation check](ACCEPTANCE_CRITERIA.md#preserve-meaning-when-amending-criteria).
Keep source obligations, exceptions, IDs, and decision authority visible.
Separate restructuring from clarification and changed requirements. Reviewer
preferences and illustrative mechanisms do not become requirements automatically.

For architectural choices, retain the original rationale and identify what changed:
an assumption, external constraint, observed failure, or product requirement.
State the evidence or condition that would cause another reconsideration.

## Assess downstream impact

Use a small table when a substantive decision or contract changes:

| Changed decision | Affected artifact or criterion | Proposed follow-up | Owner/state |
|------------------|--------------------------------|--------------------|-------------|
| Error contract changes | RFC response example and integration scenario | Reconcile expected response with agreed decision | Engineering; pending |
| Requirement deferred | Implementation plan coverage | Confirm scope and adjust planned work | Product/engineering; unresolved |
| Completed behavior conflicts | Existing implementation and tests | Propose a separate follow-up or record an agreed exception | Maintainer; decision needed |

Name the artifacts actually checked. If no dependents were supplied or inspected,
report impact as not assessed rather than claiming full synchronization.
Preserve completed-work history and existing blockers. Do not silently reopen
completed items, mark blocked work complete, or manufacture future artifacts.

After an approved update, record what was applied and verified separately from
what was only proposed. Recheck meaningful restatements of a changed concept,
including examples and differently worded references. Keep historical rationale
labeled as history rather than deleting it to make the documents appear consistent.

## Check whether another reader can use the document

Choose a realistic task and ask a reader to attempt it using the document alone:

- Plan the first implementation change.
- Construct a client request and handle its possible responses.
- Recover after a failed migration.
- Determine how an existing configuration behaves after an upgrade.

Record where the reader must guess about required behavior. An intentional open
question is not automatically a defect; confirm whether it blocks this task.
Check links, images, and referenced files from the intended shared location.
Necessary rationale and caveats must not depend on the author's private notes.

Keep template instructions and session bookkeeping out of the finished product
document. Preserve genuine uncertainty when improving prose: changing “proposed”
to “accepted” or “may” to “will” changes meaning, not just style.

## Report the result without overstating assurance

A useful summary names the version reviewed, sources checked, findings and
dispositions, unperformed checks, and next action. A clean result means no defects
were found within that stated scope. It is not proof of exhaustive correctness,
implementation completion, or approval by the decision owner.

Numeric scores, reviewer counts, and a fixed number of review rounds are not
required. Use source-backed findings and verified outcomes to explain readiness.
