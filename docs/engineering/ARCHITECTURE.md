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

The complete subscriber-relative analytics path is implemented and production-composed:

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
(owns sequencing and explicit input delivery)
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
(owns mapping and structural validation)
        |
        v
SubscriberRelativeAnalytics
(immutable typed aggregate)
```

The two calculators own only their calculations and are independent; their numeric order is
deterministic invocation order, not a data dependency between them. The
`SubscriberRelativeAnalyticsOrchestrator` obtains explicit inputs, invokes each calculator once
in the documented order, and returns a complete ordered result collection. It does not calculate
metrics, apply eligibility policy, assemble aggregates, or interpret results. The
`SubscriberRelativeResultAssembler` owns mapping and structural validation. Neither the
existing Calculator Registry nor the existing Analytics Assembler participates in Path B.

`SubscriberRelativeAnalyticsService` is the public application entry point. It invokes the
classifier, orchestrator, and result assembler once each, propagates failures unchanged, and
returns the completed aggregate without exposing pipeline internals. The application composition
root constructs and registers the service with explicitly injected dependencies.

### Subscriber-Relative Qualification and Evidence

ADR-010 and ADR-011 define the implemented Path B result and typed evidence boundary:

```text
VideoAcquisitionResult + canonical Channel
        |
        v
Unique Canonical ChannelAnalytics
        |
        v
EligibleVideoClassifier
(individual-video policy; executes once)
        |
        v
EligibleVideoClassification
        |
        +-------------------------------+
        |                               |
        v                               v
SubscriberRelativeQualification   Subscriber-Relative Calculators
(dataset usability)               (factual analytics always run)
        |                               |
        +---------------+---------------+
                        v
SubscriberRelativeAnalysisResult
(qualification + SubscriberRelativeAnalytics)
                        |
                        v
SignalEvidenceBuilder
(policy-free factual projection)
                        |
                        v
SignalEvidenceBundle
(qualification + typed metric evidence + shared provenance context)
                        |
                        v
Future qualified business signal evaluation
```

Acquisition owns an immutable `VideoAcquisitionResult` containing discovery-position
videos, unique canonical videos, and typed provenance. Provenance distinguishes discovery request
capacity, discovered positions and unique IDs, unique enrichment requests, unique enriched
resources, reconstructed output positions, omissions, and pagination state. Upstream
`totalResults` remains informational and is never treated as an expected-population denominator.

Search provenance is query-scoped and may span channels, so it cannot qualify one channel.
Subscriber-relative qualification accepts only uploads-playlist provenance scoped to the same
canonical channel. Search may discover a candidate channel, but that channel's uploads acquisition
must run before qualification.

Qualification owns dataset-level usability only. It consumes the one eligibility classification,
canonical subscriber state, acquisition provenance, and evaluation time. It applies complete
pagination, an inclusive 60% requested-ID resolution threshold, a visible positive subscriber
count, and at least five eligible standard videos. It does not repeat age, privacy, availability,
format, live-state, publication, or view-count rules owned by the classifier.

The requested-ID resolution rate is unique canonical resources resolved divided by unique IDs
submitted to `videos.list`. It measures enrichment response quality, not full-channel retrieval,
pagination coverage, canonical eligibility yield, or expected-population coverage. Pagination is
a separate closed `COMPLETE` or `TRUNCATED` fact.

Factual subscriber-relative calculators continue to run for unqualified datasets. The
`SubscriberRelativeAnalysisResult` returns qualification and analytics together; downstream
signal-facing orchestration must not pass bare unqualified analytics to business rules.

`SignalEvidenceBuilder` deterministically projects that result into a complete immutable
`SignalEvidenceBundle`. The bundle exposes qualification, eligible sample count, subscriber
state, requested-ID resolution rate, and median standard-video VSR with closed identities,
semantic units, and explicit availability. All evidence references one shared context containing
the existing acquisition provenance and evaluation timestamp. It contains no signal identity,
threshold, comparison, score, ranking, recommendation, or narrative. The existing emitted-signal
`SignalEvidence`, `SignalRule`, and `SignalEngine` contracts remain unchanged until an approved
production rule defines their subscriber-relative integration.

### Offline Subscriber-Band Threshold Research

ADR-012 defines a separate offline research path. It is not part of application startup or
production signal evaluation:

```text
Versioned Historical Backtest Dataset
        |
        v
BacktestDatasetValidator
        |
        v
Versioned Subscriber Bands + Median-VSR Threshold Candidates
        |
        v
MedianStandardVideoVsrThresholdBacktester
        |
        v
ThresholdBacktestReport
        |
        v
External Product / Analytics Review
```

Historical observations carry a positive factual subscriber count beside the immutable
`SubscriberRelativeAnalysisResult`; the count is not reconstructed from VSR or added to
production qualification/evidence contracts. Bands and candidates are explicit ordered,
versioned research configuration. Structural invalidity fails fast, while unqualified analysis,
unavailable median VSR, and unmatched bands remain typed exclusions. Reports contain factual
coverage, distributions, and results for every configured band/candidate pair. They never select
or recommend a threshold, emit a signal, or change catalog approval.

The backtesting package has no acquisition, persistence, API, scheduler, AI, or production
composition dependency. `SignalEngine` remains production rule orchestration only.

ADR-013 governs external historical input before that research path. A strict versioned JSON
document enters only through `HistoricalDatasetImporter`, which validates a schema manifest and
existing immutable `SubscriberRelativeBacktestObservation` records. It rejects unknown fields,
coercive primitive substitutions, inconsistent nested analysis, and duplicate identities, then
sorts observations by stable ID and returns `HistoricalDatasetImportResult` with the canonical
`SubscriberRelativeBacktestDataset`.

```text
Versioned Historical Dataset JSON
        |
        v
HistoricalDatasetImporter
(strict schema/domain validation; no partial import)
        |
        v
HistoricalDatasetImportResult
        |
        v
SubscriberRelativeBacktestDataset
        |
        v
Future controlled offline execution
```

Import validates structure and consistency but cannot prove factual custody. It does not invoke
YouTube, analytics, qualification, evidence, signals, or the backtester, and is not registered in
production composition. Schema version 1 is documented in
[`HISTORICAL_DATASET_FORMAT.md`](HISTORICAL_DATASET_FORMAT.md).

ADR-014 defines the controlled execution boundary that follows successful import:

```text
HistoricalDatasetImportResult + Versioned Study Configuration
        |
        v
BacktestExecutionService
(validates binding; owns synchronous sequencing)
        |
        v
MedianStandardVideoVsrThresholdBacktester
(owns factual calculations)
        |
        v
BacktestExecutionResult
(immutable factual metadata + ThresholdBacktestReport)
```

The execution service requires an explicit execution identity and timezone-aware execution time,
so equal requests produce equal results without reading a runtime clock. Study configuration binds
the imported dataset identity/version to the existing ordered band and threshold sets. The service
does not choose thresholds, interpret results, approve policy, or enter production composition.

ADR-015 governs immutable threshold-study artifacts around this execution boundary:

```text
Versioned BacktestStudyDefinition
        |
        v
BacktestExecutionResult
(complete factual findings)
        |
        v
Typed BacktestStudyReview records
        |
        v
Immutable BacktestStudyArtifact
(draft / executed / approved / rejected / archived)
```

Each artifact is a complete lifecycle snapshot rather than a mutable workflow entity. The existing
`ThresholdBacktestReport` is the findings contract; governance does not copy selected candidate
results into a new ranking model. Reviews identify the reviewer, decision, rationale, and time.
Approval applies only to the research artifact and cannot publish policy or authorize production
signal composition.

ADR-016 defines evaluation methodology separately from both execution facts and study reviews.
`ThresholdEvaluationMethodology` is an immutable, versioned, ordered collection of criteria whose
metrics map only to facts already present in `ThresholdBacktestReport`: qualification coverage,
median-VSR availability, threshold-eligible support, median-VSR distribution, candidate hit rate,
exclusions, and qualification-failure counts. It performs no evaluation and contains no weights,
scores, ranking, optimization, or calculated summary.

The methodology also closes research recommendations to further investigation, insufficient
evidence, candidate worth reviewing, and readiness for human review. These dispositions have no
production authority and cannot publish a threshold, approve policy, or activate SIG-002.

ADR-017 defines the immutable human evaluation artifact that binds one executed
`BacktestStudyArtifact` to one `ThresholdEvaluationMethodology`. It records reviewer identity, an
explicit timestamp, one ordered qualitative observation for every methodology criterion, and one
methodology-permitted `ResearchRecommendation`. Criterion identity and metric pairs must exactly
match methodology order; observations are never sorted or calculated.

Observation states are limited to reviewed, not reviewed, and needs clarification. Notes are human
text and the metric enum is the evidence reference back to the existing report concept. Required
criteria cannot be marked not reviewed; needs clarification remains a valid human observation.
Optional criteria may be marked not reviewed. The artifact has no score, weight, percentage,
ranking, threshold selection, study approval, or production authority.

ADR-018 defines a declarative production-promotion policy after human evaluation. The versioned
`ProductionPromotionPolicy` contains a unique ordered set of typed prerequisites: an approved
research study, exact methodology identity/version, positive minimum evaluation count, qualitative
criterion completion, permitted existing research recommendations, and mandatory separate manual
approval.
Every valid policy contains exactly one requirement of each supported kind. Requirement order is
explicitly supplied and preserved; policy validation neither sorts requirements nor inserts
defaults.

This policy states only what future eligibility assessment must require. It has no threshold value,
eligibility result, promotion decision, evaluator, publisher, registry, runtime lookup, or signal
integration. Research approval and recommendation remain necessary governance inputs rather than
production authorization.

ADR-019 defines immutable production-eligibility assessment after declarative promotion policy.
`ProductionEligibilityAssessment` embeds one policy, one executed study, zero or more unique human
evaluations bound to that exact study, and one ordered `EligibilityRequirementResult` for every
policy requirement. Requirement result identity and kind must exactly match policy order.

Failed requirement IDs preserve result order, and `eligible` is structurally valid only when every
requirement result is satisfied. The assessment records an outcome but does not infer requirement
satisfaction, perform manual approval, publish a threshold, modify inputs, or affect runtime state.
Because no governed manual production-approval artifact exists, the manual-approval requirement
cannot be satisfied: its result remains failed and every current assessment remains ineligible.

The YouTube acquisition layer owns interaction with the external API and conversion from upstream response shapes into immutable canonical models. The canonical models expose only the subset of public YouTube data with expected long-term application value.

## Transport and Domain Boundary

The transport layer owns YouTube-specific response formats and converts them into domain concepts before constructing canonical models. Canonical models intentionally hide upstream transport representations from analytics and every downstream layer.

For example, YouTube's `duration="PT5M30S"` transport value becomes `timedelta(minutes=5, seconds=30)` in the canonical `Video` model. Likewise, `privacyStatus="public"` becomes `PrivacyStatus.PUBLIC`.

This boundary prevents external naming and serialization formats from leaking into deterministic calculators, signals, or narratives.

### Canonical Video Acquisition

`search.list` and `playlistItems.list` discover candidate video IDs; their payloads do not provide
all canonical eligibility facts. `YouTubeService` stably deduplicates those IDs and requests
complete `videos.list` resources with `snippet`, `statistics`, `contentDetails`, `status`, and
`liveStreamingDetails`. The same complete-resource parser is used by search, uploads acquisition,
and direct `get_video()` retrieval.

```text
search.list / playlistItems.list
                |
                v
discovered video IDs (source ordered)
                |
                v
stable request deduplication
                |
                v
videos.list complete resources
                |
                v
canonical Video parsing
                |
                v
source-order reconstruction
```

Each unique discovered ID is requested once per acquisition and each returned unique resource is
parsed once. Duplicate discovery positions remain in the output and may reuse the same immutable
canonical `Video`. Reconstruction follows the original ID sequence rather than upstream response
order. If `videos.list` omits an ID, acquisition skips that position, preserves the relative order
of remaining resources, creates no placeholder, and does not infer deletion from omission alone.

Canonical parsing maps duration, privacy, availability, live state, tags, category ID, default
language, likes, and comments from official resource fields. Completed livestreams map to
`LIVE_REPLAY`; resolved non-live videos with duration strictly greater than three minutes map to
`STANDARD`; every other unresolved format remains `UNKNOWN`. Acquisition never infers `SHORT`.

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
typed metric result, and the Path B result assembler maps each result to one aggregate
field. Neither calculator contains the minimum-five qualification or a signal threshold.
Qualification policy and contracts are implemented under ADR-010.

The Calculator Registry owns only the homogeneous `ChannelAnalytics` calculator path. It executes
an explicitly injected sequence once in registration order and returns an immutable result tuple.
Duplicate metric identities are rejected during construction. Execution is fail-fast: calculator
exceptions propagate unchanged, no partial result collection is returned, and later calculators
are not executed. It does not register or execute subscriber-relative calculators.

The existing Analytics Assembler consumes Path A metric results, validates their completeness and
uniqueness, and constructs `CalculatedChannelAnalytics`. The registry remains unaware of the
aggregate, and the aggregate remains a pure immutable data contract without mapping or
orchestration behavior. The subscriber-relative result assembler provides equivalent mapping-only
ownership for Path B; it is not the existing assembler.

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
- `SubscriberRelativeAnalyticsOrchestrator`
- `SubscriberRelativeAnalyticsService`
- Production subscriber-relative dependency composition

### Implemented Analytics Assembly

- Analytics Assembler
- CalculatedChannelAnalytics population
- `SubscriberRelativeResultAssembler`
- Immutable `SubscriberRelativeAnalytics` population

### Implemented Signal Foundation

- Immutable typed signal and evidence contracts
- Independent `SignalRule` protocol
- Deterministic `SignalEngine` orchestration
- Duplicate-rule protection and fail-fast execution

### Planned Pipeline Stages

- Acquisition provenance and subscriber-relative qualification implementation under ADR-010
- Product-approved signal rules
- AI Narrative Engine

See ADR-002 for analytics-layer separation, ADR-003 for the canonical YouTube domain-model
decision, ADR-006 for signal evaluation semantics, ADR-007 for Signal Catalog governance,
ADR-008 for format-specific eligible-video bases, and ADR-009 for the separate
subscriber-relative orchestration boundary.
