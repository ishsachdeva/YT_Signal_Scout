# ADR-015: Govern Threshold Research Through Immutable Study Artifacts

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision governs research built on ADR-012 through ADR-014.

---

# 1. Decision Summary

Represent each governed threshold study as an immutable, versioned artifact containing its study
definition, optional controlled execution result, explicit lifecycle status, and strictly
timestamp-ordered human review records. Study approval approves only the research artifact; it
cannot publish a threshold, authorize production policy, or activate a signal.

# 2. Context

The repository can import governed observations and execute deterministic threshold studies, but
it has no durable representation for study purpose, lifecycle state, review provenance, or
research approval. Ad hoc documents could blur factual execution output, reviewer judgment, and
production authorization.

# 3. Alternatives Considered

## Mutable workflow service

Rejected because no persistence, authentication, permissions, or workflow behavior is required.
Mutable transitions would add state management without an approved operational use case.

## Add governance fields to execution results

Rejected because execution results are deterministic factual output. Reviewer identity, rationale,
and decisions are separate governance concerns.

## Immutable study snapshots

Selected. A complete artifact represents one valid lifecycle state without mutation or a workflow
engine and retains typed links to the existing execution contracts.

# 4. Study Contract

`BacktestStudyDefinition` gives a study a stable ID, version, purpose, creation time, and existing
execution configuration. `BacktestStudyArtifact` carries an artifact schema version, closed status,
optional `BacktestExecutionResult`, and strictly timestamp-ordered reviews.

The existing complete `ThresholdBacktestReport` inside the execution result is the factual findings
contract. No separate finding model selects, ranks, summarizes, or duplicates candidate outcomes.

# 5. Lifecycle and Validation

The closed states are `draft`, `executed`, `approved`, `rejected`, and `archived`. Draft artifacts
contain no execution or reviews. Executed artifacts contain the matching execution and no reviews.
Approved and rejected artifacts require reviews with strictly increasing timestamps whose final
decision matches the status. Archived artifacts retain an execution and review history.

Review IDs are unique, timestamps are timezone-aware and strictly increasing, and every review
matches the study version and execution identity. These are representation invariants, not mutable
transition behavior.

# 6. Approval Boundary

`approve_study` means reviewers accept the research artifact for research governance purposes.
It does not mean a candidate is recommended, a threshold is approved for production, policy is
published, the Signal Catalog is changed, or SIG-002 may be composed.

# 7. Consequences

Study purpose, execution facts, reviews, and research disposition become serializable and
auditable without adding storage or workflow infrastructure. Callers must create a new artifact
snapshot to represent another lifecycle state. Production approval remains a separate future
product-governance decision.

# 8. Implementation Impact

Adds immutable study models, lifecycle validation, package exports, focused tests, and offline
architecture documentation. It adds no calculation, service, dependency, or production behavior.

# 9. Future Revisit Criteria

Revisit if approved requirements introduce persisted artifact custody, authenticated reviewers,
multi-stage approval, signatures, or an explicit production-policy publication boundary.

# 10. Related ADRs

ADR-006, ADR-007, ADR-011, ADR-012, ADR-013, and ADR-014.
