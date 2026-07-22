# ADR-017: Record Human Threshold Evaluation as an Immutable Bound Artifact

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision extends ADR-015 and ADR-016 without changing their approval boundaries.

---

# 1. Decision Summary

Represent one human evaluation as an immutable, versioned artifact that embeds one executed study
artifact and one evaluation methodology, identifies the reviewer and evaluation timestamp, records
ordered qualitative observations for every criterion, and uses the existing research-only
recommendation enum.

# 2. Context

ADR-016 defines what reviewers inspect but deliberately does not represent a completed evaluation.
ADR-015 records study lifecycle reviews but does not bind criterion-level human observations to a
specific methodology. Free-form evaluation notes would lose methodology, criterion, ordering, and
study provenance.

# 3. Alternatives Considered

## Add observations to BacktestStudyReview

Rejected because lifecycle review decisions and methodology-based factual observations have
different responsibilities. Existing review contracts must remain stable.

## Store only study and methodology references

Rejected because no persistence or registry exists to resolve references, and future values could
silently diverge. Embedding immutable values makes the evaluation self-contained and serializable.

## Immutable bound evaluation artifact

Selected. It preserves complete study and methodology identity without introducing services,
calculations, or mutable workflow behavior.

# 4. Evaluation Contract

`BacktestStudyEvaluation` contains a stable ID, version, timezone-aware timestamp, reviewer, one
`BacktestStudyArtifact` containing an execution, one `ThresholdEvaluationMethodology`, ordered
`CriterionObservation` values, and one existing `ResearchRecommendation`.

Each observation identifies the criterion and its existing factual metric, records reviewed, not
reviewed, or needs clarification, and may contain bounded human notes. Observation identity/metric
pairs must exactly match all methodology criteria in supplied order. This rejects omission,
duplication, reordering, and metric substitution without sorting input.

A required methodology criterion cannot be marked not reviewed. It may be reviewed or marked as
needs clarification. Optional criteria may be marked not reviewed, preserving an explicit human
observation without pretending that review occurred.

# 5. Binding and Time

Draft studies cannot be evaluated because they have no execution facts. Evaluation time cannot
precede execution. The recommendation must appear in the embedded methodology's permitted values.
Embedding the study and methodology preserves their complete immutable identity and versions.

# 6. Boundary

The artifact records human observations only. It performs no automatic evaluation, calculation,
scoring, weighting, percentage derivation, ranking, optimization, threshold selection, study
approval, production-policy publication, or signal activation. Reviewer strings establish no
authentication or authorization.

# 7. Consequences

Human evaluations become deterministic, serializable, and traceable to exact study facts and
methodology criteria. Artifact size includes the embedded immutable study and methodology, which
is acceptable without a persistence or reference-resolution boundary.

# 8. Implementation Impact

Adds immutable evaluation contracts, package exports, focused tests, and offline research
documentation. No service, dependency, execution, study lifecycle, or production behavior changes.

# 9. Future Revisit Criteria

Revisit if governed persistence provides immutable content-addressed references, authenticated
reviewer identity is approved, or a separate human evaluation recording service is required.

# 10. Related ADRs

ADR-006, ADR-007, ADR-012, ADR-014, ADR-015, and ADR-016.
