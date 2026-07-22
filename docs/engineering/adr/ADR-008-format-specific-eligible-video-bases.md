# ADR-008: Establish Explicit Format-Specific Eligible Video Bases for Subscriber-Relative Analytics

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None

---

# 1. Decision Summary

Introduce a future explicit, immutable eligibility-classification boundary between validated
canonical YouTube data and subscriber-relative analytics. Acquisition owns YouTube-specific
availability, live-state, and format mapping. Analytics consumes closed canonical types and
produces separate source-ordered eligible bases for standard videos, Shorts, and livestream
replays under Eligible Video Policy v1.

The first subscriber-relative metrics are explicitly standard-video scoped:
`ELIGIBLE_STANDARD_VIDEO_COUNT` and `MEDIAN_STANDARD_VIDEO_VSR`. Mathematical calculation,
product qualification, SignalRule evaluation, ranking, and narrative remain separate
responsibilities.

# 2. Context

YT Signal Scout must identify channels whose recent videos outperform their visible subscriber
base. Raw supplied videos are not a valid analytical population: videos differ in age, privacy,
availability, format, live state, and statistics completeness. Duplicates can silently weight
results, while mixing Shorts, standard videos, and live replays creates misleading comparisons.

The current canonical model lacks explicit availability, live-state, and format types anticipated
by the TRD. The YouTube Data API exposes public live metadata but no direct authoritative Shorts
flag. Implicit filtering inside a calculator would hide both policy and uncertainty.

Calculation and qualification also answer different questions. A median is mathematically valid
for one or more eligible videos, while product qualification requires at least five and eventually
requires retrieval completeness. Signals must not recreate either concern.

# 3. Problem Statement

How should subscriber-relative analytics obtain one deterministic, explainable, format-specific
video population without duplicating eligibility rules or leaking YouTube transport heuristics
into calculators and signals?

# 4. Decision Drivers

- Correct subscriber-relative metrics
- Explicit product-policy ownership
- Format separation
- Determinism and reproducibility
- Explainability and exclusion traceability
- Canonical/analytics separation
- Compatibility with the existing Calculator Registry
- Minimal abstraction before the first metric

# 5. Goals

- Represent availability, live state, and format as closed canonical concepts.
- Apply Eligible Video Policy v1 through one focused classifier contract.
- Preserve source ordering and normal exclusion reasons.
- Reject invalid datasets rather than silently repairing them.
- Keep subscriber denominator and median calculation factual.
- Keep product qualification and signal interpretation downstream.

# 6. Alternatives Considered

## Option A — Filter independently inside every calculator

### Pros

- No new classification object

### Cons

- Duplicates policy and risks divergent eligible populations
- Hides exclusions and makes future changes difficult to audit

Rejected.

## Option B — Put eligibility inside SignalRules

### Pros

- Rules could own all product conditions

### Cons

- Factual metrics would depend on signals
- Multiple rules could calculate incompatible VSR populations
- Violates ADR-002, ADR-006, and ADR-007

Rejected.

## Option C — Generic runtime-configured eligibility engine

### Pros

- Potentially supports multiple policies

### Cons

- Premature DSL/configuration complexity
- Weakens static typing and introduces validation/security burden
- No current runtime policy-administration requirement

Rejected.

## Option D — Infer all formats inside analytics from duration

### Pros

- Uses an existing field

### Cons

- Duration is not authoritative Shorts identity
- Live replay cannot be inferred safely
- Couples analytics to evolving YouTube-specific behavior

Rejected.

## Option E — Combine all formats into one VSR population

### Pros

- One median and larger samples

### Cons

- Contradicts PRD format separation
- Mixes materially different distribution and view-count behavior
- Makes evidence ambiguous

Rejected.

## Option F — Store eligibility directly on canonical Video

### Pros

- Simple downstream access

### Cons

- Eligibility depends on evaluation time and versioned product policy
- Contaminates source facts with a derived, time-dependent decision

Rejected.

## Option G — Explicit eligibility classification step

### Pros

- One policy owner and observable immutable output
- Preserves canonical facts and calculator purity
- Supports qualification and evidence without repeated filtering

### Cons

- Adds a model and classification step
- Requires coordinated canonical acquisition changes

Selected.

# 7. Decision

Eligible Video Policy v1 in the Signal Catalog is authoritative.

Canonical acquisition/domain construction will add:

- `VideoAvailability`: `AVAILABLE`, `UNAVAILABLE`, `DELETED`, `UNKNOWN`;
- `LiveState`: `NOT_LIVE`, `UPCOMING`, `LIVE`, `COMPLETE`, `UNKNOWN`;
- `VideoFormat`: `SHORT`, `STANDARD`, `LIVE_REPLAY`, `UNKNOWN`.

New canonical fields initially default to `UNKNOWN` for construction compatibility. Acquisition
maps official public response facts into them. Analytics never imports transport types or repeats
YouTube-specific mapping.

Format mapping v1 is conservative because no direct Data API Shorts flag exists. Completed live
content maps to `LIVE_REPLAY`. A resolved non-live video longer than three minutes maps to
`STANDARD`. Non-live videos at or below three minutes remain `UNKNOWN` unless a stronger approved
official public fact becomes available. Duration alone never maps a video to `SHORT`.

A focused classifier consumes validated `ChannelAnalytics` and an explicit timezone-aware
evaluation time. It returns an immutable `EligibleVideoClassification` containing format-specific
tuples, deterministic exclusions, evaluation time, and policy version. Normal empty populations
are valid. Source order is preserved. Future timestamps, naive timestamps, and duplicate video IDs
are validation failures.

Only public, available videos aged inclusively from 24 elapsed hours through 90 elapsed days with
present non-negative views and resolved eligible format enter a basis. Unknown or unsupported
states are excluded rather than guessed.

Two focused calculators use the standard basis and return separate metric results:

- `EligibleStandardVideoCountCalculator` returns `ELIGIBLE_STANDARD_VIDEO_COUNT` as an integer;
- `MedianStandardVideoVsrCalculator` returns `MEDIAN_STANDARD_VIDEO_VSR` as `float | None`, using
  a visible positive subscriber count.

The assembler maps those identities explicitly to `eligible_standard_video_count` and
`median_standard_video_vsr`. Count zero distinguishes an empty standard basis from a positive
eligible count whose median is unavailable because the denominator is unavailable. No
qualification threshold belongs in either calculator.

For the first implementation, each calculator receives the focused classifier through explicit
injection and remains compatible with the existing `AnalyticsCalculator` protocol by consuming
`ChannelAnalytics` and returning exactly one `MetricResult`. The classifier output remains
independently callable and testable. Repeating a bounded deterministic classification in these two
calculators is preferable to speculative generalized orchestration. A shared typed orchestration
context may be proposed only if measured cost or additional consumers justify a new boundary.
Eligibility classification is deterministic, side-effect free, bounded by the supplied video
collection, and intentionally repeated until measured performance justifies shared orchestration.

Retrieval completeness and minimum-five qualification remain a future typed qualification concern.
Signals consume approved qualification state when available and never recreate eligibility or
qualification rules.

# 8. Decision Rationale

An explicit classifier is the smallest boundary that makes a versioned, time-dependent product
policy observable without contaminating canonical data or individual calculations. Closed
canonical types isolate upstream semantics. Format-specific tuples prevent accidental mixing, and
conservative unknown handling favors correctness over fabricated coverage.

Explicit standard-video metric naming avoids misleading generic fields and future compatibility
aliases. Separate count and median identities preserve ADR-005 and the current calculator
protocol: one calculator result maps to one aggregate field. This limits the next implementation's
blast radius while leaving a measured revisit point for shared orchestration.

# 9. Related Engineering Principles

- EP-001 Build for Maintainability Before Optimization
- EP-002 Separation of Concerns
- EP-003 Single Responsibility Principle
- EP-004 Deterministic Business Logic
- EP-005 Dependency Injection
- EP-006 Immutable Models

# 10. Consequences

## Positive

- Every subscriber-relative calculator uses the same approved classifier contract.
- Eligibility and exclusions become testable and explainable.
- Format mixing and duplicate weighting are prevented.
- YouTube-specific heuristics remain at acquisition.
- Metric calculability, qualification, and signals remain distinct.
- Explicit time input guarantees reproducibility.

## Negative

- Canonical models and acquisition mapping must expand.
- Conservative format mapping excludes many short or ambiguous non-live videos.
- The next milestone must coordinate model, service, validation, calculator, assembler, and tests.
- Detailed exclusions add a small immutable contract.

## Risks

- Public metadata may not reliably identify Shorts, reducing standard-cohort recall.
- YouTube may change Shorts eligibility and view-count semantics.
- Rounded subscriber counts limit ratio precision.
- Small format-specific populations may fail qualification.
- Retrieval completeness remains blocked by an unavailable expected-population denominator.

# 11. Implementation Impact

### Affected folders

- `backend/app/services/youtube/`
- `backend/app/services/analytics/`
- `backend/tests/`
- `docs/`

### Affected modules

- Canonical `Video` and acquisition mapping
- Shared analytics validation
- New eligibility models/classifier
- New `EligibleStandardVideoCountCalculator`
- New `MedianStandardVideoVsrCalculator`
- `MetricType`, `CalculatedChannelAnalytics`, and `AnalyticsAssembler`
- Production calculator composition tests

### Migration required?

No persisted data migration exists today. Existing direct `Video` construction remains compatible
through `UNKNOWN` defaults, but such instances are not eligible until tests/callers provide resolved
canonical states.

### Breaking changes?

The aggregate gains required metric structure, so all direct constructors and assembler fixtures
must change together. Existing calculator and registry contracts remain unchanged.

# 12. Security Impact

Only official public metadata is involved. No credentials, private analytics, dynamic execution,
or external policy configuration is introduced. Unknown and hidden values are not estimated.

# 13. Performance Impact

Classification and both calculations are linear in the bounded video collection, plus median
sorting. No network access occurs in analytics. Reclassification by the two initial calculators is
acceptable; measured cost or additional consumers trigger revisit.

# 14. Cost Impact

No immediate infrastructure cost. Acquisition may request existing official video parts needed for
live-state mapping; quota impact must be reviewed during implementation.

# 15. Operational Impact

Format classifier policy versions must be observable in diagnostics and future evidence. Unknown
classification rates should be monitored after implementation. Retrieval completeness remains
separate and unavailable until acquisition exposes its denominator.

# 16. Future Revisit Criteria

Revisit when:

- official public metadata provides authoritative Shorts identity;
- measured repeated-classification cost or additional consumers justify shared precomputation;
- retrieval-completeness inputs become available;
- Shorts or replay median metrics are approved;
- persisted canonical snapshots require migration/version compatibility;
- eligibility policy boundaries change.

# 17. References

- Product Requirements Document §§5, 8, and 9
- Technical Requirements Document canonical video and analytics sections
- Feature Catalogue E04-F02 and E04-F03
- Signal Catalog v1.1, Eligible Video Policy v1
- YouTube Data API video resource documentation
- YouTube Help: three-minute Shorts eligibility
- ADR-002, ADR-003, ADR-005, ADR-006, and ADR-007
