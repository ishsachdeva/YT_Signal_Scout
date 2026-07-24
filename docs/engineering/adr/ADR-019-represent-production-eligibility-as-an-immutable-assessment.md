# ADR-019: Represent Production Eligibility as an Immutable Assessment

**Status:** Superseded in part by ADR-021

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision implements the assessment boundary anticipated by ADR-018.

ADR-021 preserves the immutable assessment shape but supersedes the forced-unsatisfied manual
approval rule and the resulting requirement that every assessment remain ineligible. The text
below is retained as the historical decision.

---

# 1. Decision Summary

Represent the factual outcome of assessing one study against one promotion policy as an immutable,
versioned `ProductionEligibilityAssessment`. It embeds the policy, study, governed evaluations,
ordered per-requirement results, failed requirement identities, timestamp, and consistent eligible
or ineligible outcome. It provides no production approval or publication behavior.

# 2. Context

ADR-018 defines the complete prerequisites for promotion but deliberately contains no eligibility
result. A separate assessment boundary is required to retain which exact immutable policy, study,
evaluations, and requirement outcomes produced an eligibility fact without mutating those inputs or
conflating eligibility with approval.

# 3. Alternatives Considered

## Add eligibility fields to ProductionPromotionPolicy

Rejected because policy defines prerequisites and must not contain invocation-specific outcomes.

## Compute and publish promotion in one service

Rejected because approval, publication, registry, and runtime behavior remain explicit non-goals.

## Immutable assessment snapshot

Selected. It separates outcome representation from policy and future execution or approval
services while retaining complete factual provenance.

# 4. Assessment Contract

The assessment has a stable ID, positive version, timezone-aware timestamp, one complete
`ProductionPromotionPolicy`, one executed `BacktestStudyArtifact`, zero or more unique
`BacktestStudyEvaluation` values bound to that exact study, ordered requirement results, an
eligibility boolean, and ordered failed requirement IDs.

Each `EligibilityRequirementResult` records the policy requirement ID and kind, satisfaction, and
a human-readable failure reason only when unsatisfied. Results must exactly match every policy
requirement in policy order. They are not sorted or inferred by the model.

# 5. Consistency

Failed requirement IDs must exactly equal unsatisfied result IDs in result order. Eligibility is
true exactly when that tuple is empty. Evaluation IDs are unique, evaluations embed the assessed
study, and assessment time cannot precede the study execution or any included evaluation.

# 6. Boundary

The assessment validates a supplied factual outcome. It does not calculate requirement
satisfaction, create manual approval, publish a threshold, write a registry, perform runtime lookup,
activate a signal, mutate study/evaluation/policy artifacts, or unblock SIG-002. Eligibility is not
production approval.

The mandatory manual-approval requirement cannot be marked satisfied until a separate governed
approval artifact exists. In the current architecture its result remains unsatisfied, its ID is
present in `failed_requirement_ids`, and every valid assessment is ineligible.

# 7. Consequences

Eligibility becomes serializable and auditable with exact policy and research provenance. Because
no assessment service is introduced, callers remain responsible for supplying requirement facts;
the model guarantees their structural completeness and internal consistency only.

# 8. Implementation Impact

Adds immutable assessment contracts, package exports, focused tests, and architecture
documentation. No dependency, service, API, database, CLI, registry, or runtime behavior changes.

# 9. Future Revisit Criteria

Revisit only when an explicitly approved deterministic assessment service or separate manual
production-approval artifact is authorized. Publication remains another decision.

# 10. Related ADRs

ADR-006, ADR-007, ADR-015, ADR-016, ADR-017, and ADR-018.
