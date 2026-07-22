# ADR-011: Typed Subscriber-Relative Signal Evidence Layer

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision extends ADR-006 and ADR-010 without changing their existing contracts.

---

# 1. Decision Summary

Introduce an immutable, policy-free `SignalEvidenceBundle` built deterministically from one
`SubscriberRelativeAnalysisResult`. The bundle exposes qualification, eligible sample,
subscriber state, requested-ID resolution, and median standard-video VSR as typed facts with
explicit units, availability, and one shared acquisition-provenance context.

The builder performs no signal evaluation, comparison, thresholding, scoring, confidence,
ranking, recommendation, or presentation work.

# 2. Context

ADR-006 established immutable evidence attached to an emitted `Signal` and deliberately kept that
model minimal until real downstream requirements existed. ADR-010 later introduced qualification
and subscriber-relative analytics as one result, including unavailable factual values and typed
acquisition provenance. Future subscriber-relative rules need a safe factual input boundary that
does not receive bare unqualified analytics or recreate qualification facts independently.

# 3. Decision

```text
SubscriberRelativeAnalysisResult
        |
        v
SignalEvidenceBuilder
        |
        v
SignalEvidenceBundle
        |
        v
Future subscriber-relative signal evaluation
```

The complete bundle has fixed evidence slots for qualification, eligible standard-video count,
canonical subscriber state, requested-ID resolution rate, and median standard-video VSR. Every
slot has a closed evidence identity and semantic unit. Metric evidence records `AVAILABLE`
exactly when its value is present and `UNAVAILABLE` exactly when its value is `None`.

All slots reference the same immutable `SignalEvidenceContext`, which contains the existing
`VideoAcquisitionProvenance` object and qualification evaluation timestamp. Population counts are
not copied out of provenance. The bundle validates its fixed identity/unit mapping and shared
context so independently constructed instances cannot mislabel evidence.

# 4. Existing Signal Contracts

The existing `SignalEvidence` remains the evidence attached to an emitted `Signal` under ADR-006.
`SignalEvidenceBundle` is an upstream factual projection and does not replace, broaden, or adapt
that model in this milestone. `SignalRule`, `SignalEngine`, and `Signal` remain unchanged because
no subscriber-relative production rule is approved or implemented.

# 5. Rationale

A fixed typed bundle makes missing values, qualification, and provenance available without a raw
dictionary or speculative generic schema. A shared context keeps provenance consistent and
avoids primitive duplication. Keeping construction separate from rule evaluation preserves the
fact-versus-policy boundary.

# 6. Consequences

The layer gives future rules one deterministic, serializable factual projection and keeps
unqualified or unavailable facts explicit. The pre-rule bundle and emitted-signal evidence remain
distinct models; future rule integration must deliberately map only evidence required by an
approved catalog entry.

# 7. Non-goals

- Production rules or thresholds
- Comparator and operator policy
- Scoring, confidence, ranking, or recommendation
- Signal Engine changes
- Persistence or transport APIs
- AI narratives

# 8. Implementation Impact

Affected folders are `backend/app/services/signals/`, `backend/tests/`, and
`docs/engineering/`. No migration or breaking contract change is required.

# 9. Future Revisit Criteria

Revisit when the first subscriber-relative production rule is approved and its catalog entry
defines the exact rule input, comparator, emitted evidence, and Signal Engine integration.

# 10. Related ADRs

ADR-002, ADR-006, ADR-007, ADR-008, ADR-009, and ADR-010.
