# YT Signal Scout Architecture

## System Shape

YT Signal Scout is a modular monolith with explicit module boundaries. Application services consume typed domain models rather than vendor-specific response objects, and each downstream stage owns one responsibility.

## Analytics Pipeline

Analytics has two explicit deterministic execution paths. They share canonical source facts and
typed metric results, but they do not share an execution registry.

### Path A — Homogeneous ChannelAnalytics calculators

This implemented path contains calculators with the common
`calculate(ChannelAnalytics) -> MetricResult` contract:

```text
ChannelAnalytics
        |
        v
ChannelAnalytics Calculators
        |
        v
Calculator Registry
(ordered homogeneous execution)
        |
        v
Analytics Assembler
(mapping and structural validation)
        |
        v
CalculatedChannelAnalytics
```

### Path B — Subscriber-relative analytics

The classifier and two calculators are implemented. The orchestration and result-assembly stages
shown below are approved but not implemented:

```text
Canonical Data
        |
        v
EligibleVideoClassifier
        |
        v
EligibleVideoClassification
        |
        v
SubscriberRelativeAnalyticsOrchestrator
(future: owns sequencing and explicit input delivery)
        |
        +-- 1. EligibleStandardVideoCountCalculator(classification)
        |
        +-- 2. MedianStandardVideoVsrCalculator(classification, subscriber_count)
        |
        v
Ordered Subscriber-Relative Metric Results
        |
        v
SubscriberRelativeResultAssembler
(future: owns mapping and structural validation)
```

The two calculators own only their calculations and are independent; their numeric order is
deterministic invocation order, not a data dependency between them. The future
`SubscriberRelativeAnalyticsOrchestrator` will obtain explicit inputs, invoke each calculator once
in the documented order, and return a complete ordered result collection. It will not calculate
metrics, apply eligibility policy, assemble aggregates, or interpret results. The future
`SubscriberRelativeResultAssembler` will own mapping and structural validation. Neither the
existing Calculator Registry nor the existing Analytics Assembler participates in Path B.

The YouTube acquisition layer owns interaction with the external API and conversion from upstream response shapes into immutable canonical models. The canonical models expose only the subset of public YouTube data with expected long-term application value.

## Transport and Domain Boundary

The transport layer owns YouTube-specific response formats and converts them into domain concepts before constructing canonical models. Canonical models intentionally hide upstream transport representations from analytics and every downstream layer.

For example, YouTube's `duration="PT5M30S"` transport value becomes `timedelta(minutes=5, seconds=30)` in the canonical `Video` model. Likewise, `privacyStatus="public"` becomes `PrivacyStatus.PUBLIC`.

This boundary prevents external naming and serialization formats from leaking into deterministic calculators, signals, or narratives.

The analytics layer consumes those canonical models. Shared validation establishes calculator preconditions, and each deterministic calculator produces exactly one typed metric without orchestration, scoring, signal detection, or AI behavior.

Eligible Video Policy v1 establishes an explicit classification boundary for subscriber-relative
analytics. Canonical acquisition owns closed availability, live-state, and format mapping. The
classifier consumes those canonical facts with an explicit evaluation time and produces immutable,
source-ordered standard, Shorts, and livestream-replay bases. Unknown classification is excluded
rather than guessed.

The implemented subscriber-relative facts are explicitly standard-video scoped and use separate
metric identities. `eligible_standard_video_count` records the classified standard-basis size.
`median_standard_video_vsr` uses that basis and a visible positive subscriber count and returns
unavailable for an empty basis or unavailable denominator. Each calculator returns exactly one
typed metric result, and the future Path B result assembler will map each result to one aggregate
field. Neither calculator contains the minimum-five qualification or a signal threshold.
Qualification remains a future typed concern.

The Calculator Registry owns only the homogeneous `ChannelAnalytics` calculator path. It executes
an explicitly injected sequence once in registration order and returns an immutable result tuple.
Duplicate metric identities are rejected during construction. Execution is fail-fast: calculator
exceptions propagate unchanged, no partial result collection is returned, and later calculators
are not executed. It does not register or execute subscriber-relative calculators.

The existing Analytics Assembler consumes Path A metric results, validates their completeness and
uniqueness, and constructs `CalculatedChannelAnalytics`. The registry remains unaware of the
aggregate, and the aggregate remains a pure immutable data contract without mapping or
orchestration behavior. A future subscriber-relative result assembler will provide equivalent
mapping-only ownership for Path B; it is not the existing assembler and is not yet implemented.

Independent signal rules interpret the completed aggregate through explicit, deterministic
business policies. The signal engine owns only ordered orchestration: it snapshots the
injected rule sequence, rejects duplicate rule identities, preserves rule and per-rule output
order, and fails fast without returning partial results. Signals are immutable,
machine-readable interpretations carrying typed metric evidence and rule provenance.

Signal identity and polarity remain separate concepts. Category and severity are deferred until
approved production rules establish a real taxonomy and importance policy. Confidence is also
deferred because the aggregate does not yet contain the cohort, sample-completeness, and
observation inputs needed for a defensible policy. No production rule thresholds are
implemented until product definitions approve them.

Signal policy is governed by the documentation-first Signal Catalog. A production rule must
trace to an approved, implementation-ready catalog entry with matching machine identities,
version, condition, boundaries, evidence, and limitations. Proposed or blocked entries are not
production authorization. The catalog is not loaded at runtime and is not a generic rule DSL.

The AI narrative engine remains a future final consumer and will explain typed evidence rather
than calculate metrics or signals.

## Dependency Direction

Dependencies flow downward through the pipeline. Downstream stages may depend on typed outputs from the stage above, but upstream acquisition and deterministic calculation must not depend on signal or narrative concerns.

Raw API response shapes and Google SDK types must not cross the canonical domain-model boundary.

## Implementation Status

### Implemented Calculators

- ChannelAge
- AverageViews
- MedianViews
- ViewsPerDay
- UploadFrequency
- UploadConsistency
- ViewDistribution
- ViewOutlier
- ViewGrowthRate
- ViewEngagementRate
- EligibleStandardVideoCount
- MedianStandardVideoVsr

### Implemented Eligibility

- Immutable `EligibleVideoClassification` and exclusions
- Deterministic `EligibleVideoClassifier`
- Ordered standard-video, Shorts, and livestream-replay bases

### Implemented Orchestration

- Calculator Registry

### Implemented Analytics Assembly

- Analytics Assembler
- CalculatedChannelAnalytics population

### Implemented Signal Foundation

- Immutable typed signal and evidence contracts
- Independent `SignalRule` protocol
- Deterministic `SignalEngine` orchestration
- Duplicate-rule protection and fail-fast execution

### Planned Pipeline Stages

- Complete canonical availability, live-state, and format acquisition mapping
- Dedicated subscriber-relative analytics orchestration
- Subscriber-relative result assembly and aggregate integration
- Subscriber-relative qualification
- Product-approved signal rules
- AI Narrative Engine

See ADR-002 for analytics-layer separation, ADR-003 for the canonical YouTube domain-model
decision, ADR-006 for signal evaluation semantics, ADR-007 for Signal Catalog governance,
ADR-008 for format-specific eligible-video bases, and ADR-009 for the separate
subscriber-relative orchestration boundary.
