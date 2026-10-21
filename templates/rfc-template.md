---
# REQUIRED FIELDS - All must be present for validation to pass
id: "rfc-XXX"  # Lowercase format: "rfc-XXX" where XXX matches filename number (e.g., "rfc-001")
slug: rfc-XXX-brief-description  # URL-friendly slug (lowercase-with-dashes)
title: "RFC-XXX: Technical Proposal Title"  # Must start with "RFC-XXX:" where XXX is 3-digit number
status: Draft  # Valid values: Draft, Proposed, Accepted, Rejected, Implemented, Deprecated, Superseded
created: YYYY-MM-DD  # ISO 8601 format (YYYY-MM-DD) - date RFC was first created, DO NOT CHANGE after initial creation
                     # Generate: date +%Y-%m-%d  OR  python -c "from datetime import date; print(date.today())"  OR  auto-set with: docuchango bulk timestamps
author: Your Name  # Person or team who wrote this RFC (e.g., "Jacob Repp", "Platform Team")
                   # Generate: git config user.name
tags: ["architecture", "api", "backend"]  # List of lowercase-with-dashes tags (e.g., ["performance", "security"])
project_id: "your-project-id"  # Project identifier from docs-project.yaml
doc_uuid: "00000000-0000-4000-8000-000000000000"  # UUID v4 - Generate: uuidgen  OR  python -c "import uuid; print(uuid.uuid4())"
---

# RFC-XXX: Technical Proposal Title

## Summary

Brief one-paragraph description of the proposed change.

What are we building/changing and why? Include the high-level approach in 2-3 sentences.

## Motivation

Why are we doing this? What use cases does it support? What problems does it solve?

### Problem Statement

Describe the current pain points or limitations:
- What's broken or missing?
- Who is affected?
- What's the impact if we don't solve this?

### Goals

What we aim to achieve with this proposal:

- **Goal 1**: Specific, measurable outcome
- **Goal 2**: Specific, measurable outcome
- **Goal 3**: Specific, measurable outcome

### Non-Goals

What this proposal explicitly does not address:

- Out of scope item 1 (explain why)
- Future work that might be related but is deferred
- Related problems we're not solving now

### Success Criteria

How will we know this is successful?

- **Metric 1**: Target value (e.g., "API latency < 100ms at p99")
- **Metric 2**: Target value (e.g., "99.9% uptime")
- **Metric 3**: Target value (e.g., "Support 10K requests/sec")

## Proposal

Detailed description of the proposed solution.

### Requirements Coverage

Reference the parent PRD's requirements and acceptance criteria. Without a parent
PRD, state requirements and their rationale here. Preserve IDs across revisions.

For long-running work, identify the source baseline (path plus commit, version,
or date where needed). Check ranges against actual AC definitions, including gaps;
do not invent missing IDs. Repeated references are valid; duplicate definitions
or ambiguous source documents need clarification.

| Source requirement | Acceptance criterion | Disposition | Design section | Verification |
|--------------------|----------------------|-------------|----------------|--------------|
| [PRD reference / FR-1] | AC-1 | [Covered / deferred / unresolved] | [Relevant section] | [Test level and evidence] |

Identify deferred requirements explicitly. Keep one authoritative requirement
statement and reference it; technical details supplement rather than rewrite
the product contract. A short list is enough for a small change.
See the [worked example](../docs/ACCEPTANCE_CRITERIA.md).

Covered requires a mechanism and observable result, not just an ID mention.
Record the reason and agreement source for deferred scope; a proposed deferral
remains unresolved. Distinguish verified current behavior from proposed design
and assumptions. Check named interfaces, defaults, and paths at their sources.

### High-Level Design

Overview of the approach and key components:
- What are the main building blocks?
- How do they fit together?
- What's the data flow?

### Architecture

System architecture and component interactions:

```text
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Component  │─────▶│  Component  │─────▶│  Component  │
│      A      │      │      B      │      │      C      │
└─────────────┘      └─────────────┘      └─────────────┘
```

Explain the diagram and key architectural decisions.

### API Design

Proposed API or interface specifications:

```proto
// Example: gRPC service definition
service ExampleService {
  rpc GetResource(GetResourceRequest) returns (GetResourceResponse);
  rpc CreateResource(CreateResourceRequest) returns (CreateResourceResponse);
}

message GetResourceRequest {
  string resource_id = 1;
}

message GetResourceResponse {
  Resource resource = 1;
}
```

Or for REST APIs:

```text
GET    /api/v1/resources/{id}
POST   /api/v1/resources
PUT    /api/v1/resources/{id}
DELETE /api/v1/resources/{id}
```

Include request/response examples and error handling.

### Data Model

Data structures, schemas, and persistence:

```sql
-- Example: Database schema
CREATE TABLE resources (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  INDEX idx_status (status)
);
```

Explain key fields, relationships, and indexing strategy.

### Implementation Details

Key technical specifics:

- **Technology Stack**: Languages, frameworks, libraries
- **Dependencies**: External services, third-party components
- **Configuration**: Environment variables, feature flags
- **Error Handling**: How failures are managed
- **Logging/Monitoring**: What gets logged and tracked

## Alternatives Considered

### Alternative 1: [Approach Name]

Description of this alternative approach and its key characteristics.

**Pros:**
- Benefit 1
- Benefit 2

**Cons:**
- Limitation 1
- Limitation 2

**Why not chosen**: Specific technical or business reason (e.g., "Higher complexity for minimal gain", "Doesn't scale to our requirements")

### Alternative 2: [Approach Name]

Description of this alternative approach and its key characteristics.

**Pros:**
- Benefit 1
- Benefit 2

**Cons:**
- Limitation 1
- Limitation 2

**Why not chosen**: Specific technical or business reason

### Do Nothing

What happens if we don't implement this?

- Impact on users
- Technical debt implications
- Opportunity cost

## Trade-offs and Implications

### Technical Trade-offs

- **Trade-off 1**: Description (e.g., "Increased complexity for better performance")
  - **Mitigation**: How we'll manage this
- **Trade-off 2**: Description
  - **Mitigation**: How we'll manage this

### Operational Impact

- Changes to deployment processes
- New monitoring requirements
- On-call impact
- Documentation needs

## Security Considerations

Security implications and how they are addressed:

- **Authentication/Authorization**: How is access controlled?
- **Data Protection**: Encryption, PII handling, compliance
- **Attack Vectors**: What threats are we protecting against?
- **Audit/Compliance**: Logging and audit trail requirements

## Performance and Scalability

Expected performance characteristics:

- **Latency**: Target response times (p50, p95, p99)
- **Throughput**: Requests per second capacity
- **Resource Usage**: CPU, memory, storage requirements
- **Scalability**: Horizontal/vertical scaling approach
- **Bottlenecks**: Known limitations and mitigation

## Testing Strategy

### Technical Acceptance Criteria

For each source criterion, define the technical contract and its rationale:
responses, payloads, errors, persistence, compatibility, and recovery as relevant.
Label new technical decisions as proposed until agreed.

**Technical contract for AC-1**
- Source: [requirement or agreed decision]
- Given [state], when [action], then [observable technical result].
- On failure: [response, allowed side effects, preserved state, recovery].
- Verification: [test level and evidence that establishes this contract].

Describe necessary guarantees, not incidental helper names or file layouts.
Internal constraints may need unit or integration tests rather than API-level
acceptance tests. For quantitative targets, specify metric/percentile, workload,
dataset, environment, measurement period, and the source of the target.

### Verification Plan

How will each acceptance criterion be tested? Link criteria to tests or planned
evidence and explain which incorrect behavior each check detects. Planned
coverage is not a passing result. Keep execution results with tests or release
records instead of maintaining stale results in this RFC.

Separate feature acceptance from shared Definition of Done checks such as lint
and peer review. The [planning and test example](../docs/PLANNING_AND_VERIFICATION.md)
shows how to map criteria to reviewable steps and evidence without another
mandatory document or fixed scenario count.

### Unit Tests

- Component-level test coverage
- Mock external dependencies

### Integration Tests

- End-to-end scenarios
- External service integration

### Performance Tests

- Load testing approach
- Stress testing scenarios
- Benchmark targets

### Test Scenarios

1. **Happy Path**: Normal operation flow
2. **Error Cases**: Failure modes and recovery
3. **Edge Cases**: Boundary conditions
4. **Scale Tests**: High load behavior

Select scenarios based on the change's risks: invalid input, empty results,
partial completion, retries, concurrency, and compatibility where applicable.
Specify what must remain unchanged on failure; “returns an error” alone does
not establish that persistent state is safe. Omit irrelevant scenarios.

## Migration and Rollout Plan

How will this be deployed?

### Migration Steps

1. **Phase 1**: Preparation (database migrations, config changes)
2. **Phase 2**: Gradual rollout (canary, staged deployment)
3. **Phase 3**: Full deployment and cleanup

### Rollback Strategy

- How to revert if issues arise
- Rollback triggers and criteria
- Data migration reversibility

### Feature Flags

- Which flags control the rollout
- Gradual enablement strategy

## Monitoring and Observability

What will we monitor?

- **Metrics**: Key performance indicators
- **Logs**: What gets logged and at what level
- **Traces**: Distributed tracing approach
- **Alerts**: What triggers notifications
- **Dashboards**: Visualization and monitoring tools

## Timeline and Milestones

Estimated implementation timeline:

- **Phase 1**: Design and Prototyping (X weeks)
  - Complete detailed design
  - Build proof of concept
  - Review and iterate

- **Phase 2**: Implementation (X weeks)
  - Core functionality
  - Tests and documentation
  - Security review

- **Phase 3**: Rollout (X weeks)
  - Staged deployment
  - Monitoring and validation
  - Production readiness

**Total**: Estimated X weeks

## Open Questions

Unresolved questions that need discussion:

For each question, name an owner, the affected criterion, whether it blocks
implementation, and the next step or agreed resolution. Do not silently turn an
assumption into a requirement. Resolve “warn or reject” before testing unless
both outcomes intentionally satisfy a stated invariant.

1. **Question 1**: What needs to be decided?
   - Options being considered
   - Decision maker
   - Timeline for resolution

2. **Question 2**: What needs clarification?
   - Context and implications
   - Stakeholders to consult

## Related Documents

- [Related ADR](../adr/adr-XXX) - Decision that led to this RFC
- [Related RFC](../rfcs/rfc-XXX) - Dependency or related work
- [External Documentation](https://example.com) - Reference material
- [Design Doc](https://example.com) - Detailed design specs

## Appendix

### Glossary

Define technical terms or acronyms used in this RFC.

### References

Academic papers, blog posts, or other resources that informed this design.

## Revision History

### Change Impact and Review

For an amendment, identify the changed decision and source baseline, affected
criteria/documents/tests, follow-up owners, and verification state. Preserve
unrelated decisions and completed-work history. An impact proposal does not mean
the downstream artifacts were synchronized.

Use the [review and amendment guide](../docs/REVIEW_GUIDE.md) to distinguish
evidence-backed defects, open questions, and suggestions. State the conditions
that would reverse consequential decisions. Before handoff, ask a reader to
perform a realistic planning or recovery task from the RFC alone, and check
references from the intended shared location.

Optional section to track major changes:

- YYYY-MM-DD: Initial draft (Author Name)
- YYYY-MM-DD: Updated after architecture review (Author Name)
- YYYY-MM-DD: Accepted by tech leads (Reviewers)
- YYYY-MM-DD: Implementation complete (Status: Implemented)
