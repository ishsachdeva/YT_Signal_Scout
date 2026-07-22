# ADR-012: Deterministic Offline Subscriber-Band Threshold Backtesting

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision extends the research path without changing ADR-006, ADR-007, or ADR-011.

---

# 1. Decision Summary

Introduce a dedicated offline `services/backtesting` boundary for deterministic analysis of
historical median standard-video VSR observations across explicitly configured subscriber bands
and threshold candidates. It produces factual reports for external Product and Analytics review
but cannot choose, recommend, approve, or execute signal policy.

# 2. Context

SIG-002 remains blocked on an approved threshold and exact equality boundary. Production
calculators and evidence now expose the necessary facts, but selecting policy from unversioned
scripts or by embedding experiments in `SignalRule` would weaken reproducibility and blur research
with production evaluation.

# 3. Decision

```text
Historical SubscriberRelativeAnalysisResult observations
        |
        v
BacktestDatasetValidator
        |
        v
Versioned SubscriberBandSet + MedianVsrThresholdSet
        |
        v
MedianStandardVideoVsrThresholdBacktester
        |
        v
Immutable ThresholdBacktestReport
        |
        v
External Product / Analytics review
```

The observation contract is a narrow immutable research projection containing a stable identity,
channel identity, timestamp, positive factual subscriber count, and the existing immutable
analysis result. The numeric count is not reconstructed from VSR and is not added to production
qualification or evidence contracts. It must agree with the analysis's available-positive
subscriber state, timestamp, and channel-scoped provenance.

Subscriber bands are versioned, ordered half-open ranges with unique IDs. Overlap is invalid.
Gaps are rejected unless the configuration explicitly enables them; an unmatched otherwise-valid
observation becomes a typed analytical exclusion. Only the final range may be unbounded.

Threshold candidates are versioned, ordered, uniquely identified facts. Because Product has not
approved whether SIG-002 uses `>` or `>=`, both are closed configuration operators and every
candidate records its operator. The backtester evaluates all configured band/candidate pairs and
never selects among them.

# 4. Validation and Exclusion Semantics

Malformed observations, duplicate observation IDs, duplicate channel/timestamp snapshots,
contradictory subscriber state, invalid versions, invalid bands, and invalid candidates fail
structural validation. Valid observations are excluded as result values when the existing
analysis is unqualified, median VSR is unavailable, or no configured band matches. Qualification
failures remain unchanged and are preserved on exclusions and counted in enum order.

# 5. Statistics and Precision

Each band reports count, minimum, maximum, arithmetic mean, and median for threshold-eligible
values. Empty statistics and zero-denominator rates are `None`. Candidate results report eligible,
excluded, hit, non-hit, and unrounded hit rate. Comparisons and calculations use existing binary
floating-point analytics values without pre-rounding. Values are sorted before aggregation so
input observation order cannot alter floating-point summation order.

# 6. Determinism and Ordering

Observations are canonicalized by stable observation ID. Subscriber bands and candidates preserve
their explicit configured order. Exclusions follow canonical observation order. Qualification
failure counts follow the existing enum order. Identical factual inputs and configuration produce
equal serializable reports.

# 7. Production Boundary

The package is not registered in application startup and has no API, CLI, persistence, scheduler,
network, acquisition, signal-emission, ranking, scoring, recommendation, or narrative behavior.
`SignalEngine`, `SignalRule`, `SignalEvidenceBuilder`, and production calculators remain unchanged.

# 8. Consequences

Threshold research becomes reproducible and reviewable without turning research output into
policy. Configuration and reports add explicit domain contracts, while dataset collection,
storage, execution tooling, and Product approval remain external future concerns.

# 9. Implementation Impact

Adds `backend/app/services/backtesting/`, focused tests, architecture documentation, and catalog
capability notes. No migration or breaking production contract change is required.

# 10. Future Revisit Criteria

Revisit when a governed historical dataset is available for an actual study, when reports require
persistence or a controlled execution surface, or after Product and Analytics approve a threshold
and equality boundary for a versioned catalog entry.

# 11. Related ADRs

ADR-002, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010, and ADR-011.
