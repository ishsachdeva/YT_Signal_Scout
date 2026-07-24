# ADR-016: Define Versioned Factual Threshold Evaluation Methodology

**Status:** Accepted — recommendation vocabulary amended by ADR-021

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision extends the research governance established by ADR-012 through ADR-015.

ADR-021 later renamed two research recommendations without changing this ADR's factual methodology
or production-authority boundary.

---

# 1. Decision Summary

Represent threshold evaluation methodology as an immutable, explicitly versioned, ordered set of
criteria limited to factual concepts already available in `ThresholdBacktestReport`, together with
a closed set of research-only recommendations. Methodology defines what humans inspect; it does
not evaluate, score, rank, recommend, or approve a threshold.

# 2. Context

Backtest reports provide reproducible facts and study artifacts provide lifecycle governance, but
the repository does not yet define which report concepts a governed evaluation must inspect.
Leaving methodology implicit would make reviews inconsistent and could allow unsupported measures
or production decisions to enter research artifacts.

# 3. Alternatives Considered

## Free-form methodology documents

Rejected because identifiers, versions, supported evidence, and recommendation boundaries would
not be machine-validatable.

## Weighted criteria and calculated summaries

Rejected because weights imply scoring and aggregation policy. No approved ranking, optimization,
or threshold-selection method exists.

## Closed factual criteria

Selected. Typed metrics map directly to existing report facts, while descriptions state what human
reviewers inspect without introducing calculations.

# 4. Methodology Contract

`ThresholdEvaluationMethodology` carries a stable identity, version, name, objective, ordered
criteria, and permitted recommendations. Criterion and metric identities are unique. Each
`ThresholdEvaluationCriterion` identifies one closed `ThresholdEvaluationMetric`, supplies a
bounded description, and records whether review requires that criterion.

Supported metrics are qualification coverage, median-VSR availability, threshold-eligible support,
median-VSR distribution, candidate hit rate, exclusion profile, and qualification-failure profile.
Precision, false-positive/negative rates, confidence intervals, and stability are excluded because
the current report does not contain the labelled or repeated-run facts needed to support them.

# 5. Recommendation Boundary

The closed research dispositions are further investigation, insufficient evidence, candidate
worth reviewing, and ready for human review. None means production approved, publish threshold,
enable signal, deploy, or release. Methodology records permitted vocabulary only; it does not emit
a recommendation or modify study status.

# 6. Determinism and Validation

All contracts are frozen and serializable. Supplied criterion and recommendation order is
preserved. Duplicate criterion IDs, metrics, and recommendation values are rejected. Equal inputs
produce equal methodology values without clocks, external state, or calculations.

# 7. Consequences

Research teams gain an explicit review contract without adding a scoring engine or duplicating
report data. Supporting a genuinely new metric requires first establishing the factual source and
then versioning the methodology contract. Production policy remains a separate decision.

# 8. Implementation Impact

Adds immutable methodology contracts, package exports, focused tests, and offline research
documentation. No service, calculator, dependency, production composition, or study execution
behavior changes.

# 9. Future Revisit Criteria

Revisit when governed labelled outcomes support classification measures, repeated cohorts support
stability analysis, or Product and Analytics explicitly approve a separate evaluation operation.

# 10. Related ADRs

ADR-006, ADR-007, ADR-011, ADR-012, ADR-013, ADR-014, and ADR-015.
