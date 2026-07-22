# YT Signal Scout — Signal Catalog v1

**Catalog version:** 1.4
**Status:** Active — No production signals approved  
**Date:** 2026-07-22  
**Owners:** Product and Analytics  
**Architecture authority:** ADR-006, ADR-007, ADR-010, ADR-011, and ADR-012

## 1. Purpose

This catalog is the authoritative business specification for deterministic YT Signal Scout
signals. Analytics establish facts; this catalog decides which facts matter to the product;
approved `SignalRule` implementations encode those decisions exactly.

Catalog inclusion does not imply approval. Only an entry whose status is **Approved** and whose
implementation readiness is **Implementable Now** may become a production rule.

The catalog is documentation-first. There is no current consumer for YAML, JSON, Python
configuration, or a rule DSL. Executable policy would duplicate application code and introduce
configuration validation and deployment complexity before the first rule exists.

## 2. Architectural boundary

```text
Analytics                     factual, typed measurements
    |
    v
Signal Catalog                approved product meaning and policy
    |
    v
SignalRule                    exact deterministic implementation
    |
    v
Signal Engine                 ordered execution only
    |
    +--> Ranking              future prioritisation
    |
    +--> AI Narrative         future explanation of existing signals
```

- Calculators must not assign business meaning.
- Rules must trace to one approved catalog ID and must not invent policy.
- The engine must not contain thresholds or interpretation.
- Ranking must not determine whether a signal exists.
- AI may explain an emitted signal but must not originate, suppress, or alter it.

## 3. Terminology

| Term | Definition |
|---|---|
| Current aggregate | Metrics derived from one `ChannelAnalytics` snapshot and its video collection. |
| Upload-cohort comparison | Comparison between newer and older videos in one snapshot; not repeated-snapshot channel growth. |
| Repeated snapshot | Two or more observations of the same public entity at different collection times. |
| Eligible video | A public, non-deleted video satisfying approved format, age, and exclusion rules. Current analytics do not establish this classification. |
| VSR | Product-generated view-to-subscriber ratio: video views divided by current visible channel subscribers. |
| Benchmark-relative | Compared with an explicitly defined external or peer baseline. |
| Ranking-relative | Compared with other items in a defined ranking population or cohort. |
| Threshold source | Provenance of a comparison boundary: existing requirement, mathematical derivation, proposal, experiment, or undefined. |
| Implementable now | All inputs and approved boundary semantics exist; it does not mean implemented. |

## 4. Eligible Video Policy v1

This section is the authoritative product policy for video eligibility in subscriber-relative
analytics. The policy, classifier, canonical fields, and subscriber-relative metrics described
here are approved and implemented. A change to any boundary, classification rule, or missing-data
behavior requires a new eligibility-policy version and review under ADR-008.

### 4.1 Conflict and gap resolution

| Topic | Existing product requirement | Existing TRD expectation | Current implementation | Ratified v1 decision |
|---|---|---|---|---|
| Lower age | Exclude videos younger than 24 hours | Configured maximum/minimum age implied | Classifier enforces the approved elapsed-time boundary | Inclusive lower bound: exactly 24 elapsed hours is eligible |
| Upper age | Exclude videos older than 90 days | Acquisition stops beyond maximum age | Classifier enforces the approved elapsed-time boundary | Inclusive upper bound: exactly 90 elapsed days is eligible |
| Evaluation time | Timestamped analytics required | Immutable snapshot timestamps | `ChannelAnalytics.generated_at` exists | Classifier receives explicit timezone-aware `evaluation_time`; normal value is `generated_at` |
| Future timestamp | Not specified | Canonical publication time expected | Classifier and time-dependent calculators reject it | Validation failure, never a normal exclusion |
| Missing publication | Eligible videos are recent published videos | Canonical video includes publication time | Field remains optional and missing values are excluded | Ineligible/incomplete; never guessed. Available published videos should carry it when supplied upstream |
| Privacy | Eligible means public | Availability modeled separately | `PrivacyStatus` or `None` | Only `PUBLIC`; private, unlisted, and unknown are ineligible |
| Availability | Deleted/private marked unavailable | `availability` expected | Closed canonical field populated conservatively by acquisition | Closed `VideoAvailability`; only `AVAILABLE` continues |
| View count | Retrievable statistics required | Snapshot view count expected | Optional non-negative value | Missing is ineligible; zero is valid; negative is invalid canonical input |
| Duplicate IDs | Duplicate discovery entities collapse | Idempotent persistence expected | Acquisition deduplicates requests while preserving discovery positions; analytics rejects duplicate IDs | Shared analytics validation rejects duplicate video IDs |
| Shorts | Separate from standard videos | `format_class` expected | Closed `VideoFormat`; acquisition never infers `SHORT` | Closed `VideoFormat`; no duration-only Shorts claim; unresolved cases are `UNKNOWN` |
| Standard video | Separate cohort | `format_class` expected | Non-live videos longer than three minutes map to `STANDARD` | v1 safely resolves non-live videos longer than three minutes as `STANDARD`; shorter/equal unresolved videos are `UNKNOWN` |
| Live state | Replays separate/excluded | `live_state` expected | Closed `LiveState` populated from official public live metadata | Closed `LiveState` mapped by acquisition from official public live metadata |
| Replay | Separate cohort or exclude by default | Live state and format expected | Completed livestreams map to `LIVE_REPLAY` | Completed livestream maps to `LIVE_REPLAY`; retained separately, excluded from standard median |
| Upcoming/live | Not explicitly eligible | Live state expected | Canonical states are populated and excluded by the classifier | `UPCOMING` and `LIVE` are ineligible for v1 |
| Uncertain format | Expose uncertainty | Format expected | Unresolved formats remain `UNKNOWN` | `UNKNOWN`; retained as exclusion and never reclassified downstream |
| Retrieval completeness | At least 60% | Numerator/denominator provenance expected | Enrichment facts exist transiently; no typed provenance result | Requested-ID resolution `>= 0.60` plus complete pagination; do not claim expected-population coverage |
| Minimum sample | At least five eligible videos | Qualification gate | Classifier count exists; qualification model is not implemented | Median calculable from one; qualification requires count `>= 5` |
| Subscriber visibility | Visible and greater than zero | Hidden state retained | Canonical count and hidden flag exist | Hidden, missing, zero, or missing statistics make VSR unavailable |
| Subscriber rounding | Preserve limitation | Captured public value | No rounding flag | Use captured value without correction; evidence must disclose public-value limitation |
| Format aggregation | Do not mix formats | Format-specific cohort expected | Classifier produces separate immutable format bases | Separate immutable standard, Shorts, and replay bases; first median is standard-only |

### 4.2 Evaluation time and age

The classifier accepts an explicit `evaluation_time`. It never reads the system clock. For normal
analytics processing, `evaluation_time` equals the source analytics snapshot's `generated_at`.
Both `evaluation_time` and `published_at` must be timezone-aware.

Age is elapsed duration without calendar-day rounding:

```text
video_age = evaluation_time - published_at
eligible_age = 24 hours <= video_age <= 90 days
```

- Younger than 24 hours is ineligible.
- Exactly 24 hours is eligible.
- Exactly 90 days is eligible.
- Older than 90 days is ineligible.
- `published_at > evaluation_time` is invalid analytics input and fails classification.
- Missing `published_at` is a normal incomplete-metadata exclusion; no timestamp is substituted.
- Scheduled upcoming items use explicit live state and must not masquerade as published videos
  through a future timestamp.

### 4.3 Canonical availability, privacy, and statistics

Canonical video availability uses a closed `VideoAvailability` enum:

```text
AVAILABLE
UNAVAILABLE
DELETED
UNKNOWN
```

Only `AVAILABLE` videos continue through eligibility checks. Availability describes whether the
canonical item can validly participate in analytics; it is distinct from privacy. Missing counters
must not be used to infer availability.

Only `PrivacyStatus.PUBLIC` videos are eligible. Private, unlisted, and missing/unknown privacy
states are ineligible. Eligible VSR input also requires a present non-negative view count. Zero
views are valid and later produce VSR `0.0`; a missing count is excluded rather than converted to
zero. Negative counts remain invalid canonical input.

For backward-compatible canonical construction, availability, live-state, and format fields
default to `UNKNOWN`. Such legacy/uncertain videos are safely excluded until
acquisition supplies resolved values.

The implemented canonical contract is:

| Field | Type / nullability | Default | Mapping and invariant | Immediate consumers |
|---|---|---|---|---|
| `availability` | `VideoAvailability`, non-null | `UNKNOWN` | Acquisition maps successful, unavailable, deleted, or unresolved upstream state; privacy is separate | Eligibility classifier |
| `live_state` | `LiveState`, non-null | `UNKNOWN` | Acquisition maps official live-broadcast facts; contradictory/missing facts remain unknown | Format mapping and eligibility |
| `format` | `VideoFormat`, non-null | `UNKNOWN` | Acquisition-owned versioned mapping; analytics never infers it | Format-specific bases |
| `published_at` | timezone-aware `datetime \| None` | `None` | Remains optional for unavailable/incomplete canonical items; eligible available videos require it | Age validation/classification |
| `duration` | `timedelta \| None` | `None` | Supporting acquisition classification fact, never sole proof of Shorts identity | Acquisition format mapping |
| `view_count` | `int \| None`, non-negative when present | `None` | Missing remains distinct from zero | Eligibility and VSR |
| `privacy_status` | `PrivacyStatus \| None` | `None` | Missing means unknown and is excluded | Eligibility |

The three new enum fields are backward-compatible for existing constructors through `UNKNOWN`
defaults. Existing optional publication, duration, statistics, and privacy fields remain optional
because canonical unavailable/incomplete items must remain representable. Eligibility, rather than
canonical construction, owns the stricter participation requirements.

### 4.4 Canonical live state and format

Canonical live state uses a closed `LiveState` enum:

```text
NOT_LIVE
UPCOMING
LIVE
COMPLETE
UNKNOWN
```

Canonical format uses a closed `VideoFormat` enum:

```text
SHORT
STANDARD
LIVE_REPLAY
UNKNOWN
```

Acquisition/domain construction owns YouTube-specific mapping. Analytics consumes these canonical
types and never repeats transport heuristics.

Discovery through `search.list` and `playlistItems.list` is enriched with complete `videos.list`
resources before canonical construction. Requests are stably deduplicated, output order and
duplicate positions follow discovery order, and each returned unique resource is parsed once.
Omitted resources are skipped without placeholders or deletion inference.

The v1 live mapping uses official public video metadata:

- upcoming broadcast -> `UPCOMING`;
- active broadcast -> `LIVE`;
- public live details with an actual end -> `COMPLETE` and `LIVE_REPLAY`;
- explicit non-live state without live details -> `NOT_LIVE`;
- missing or contradictory facts -> `UNKNOWN`.

Upcoming, active, and unknown live states are ineligible. Completed replays are retained only in
the replay basis. A long duration alone never implies a livestream replay.

The YouTube Data API does not expose a direct authoritative Shorts flag. Public YouTube policy
classifies Shorts using facts including duration, square/vertical aspect ratio, upload date, and
some channel context. The current canonical and transport models do not carry an authoritative
aspect-ratio or Shorts identity. Therefore acquisition format policy version 1 is conservative:

- `COMPLETE` live content -> `LIVE_REPLAY`;
- `UPCOMING`, `LIVE`, or unknown live state -> `UNKNOWN` format for eligibility;
- `NOT_LIVE` with duration strictly greater than three minutes -> `STANDARD`;
- `NOT_LIVE` with duration at or below three minutes, or missing duration -> `UNKNOWN`;
- `SHORT` is reserved for a future stronger official public fact or a separately approved
  classifier version; v1 does not infer it from duration alone.

This policy intentionally sacrifices recall to prevent Shorts from entering the standard cohort.
It uses the official maximum Shorts duration only to establish that a longer non-live video cannot
be a Short; it does not claim that every shorter video is a Short. References:
[YouTube Data API video resource](https://developers.google.com/youtube/v3/docs/videos) and
[YouTube Help: three-minute Shorts](https://support.google.com/youtube/answer/15424877).

### 4.5 Format-specific eligible bases

Classification produces separate immutable, source-ordered populations:

- standard videos;
- Shorts;
- livestream replays.

Unknown format is excluded with traceability. Formats are never combined into one median. The
first subscriber-relative aggregate uses only the standard basis and is named explicitly:

```text
MetricType.MEDIAN_STANDARD_VIDEO_VSR
SubscriberRelativeAnalytics.median_standard_video_vsr: float | None
```

The generic product term “Median VSR” means a median within one explicitly named format cohort;
it does not authorize an all-format aggregate. Shorts and replay median metrics are deferred.

### 4.6 Eligibility result contract

The implemented immutable contract is:

```text
EligibleVideoClassification
    eligible_standard_videos: tuple[Video, ...]
    eligible_shorts: tuple[Video, ...]
    eligible_livestream_replays: tuple[Video, ...]
    exclusions: tuple[VideoExclusion, ...]
    evaluated_at: datetime
    policy_version: int = 1
```

Classifier input is one validated `ChannelAnalytics` dataset plus explicit `evaluation_time`.
Shared analytics validation rejects non-timezone-aware evaluation/publication timestamps, future
publication timestamps, and duplicate video IDs before normal classification.

Eligible populations and exclusions preserve source order. Empty populations are valid.
`VideoExclusion` contains the video identity and one closed primary reason sufficient to explain
normal ineligibility. Detailed exclusions are justified immediately by qualification diagnosis,
future evidence, and deterministic testing; arbitrary strings and generic policy configuration
are prohibited. Invalid input raises the established analytics validation exception rather than
appearing as an exclusion. Identical inputs, evaluation time, and policy version produce equal
results.

The closed v1 primary exclusion vocabulary is:

```text
UNAVAILABLE
DELETED
UNKNOWN_AVAILABILITY
PRIVATE
UNLISTED
UNKNOWN_PRIVACY
MISSING_PUBLICATION_TIME
TOO_YOUNG
TOO_OLD
MISSING_VIEW_COUNT
UPCOMING
CURRENTLY_LIVE
UNKNOWN_LIVE_STATE
UNKNOWN_FORMAT
UNSUPPORTED_FORMAT
```

When multiple normal exclusions apply, classification records the first matching reason in this
order: availability, privacy, publication presence, age, view-count presence, live state, then
format. Within availability and privacy, the specific canonical state selects the reason. Invalid
shared invariants—duplicate IDs, naive timestamps, future publication, or negative counters—fail
before exclusion classification. This precedence affects explanation only; it never makes an
otherwise ineligible video eligible.

### 4.7 VSR, denominator, precision, and sample policy

For every eligible standard video:

```text
video_vsr = video.view_count / channel.statistics.subscriber_count
```

The denominator must be visible, present, and strictly positive. Hidden subscribers, missing
channel statistics, missing subscriber count, and zero subscribers make the aggregate unavailable.
They do not produce zero, infinity, a guessed denominator, or a validation error for legitimate
missing public data.

Public subscriber counts may be rounded. Analytics use the captured official public value without
estimation or correction. Results are deterministic relative to that snapshot, and future evidence
and explanations must preserve the approximation limitation.

The implemented factual metric is:

```text
median_standard_video_vsr = median(
    video.view_count / visible_positive_subscriber_count
    for video in eligible_standard_videos
)
```

One or more eligible standard videos make the median mathematically calculable. An empty standard
basis or unavailable denominator returns `None`. No minimum-five gate belongs in the calculator.
Use Python's existing floating-point/statistics conventions with no display or threshold rounding.
Median calculation is independent of source order.

The immutable `SubscriberRelativeAnalytics` aggregate exposes:

```text
eligible_standard_video_count: int
median_standard_video_vsr: float | None
```

Count zero distinguishes an empty standard basis from an unavailable subscriber denominator with
a positive eligible count. These are separate factual metrics with separate identities:

```text
MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT
MetricType.MEDIAN_STANDARD_VIDEO_VSR
```

`EligibleStandardVideoCountCalculator` returns only the integer count.
`MedianStandardVideoVsrCalculator` returns only the nullable median. Both consume one precomputed
`EligibleVideoClassification` through narrow typed inputs; the median calculator also receives the
explicit subscriber count. They do not implement the homogeneous `ChannelAnalytics` input contract
and do not execute through `CalculatorRegistry`.

ADR-009 assigns their sequencing and input delivery to the implemented
`SubscriberRelativeAnalyticsOrchestrator`. It invokes the count calculator first and the median
calculator second, once each, and returns ordered metric results. The implemented
`SubscriberRelativeResultAssembler` maps each metric identity to exactly one field on
`SubscriberRelativeAnalytics`. `SubscriberRelativeAnalyticsService` connects classification,
orchestration, and assembly, and the production composition root injects the complete path.

### 4.8 Duplicate IDs, requested-ID resolution, and qualification

Duplicate video IDs in one analytics dataset are invalid because they change medians, hit counts,
and completeness. Shared analytics dataset validation owns rejection; classifiers may assume
unique IDs.

Acquisition may discover the same ID at multiple positions. The approved future
`VideoAcquisitionResult` preserves those discovery positions and also exposes one stable,
first-seen canonical object per resolved unique ID. Only that unique collection may enter
`ChannelAnalytics`; independently supplied duplicate analytics input remains a validation error.

The approved acquisition-response metric is **requested-ID resolution rate**, not retrieval
completeness:

```text
requested_id_resolution_rate =
    enriched_unique_video_count / enrichment_requested_unique_count
```

The numerator counts unique requested IDs returned and parsed into canonical resources. The
denominator counts unique discovered IDs actually submitted to `videos.list`, excluding stable
cross-page duplicates. Exactly 60% qualifies; compare the integer numerator and denominator
without pre-comparison rounding. A zero denominator produces an undefined rate and no independent
resolution failure; the eligible-sample requirement still fails.

This rate does not measure complete channel retrieval. Discovery request capacity, discovery
positions, unique discovered IDs, enriched output positions, eligibility yield, pagination
coverage, and upstream `totalResults` are separate facts. Upstream `totalResults`, requested page
size, eligible/discovered, and supplied/supplied are prohibited completeness denominators.

Pagination is separately `COMPLETE` when no next-page token remains after the bounded acquisition
and `TRUNCATED` when acquisition stops with a next-page token. Intentional page limits remain
truncation for subscriber-relative qualification.

Subscriber-relative qualification requires uploads-playlist provenance scoped to the canonical
channel. General search provenance may span channels and cannot be partitioned or treated as a
channel qualification denominator. Search-discovered candidates require a subsequent channel
uploads acquisition.

ADR-010 approves a future immutable `SubscriberRelativeQualification`. It covers:

- eligible standard-video count `>= 5` (equality qualifies);
- visible positive canonical subscriber count;
- requested-ID resolution rate `>= 0.60` when defined;
- complete pagination;
- acquisition provenance and explicit evaluation time.

Hidden subscribers, unavailable subscribers, and zero subscribers are distinct normal failures.
Negative subscriber counts and a hidden flag accompanied by a numeric count are invalid canonical
input and raise validation errors. Missing publication, privacy, availability, format, or view
facts remain classifier exclusions rather than a generic canonical-incomplete qualification
reason.

All applicable qualification failures accumulate in this fixed order:

1. `ACQUISITION_TRUNCATED`
2. `INSUFFICIENT_REQUESTED_ID_RESOLUTION`
3. `SUBSCRIBER_COUNT_HIDDEN`
4. `SUBSCRIBER_COUNT_UNAVAILABLE`
5. `SUBSCRIBER_COUNT_NOT_POSITIVE`
6. `INSUFFICIENT_ELIGIBLE_STANDARD_VIDEOS`

Qualification is neither positive nor negative business meaning. Existing calculators continue
to return factual analytics whenever mathematically possible, including for unqualified datasets.
The future `SubscriberRelativeAnalysisResult` returns qualification and analytics together.
Downstream signal evaluation must require `qualification.qualified`; rules must not recreate these
gates. Whether qualification failures are themselves exposed as Signals remains deferred.

## 5. Analytics inventory

All Path A fields below are exposed by `CalculatedChannelAnalytics`. `source_dataset` is snapshot
provenance rather than a calculated metric; it contains the canonical `Channel`, videos, and
`generated_at` timestamp.

| Metric | Type / nullability | Unit and input basis | Calculator and factual interpretation | Minimum data and limitations | Time basis | Signal support |
|---|---|---|---|---|---|---|
| `channel_age` | `int`, required | Whole elapsed days from channel publication to injected clock | `ChannelAgeCalculator`; factual channel age | Published date and timezone-aware clock; rejects future dates; result depends on calculation time | Current channel metadata | Can support a rule only after age policy is approved; not evidence of emergence by itself |
| `upload_frequency` | `float`, required | Uploads per seven elapsed days between earliest and latest supplied videos | `UploadFrequencyCalculator`; observed publication cadence | At least one video with publication time; one video returns `1.0`; a one-day minimum window can distort small samples | Current supplied upload collection | Partially supports a cadence rule; no approved threshold or eligibility filtering |
| `average_views` | `float`, required | Arithmetic mean of lifetime view counts | `AverageViewsCalculator`; mean absolute reach | At least one video with non-negative view count; highly outlier-sensitive; no age, format, subscriber, or cohort normalization | Current aggregate performance | Weak alone; must not be an opportunity signal |
| `median_views` | `float`, required | Median lifetime video views | `MedianViewsCalculator`; robust absolute reach midpoint | At least one valid view count; no age, format, subscriber, or cohort normalization | Current aggregate performance | More robust than mean but still not subscriber-relative or benchmark-relative |
| `views_per_day` | `float`, required | Mean of each video's lifetime views divided by elapsed days, with one-day denominator floor | `ViewsPerDayCalculator`; age-adjusted current view accumulation proxy | At least one video with publication time and views; uses injected clock; lifetime average is not repeated-snapshot velocity | Current aggregate with video-age normalization | Partially supports a proposal; benchmark and threshold are undefined |
| `view_distribution` | `float`, required | Population coefficient of variation of lifetime views | `ViewDistributionCalculator`; dispersion relative to mean | At least one valid view count; returns `0.0` when mean is zero; unstable in small samples and says nothing about subscriber scale | Distribution in current aggregate | Can support descriptive concentration policy after sample and threshold approval |
| `upload_consistency` | `float`, required | Population coefficient of variation of consecutive upload intervals | `UploadConsistencyCalculator`; lower means more regular intervals | At least one dated video; one video and zero mean interval return `0.0`, which does not prove a stable cadence | Distribution of upload intervals in current collection | Partially supports a cadence rule; minimum sample and threshold are undefined |
| `view_outlier` | `OutlierResult`, required | IDs and population z-scores of highest and lowest lifetime-view observations | `ViewOutlierCalculator`; identifies extrema, not statistically approved outliers | At least one valid view count; one/constant collections return no IDs; no significance threshold; small samples are misleading | Distribution in current aggregate; individual video references | Cannot support a production breakout rule without eligibility, age handling, and approved significance policy |
| `view_growth_rate` | `float`, required | Newer-half mean lifetime views divided by older-half mean | `ViewGrowthRateCalculator`; upload-cohort performance ratio | At least one dated video with views; one video returns `1.0`; old mean zero yields `1.0` or infinity; lifetime exposure differs by video age | Upload-cohort comparison within one snapshot | Can support only a carefully named proposal; must not be called historical or snapshot growth |
| `view_engagement_rate` | `float \| None` | Unweighted mean of `(likes + comments) / views` for videos with all three values and views greater than zero | `ViewEngagementRateCalculator`; observed public interaction rate | May be `None`; silently excludes ineligible rows; no explicit sample count, format separation, age adjustment, or benchmark | Current aggregate performance | Blocked for unusual-engagement policy by missing sample evidence and benchmark |

Path B exposes the following fields through immutable `SubscriberRelativeAnalytics`:

| Metric | Type / nullability | Unit and input basis | Calculator and factual interpretation | Minimum data and limitations | Time basis | Signal support |
|---|---|---|---|---|---|---|
| `eligible_standard_video_count` | `int`, required | Count of the Eligible Video Policy v1 standard-video basis | `EligibleStandardVideoCountCalculator`; factual classified population size | Valid `EligibleVideoClassification`; zero is valid | Explicit eligibility evaluation time | Supports future qualification and sample evidence; no business meaning by itself |
| `median_standard_video_vsr` | `float \| None` | Median standard-video views divided by explicit public subscriber count | `MedianStandardVideoVsrCalculator`; subscriber-relative reach midpoint | At least one eligible standard video and a positive subscriber count; otherwise `None` | Current captured views/subscribers over the evaluated eligibility basis | Factual prerequisite for SIG-002; threshold `T` remains unapproved |

`SubscriberRelativeAnalyticsService` exposes the fully classified, orchestrated, and assembled
Path B result. These metrics intentionally remain separate from `CalculatedChannelAnalytics`.

### 5.1 Capability distinctions

- **Current aggregate performance:** average views, median views, views per day, and engagement
  rate describe the supplied snapshot only.
- **Upload-cohort comparison:** `view_growth_rate` compares newer and older uploads. It is not
  repeated-snapshot view growth.
- **Distribution:** view distribution, view outlier, and upload consistency summarize variation
  inside the supplied collection.
- **Repeated-snapshot growth:** not available.
- **Subscriber-relative performance:** count and median standard-video VSR are available through
  the composed `SubscriberRelativeAnalyticsService` as a typed immutable aggregate.
- **Benchmark-relative performance:** not available.
- **Ranking-relative performance:** not available.
- **Eligible-video population:** available as immutable `EligibleVideoClassification` and the
  assembled eligible standard-video count.

## 6. Product requirement mapping

Sources are the Product Requirements Document (PRD), Technical Requirements Document (TRD),
UI/UX Specification, Security Specification, and Feature Catalogue under
`docs/product/source/`.

| Product concept | Source | Classification | Finding |
|---|---|---|---|
| High views relative to subscriber base | PRD §§1, 5, 8.2; FR-SCO-001 | Factual analytics implemented; signal policy blocked | Eligible standard-video count and median VSR are assembled; production threshold and qualification remain unapproved |
| Median VSR | PRD §5 and §8.2; Eligible Video Policy v1 | Implemented factual analytics | Standard-video classification, calculation, orchestration, assembly, aggregate, and composed service are implemented |
| Repeated video overperformance / hit consistency | PRD §5 and §8.2; Eligible Video Policy v1 | Partially supported by approved policy | VSR hit boundary is `>= 1.0`; classification exists, but qualifying-hit analytics and hit-share threshold `P` remain undefined |
| Breakout video | PRD §9; FR-ALT-001; Feature Catalogue E04 | Ambiguous product policy | Product intent exists, but “materially exceeds baseline” and baseline are undefined |
| Momentum score | PRD §8.2; TRD scoring sections | Requires cohort, snapshots, and ranking context | Components and weights are documented, but supporting cohort and history infrastructure are absent |
| Observed velocity / acceleration | PRD §§5, 8.2; FR-SCO-003 | Requires repeated snapshots | Current views-per-day and upload-cohort ratio cannot substitute for public view-count deltas |
| Consistent performance | PRD §8.2; FR-SCO-003 | Requires new metrics | Product consistency means repeated VSR overperformance, not upload schedule consistency |
| Upload consistency | Existing analytics only | Ambiguous product policy | Factual cadence metric exists but product discovery value and thresholds are not approved |
| Engagement | UI filters and current analytics | Requires external benchmark data | “Unusual” needs peer/format baseline plus eligible sample count |
| High views per day | Current analytics; related to PRD velocity intent | Partially supported | Metric exists, but it is lifetime age-normalized reach, not snapshot velocity; threshold/benchmark absent |
| Declining performance | General monitoring intent | Ambiguous product policy | Upload-cohort ratio exists, but naming, boundary, and minimum sample need approval |
| Cohort percentile | PRD §8.2 | Requires ranking/cohort context | Cohort definition is approved conceptually; no cohort service or values exist |
| Qualification / insufficient data | PRD §8.1; Eligible Video Policy v1; FR-SCO-002 | Policy and contract approved; implementation pending | ADR-010 defines provenance, requested-ID resolution, pagination, subscriber state, ordered failures, and the analysis-result boundary |
| Confidence | PRD §8.3 | Requires new metrics and snapshots | Conditions are documented; subscriber-relative count exists, but completeness, anomaly state, and history remain absent |
| Hidden subscriber handling | PRD guardrail GR-01 and §9 | Supported canonically and analytically | Canonical channel retains hidden state; callers supply unavailable subscriber count to the VSR pipeline, which returns `None` |
| Stale snapshot | General traceability requirement | Ambiguous product policy | Timestamp exists; maximum acceptable age and evaluation clock policy are undefined |

## 7. Signal catalog schema

Every entry uses these fields:

1. **Identity:** catalog ID, `RuleId`, `SignalType`, `ReasonCode`, name, version, status.
2. **Business meaning:** question, value, interpretation, non-meaning, consumers.
3. **Inputs:** analytics/canonical fields, benchmarks, snapshots, sample, missing behavior.
4. **Deterministic policy:** exact condition, operator, threshold provenance, equality, null,
   zero, precision, cardinality, coexistence.
5. **Signal output:** polarity, factual evidence, observed/comparison values, units, snapshot and
   provenance.
6. **Explanation contract:** internal and user interpretation, prohibited wording, AI limits.
7. **Limitations:** statistical, sample, temporal, benchmark, and error modes.
8. **Dependencies:** current/new metrics, ingestion, benchmark, history, ranking.
9. **Approval:** required approvers, open decisions, readiness.

Allowed lifecycle statuses are **Proposed**, **Approved**, **Implementable Now**, **Blocked**,
**Deferred**, **Rejected**, and **Deprecated**. Approval and readiness are recorded separately:
an approved definition can remain blocked by missing analytics.

## 8. Candidate signal catalog

### SIG-001 — Sustained subscriber-relative overperformance

**Identity:** `RuleId=discovery.sustained_subscriber_relative_overperformance`;
`SignalType=discovery.sustained_subscriber_relative_overperformance`;
`ReasonCode=discovery.consistent_vsr_at_or_above_one`; name “Sustained subscriber-relative
overperformance”; version 1; **Blocked**.

**Business meaning:** Answers whether a channel repeatedly earns at least as many views per
eligible video as its visible subscriber count. It supports discovery analysts. It does not mean
subscriber growth, revenue, audience quality, or guaranteed future performance.

**Inputs:** Per-standard-video VSR, eligible standard-video count, qualifying-hit count,
visible non-zero subscriber count, snapshot provenance; no benchmark or history. Minimum five
eligible standard videos under PRD §8.1 and Eligible Video Policy v1; missing/hidden/zero
subscribers or fewer than five eligible videos emit no signal and produce qualification state
outside this rule.

**Deterministic policy:** Emit when
`qualifying_hit_count / eligible_standard_video_count >= P`, where a
hit is approved by PRD §8.2 as `video_vsr >= 1.0`. The `1.0` threshold is **Explicitly defined in
existing requirements**, including equality. `P` is **Not yet defined**. Use full-precision
values with no pre-comparison rounding. Emit zero or one; may coexist with high median VSR and a
breakout signal.

**Signal output:** Positive polarity. Evidence must include hit-consistency metric, observed
share, comparator `P`, `>=`, proportion unit, eligible sample count, VSR hit threshold `1.0`,
subscriber count, channel ID, snapshot timestamp, rule ID/version. Current `SignalEvidence`
cannot represent comparator, operator, unit, or sample count.

**Explanation contract:** Internal: approved share of eligible uploads reached subscriber parity.
User-facing: “A sustained share of eligible videos reached at least one view per subscriber.”
Prohibit “viral,” “fast-growing,” “guaranteed growth,” and claims about unique viewers. AI may
explain only emitted evidence and must preserve sample, threshold, and subscriber visibility.

**Limitations:** Public subscriber counts may be rounded; views and subscribers are collected at
one time; format and age affect VSR; embedded/paid traffic is not distinguishable. Small samples
create false positives; strict eligibility can create false negatives.

**Dependencies:** Approved Eligible Video Policy v1; canonical model evolution; classifier;
per-video VSR and hit-consistency metrics. No benchmark, history, or ranking service.

**Approval:** Eligibility and ratio semantics are approved by Eligible Video Policy v1. Product
must still approve `P`; Architecture must review evidence evolution. Not implementable now.

### SIG-002 — High median subscriber-relative reach

**Identity:** `RuleId=discovery.high_median_vsr`; `SignalType=discovery.high_median_vsr`;
`ReasonCode=discovery.median_vsr_above_policy_threshold`; name “High median subscriber-relative
reach”; version 1; **Blocked**.

**Business meaning:** Answers whether the typical eligible recent video materially outperforms
the channel's subscriber scale. It is a core discovery signal, not a growth rate or cohort rank.

**Inputs:** Median standard-video VSR, eligible standard-video count, visible positive subscribers,
and snapshot provenance; no history. The metric may exist below five videos, while future
qualification requires at least five. Missing/hidden/zero subscribers or failed qualification
emit no production signal.

**Deterministic policy:** Emit when `median_standard_video_vsr >= T`. `T` is **Not yet defined**;
equality is included in the proposed operator. No rounding before comparison. Zero or one; may
coexist with SIG-001 and SIG-003.

**Signal output:** Positive. Evidence: median VSR, observed ratio, `T`, `>=`, ratio unit, sample
count, subscriber count, channel/snapshot, rule version. Current evidence has the same comparison
and sample gaps described in SIG-001.

**Explanation contract:** Say “typical eligible recent video views relative to current public
subscribers.” Prohibit “subscriber growth,” “audience conversion,” and unqualified “viral.” AI
must retain eligibility window, format, sample, and approximate-subscriber caveats.

**Limitations:** Same-time denominator, rounded subscribers, video-age exposure, conservative
format exclusions, and traffic-source ambiguity. Median reduces but does not eliminate selection
bias.

**Dependencies:** Approved Eligible Video Policy v1; canonical model evolution; classifier;
`ELIGIBLE_STANDARD_VIDEO_COUNT`; `MEDIAN_STANDARD_VIDEO_VSR`; evidence extension. Product and
Analytics must approve `T` through cohort analysis, labelled review, and sensitivity testing.

**Approval:** Eligibility, denominator, standard basis, and null semantics are approved. Product
and Analytics must approve `T`; Architecture reviews evidence evolution. Not implementable now.

### SIG-003 — Breakout eligible video

**Identity:** `RuleId=discovery.breakout_video`; `SignalType=discovery.breakout_video`;
`ReasonCode=discovery.video_materially_above_channel_baseline`; name “Breakout eligible video”;
version 1; **Blocked**.

**Business meaning:** Identifies one eligible recent video materially above an approved channel
baseline. It is evidence of a breakout observation, not sustained channel performance.

**Inputs:** Eligible video ID, age/format-adjusted performance, approved baseline, eligible sample
and subscriber visibility as policy decides. Missing baseline/sample emits none.

**Deterministic policy:** Operator and threshold are **Not yet defined**. Options: z-score above an
approved boundary; VSR multiple above median VSR; or snapshot velocity above baseline. Equality,
null, zero, precision, and coexistence remain open. Emit at most one highest qualifying video;
may coexist with sustained signals but must never substitute for them.

**Signal output:** Positive. Evidence must identify video, metric, observed value, baseline,
operator, threshold, unit, sample, channel, timestamp, and provenance.

**Explanation contract:** “One eligible video materially exceeded the defined baseline.” Prohibit
“sustained,” “channel is growing,” or causal claims. AI must name the single-video scope.

**Limitations:** Highly susceptible to paid/embedded distribution, topic spikes, small samples,
age exposure, and baseline selection within a format-specific basis. Current z-score extrema are
not approved significance tests.

**Dependencies:** Approved format-specific eligibility plus an undefined breakout baseline,
possibly VSR/velocity, and richer evidence. Product and Analytics approval required.

**Approval:** Product selects the breakout definition; Analytics validates baseline and false
positives; Architecture reviews evidence shape. Not implementable now.

### SIG-004 — Newer upload cohort outperformance

**Identity:** `RuleId=performance.newer_upload_cohort_outperformance`;
`SignalType=performance.newer_upload_cohort_outperformance`;
`ReasonCode=performance.newer_half_mean_views_above_older_half`; name “Newer upload cohort
outperformance”; version 1; **Proposed**.

**Business meaning:** Answers whether newer supplied uploads currently have higher mean lifetime
views than older supplied uploads. It is supporting context, not repeated-snapshot growth,
acceleration, or subscriber-relative opportunity.

**Inputs:** Current `view_growth_rate`; proposed minimum sample of four dated videos; no benchmark
or snapshots. Missing dates are rejected upstream. Infinite values caused by zero older mean need
explicit policy.

**Deterministic policy:** Proposed emit when finite `view_growth_rate > 1.0`. Boundary `1.0` is
**Derived mathematically from the metric definition** as equal cohort means, but interpreting any
increase as material is **Proposed for product approval**. Equality emits none. No rounding.
Zero or one; may coexist with subscriber-relative signals.

**Signal output:** Positive. Evidence: growth-rate metric, observed ratio, `1.0`, `>`, ratio unit,
sample and split sizes, channel/snapshot, provenance. Current evidence lacks comparator/operator,
unit, and sample sizes.

**Explanation contract:** “Newer supplied uploads have a higher mean lifetime view count than the
older supplied uploads.” Prohibit “channel growth,” “view velocity,” “accelerating,” and any
snapshot-history claim. AI must preserve cohort and lifetime-view semantics.

**Limitations:** Newer videos usually have less exposure time; means are outlier-sensitive;
collection selection and odd splits affect output; infinity is not interpretable. False positives
include one recent hit; false negatives include strong but younger videos.

**Dependencies:** Existing metric plus sample-count evidence and approved infinity policy. Product
and Analytics approval required. Data exists, but policy and evidence are not implementation-ready.

**Approval:** Product must approve whether this supporting observation has user value and what
counts as material; Analytics must approve sample and exposure controls. Proposed only.

### SIG-005 — Unusual engagement

**Identity:** `RuleId=performance.unusual_engagement`; `SignalType=performance.unusual_engagement`;
`ReasonCode=performance.engagement_above_peer_benchmark`; name “Unusual engagement”; version 1;
**Blocked**.

**Business meaning:** Asks whether eligible videos receive unusually high public likes/comments
relative to views and comparable peers. It does not measure watch time, sentiment, authenticity,
or subscriber conversion.

**Inputs:** Engagement rate, eligible count, excluded count/reasons, format/age cohort benchmark.
Minimum sample and missing behavior are undefined; `None` must emit none.

**Deterministic policy:** Compare against a cohort percentile or robust boundary; operator,
threshold, equality, and sample are **Not yet defined**. No rounding. Zero or one.

**Signal output:** Positive with observed rate, comparator, operator, percent unit, sample,
eligibility, source/provenance. AI may explain public interactions only and must not say audience
quality or positive sentiment.

**Explanation contract:** Internal and user explanations must say public likes/comments per view
relative to a named peer benchmark. Prohibit “audience quality,” “positive sentiment,” “loyalty,”
and authenticity claims. AI must preserve cohort and sample facts.

**Limitations:** Optional counts, platform behavior, bots, controversy, format, and small videos
can distort rates. Current unweighted mean and missing sample count are insufficient.

**Dependencies:** Revised engagement aggregate or companion sample metric, eligibility, benchmark
service. Product/Analytics approval and benchmark validation required.

**Approval:** Product approves user meaning and comparator; Analytics approves metric/sample and
cohort construction; Architecture approval is needed only for evidence changes. Not implementable.

### SIG-006 — High age-normalized view accumulation

**Identity:** `RuleId=performance.high_views_per_day`; `SignalType=performance.high_views_per_day`;
`ReasonCode=performance.views_per_day_above_peer_benchmark`; name “High views per day”; version 1;
**Blocked**.

**Business meaning:** Describes high lifetime view accumulation adjusted by video age relative to
comparable channels. It is not repeated-snapshot velocity.

**Inputs:** `views_per_day`, eligible sample, format/age cohort benchmark. Missing benchmark emits
none. Minimum sample is undefined.

**Deterministic policy:** Compare with an approved peer percentile. Percentile and equality are
**Not yet defined**. Full precision; zero or one; may coexist with VSR signals.

**Signal output:** Positive with observed rate, benchmark, operator, views/video/day unit, sample,
source/provenance. Prohibit “real-time velocity” and “accelerating.”

**Explanation contract:** Describe lifetime age-normalized view accumulation relative to the
named peer benchmark. AI must not call it real-time velocity, acceleration, or subscriber growth.

**Limitations:** Lifetime average, one-day floor, old-video selection, topic and format effects.
Requires cohort context and may favor absolute channel scale.

**Dependencies:** Eligibility/sample metric and benchmark service. Product/Analytics approval.

**Approval:** Product approves discovery value and percentile; Analytics approves cohort/sample
policy. Architecture approval is needed only for evidence evolution. Not implementable now.

### SIG-007 — Stable upload cadence

**Identity:** `RuleId=publishing.stable_upload_cadence`;
`SignalType=publishing.stable_upload_cadence`;
`ReasonCode=publishing.interval_variation_at_or_below_policy`; name “Stable upload cadence”;
version 1; **Deferred**.

**Business meaning:** Describes regular upload intervals for workflow context. It does not imply
audience demand, quality, opportunity, or sustained performance.

**Inputs:** `upload_consistency`, upload count, observation span. Proposed minimum three uploads;
missing dates fail upstream.

**Deterministic policy:** Emit when coefficient of variation `<= C`; `C` and sample policy are
**Not yet defined**. One-video `0.0` must never qualify. No rounding; zero or one.

**Signal output:** Informational with observed coefficient, `C`, `<=`, coefficient unit, upload
count/window, source/provenance. AI must frame it as cadence only.

**Explanation contract:** Describe regularity of observed upload intervals only. Prohibit claims
about content quality, audience demand, creator reliability, or future publishing behavior.

**Limitations:** Seasonal schedules, batching, same timestamps, small samples, and incomplete
inventories. It is supporting, not core discovery evidence.

**Dependencies:** Sample/window evidence and product approval. Deferred until core discovery
signals exist.

**Approval:** Product must first establish a supporting use case; Analytics approves sample and
window semantics. Architecture approval is not currently required. Deferred.

### SIG-008 — Declining newer upload cohort performance

**Identity:** `RuleId=performance.newer_upload_cohort_decline`;
`SignalType=performance.newer_upload_cohort_decline`;
`ReasonCode=performance.newer_half_mean_views_below_older_half`; name “Declining newer upload
cohort performance”; version 1; **Proposed**.

**Business meaning:** Answers whether newer supplied uploads currently have lower mean lifetime
views than older supplied uploads. It is not proof of declining channel demand or snapshot loss.

**Inputs:** `view_growth_rate`, proposed minimum four videos, finite-value policy. No history.

**Deterministic policy:** Proposed `view_growth_rate < 1.0`; `1.0` is mathematical equality, while
materiality and sample are **Proposed for product approval**. Equality emits none; no rounding;
zero or one; mutually exclusive with SIG-004 for the same rule version.

**Signal output:** Negative with ratio, comparator/operator, sample/split, source/provenance.
Current evidence gaps apply. Prohibit “losing subscribers,” “channel decline,” and causal claims.

**Explanation contract:** Describe only lower mean lifetime views in the newer supplied half.
AI must not claim channel decline, lost demand, subscriber loss, or repeated-snapshot change.

**Limitations:** Exposure-age bias can systematically make newer uploads appear weaker; means are
outlier-sensitive. Requires validation before approval.

**Dependencies:** Existing metric, evidence expansion, sample and finite-value policy. Product and
Analytics approval required.

**Approval:** Product approves materiality and user value; Analytics validates exposure bias and
sample/infinity behavior. Proposed only.

### SIG-009 — Highly uneven video outcomes

**Identity:** `RuleId=performance.high_view_dispersion`;
`SignalType=performance.high_view_dispersion`;
`ReasonCode=performance.view_coefficient_of_variation_above_policy`; name “Highly uneven video
outcomes”; version 1; **Deferred**.

**Business meaning:** Indicates lifetime views are concentrated unevenly across supplied videos.
It does not prove a breakout, instability, or poor channel quality.

**Inputs:** `view_distribution`, sample count, format/age eligibility. Minimum and missing policy
undefined.

**Deterministic policy:** Proposed `view_distribution > D`; `D` is **Not yet defined**. Equality,
minimum sample, and zero-mean behavior require approval. Zero or one.

**Signal output:** Informational with coefficient, `D`, operator, sample, source/provenance. AI may
describe dispersion only.

**Explanation contract:** Say that supplied video lifetime views are unevenly distributed.
Prohibit “breakout,” “unreliable,” or performance-quality conclusions without another signal.

**Limitations:** Small samples, mixed formats, ages, and zero-heavy collections; coefficient is
unstable near zero mean.

**Dependencies:** Eligibility/sample metric and product validation. Deferred as supporting context.

**Approval:** Product must establish a supporting use case and threshold; Analytics approves
sample and zero-mean policy. Deferred.

### SIG-010 — Insufficient eligible evidence

**Identity:** `RuleId=eligibility.insufficient_eligible_videos`;
`SignalType=eligibility.insufficient_evidence`;
`ReasonCode=eligibility.fewer_than_five_eligible_videos`; name “Insufficient eligible evidence”;
version 1; **Blocked**.

**Business meaning:** Explains why a channel cannot enter subscriber-ratio scoring. It is a
data-quality/qualification outcome, not negative performance.

**Inputs:** Eligible standard-video count and exclusion reasons, requested-ID resolution,
pagination state, and visible subscriber state. Minimum five eligible videos is **Explicitly
defined in existing requirements**
(PRD §8.1) and assigned to qualification by Eligible Video Policy v1.

**Deterministic policy:** If qualification failures later become signals, emit when
`eligible_standard_video_count < 5`; equality at five emits none. Count comparison uses integers
without rounding. Missing classification is a pipeline failure, not zero. Zero or one; may coexist
with missing-subscriber qualification state if product approves multiple reasons.

**Signal output:** Informational with observed count, threshold five, `<`, video-count unit,
exclusion summary, source/provenance. Current evidence lacks comparator, unit, and exclusion/sample
structure.

**Explanation contract:** “Fewer than five videos met the approved eligibility policy.” Prohibit
“poor performance” or claims that the channel has fewer than five total videos. AI may explain
exclusion facts only.

**Limitations:** Correctness depends entirely on explicit format, age, privacy, deletion, and
retrieval rules. Incomplete acquisition may cause false insufficiency.

**Dependencies:** The classifier and count are implemented; ADR-010 qualification and acquisition
provenance remain to be implemented. The decision whether qualification failures are signals
remains open. Not ready.

**Approval:** Product confirms whether qualification failures are signals; Analytics approves the
eligibility pipeline and exclusion evidence; Architecture reviews the result/evidence boundary.

### SIG-011 — Missing subscriber basis

**Identity:** `RuleId=eligibility.missing_subscriber_basis`;
`SignalType=eligibility.insufficient_evidence`;
`ReasonCode=eligibility.subscriber_count_hidden_or_unavailable`; name “Missing subscriber basis”;
version 1; **Blocked**.

**Business meaning:** Explains why subscriber-relative analysis is unavailable. It does not imply
low subscribers or poor performance.

**Inputs:** Canonical `source_dataset.channel.statistics.subscriber_count_hidden` and
`source_dataset.channel.statistics.subscriber_count`; no benchmark/history. Missing channel
statistics must not be interpreted as a numeric zero.

**Deterministic policy:** Candidate condition: hidden is true or count is `None`; zero subscriber
handling is a separate approved PRD §8.1 qualification failure. Exact coexistence and whether
qualification outcomes are Signals or a separate result model are **Ambiguous product policy**.
No rounding; zero or one.

**Signal output:** Informational; evidence must avoid fabricating a numeric metric and identify
canonical subscriber availability, source channel, snapshot, and provenance. Current evidence is
metric-oriented and cannot represent this canonical fact cleanly.

**Explanation contract:** “Subscriber-relative analysis is unavailable because public subscriber
count is hidden or unavailable.” Prohibit estimating the hidden count. AI may repeat only the
availability state.

**Limitations:** Availability can change; zero and hidden are distinct; raw API omission and policy
errors must not be conflated.

**Dependencies:** Decision whether eligibility outcomes belong in Signal Engine, plus evidence
support for canonical facts. Architecture/Product approval required.

**Approval:** Product decides whether this is a Signal or qualification result; Analytics confirms
missing/hidden/zero distinctions; Architecture approves canonical-fact evidence if it remains a
signal. Not implementable now.

### SIG-012 — Stale analytics snapshot

**Identity:** `RuleId=data_quality.stale_analytics_snapshot`;
`SignalType=data_quality.stale_analytics_snapshot`;
`ReasonCode=data_quality.snapshot_older_than_policy`; name “Stale analytics snapshot”; version 1;
**Deferred**.

**Business meaning:** Warns that evidence may no longer represent current public metrics. It does
not mean performance declined.

**Inputs:** `source_dataset.generated_at`, explicit evaluation clock, maximum age policy.

**Deterministic policy:** Emit when `evaluation_time - generated_at > A`; `A` is **Not yet defined**.
Equality and clock ownership require approval. No rounding; zero or one.

**Signal output:** Informational with snapshot time, evaluation time, observed age, `A`, operator,
time unit, channel/provenance. Prohibit performance conclusions.

**Explanation contract:** Explain only that the snapshot exceeds an approved freshness window.
AI must not infer decline or changed metrics and must preserve both timestamps.

**Limitations:** Freshness needs differ by workflow; current Signal Engine intentionally has no
clock dependency.

**Dependencies:** Product freshness policy and explicit deterministic clock/snapshot evaluation
input. Deferred; do not add a hidden system clock to rules.

**Approval:** Product approves workflow-specific freshness; Architecture approves explicit time
input ownership if implemented. Analytics approval is not otherwise required. Deferred.

## 9. Approved signals

None. Existing requirements approve several component definitions and qualification boundaries,
but no complete catalog entry has all semantics, inputs, evidence, and approvals needed for a
production `SignalRule`.

## 10. Implementable-now signals

None. SIG-004 and SIG-008 use an existing metric, but materiality, minimum sample, infinity
handling, and evidence comparison fields remain unresolved. They are proposals, not production
policy.

## 11. Blocked signals

| Signal | Primary blocker |
|---|---|
| SIG-001 | Qualifying-hit analytics, qualification implementation/evidence contract, and approved share threshold `P` |
| SIG-002 | Qualification implementation/evidence contract and threshold `T` |
| SIG-003 | Approved breakout baseline and significance policy |
| SIG-005 | Eligible sample evidence and cohort benchmark |
| SIG-006 | Cohort benchmark and eligibility/sample evidence |
| SIG-010 | ADR-010 qualification implementation, decision to represent failures as signals, and evidence shape |
| SIG-011 | Decision whether the qualification failure is also a Signal, plus canonical-fact evidence |

Deferred supporting signals SIG-007, SIG-009, and SIG-012 should not displace core discovery
work. Proposed SIG-004 and SIG-008 require approval and validation.

## 12. Rejected signals and designs

- **High average views means opportunity:** rejected; absolute scale is not subscriber-relative.
- **Any extrema from `view_outlier` means breakout:** rejected; extrema are not significance.
- **One breakout means sustained performance:** rejected; it contradicts robust discovery intent.
- **`view_growth_rate` means historical channel growth:** rejected; it is upload-cohort comparison.
- **Views per day means repeated-snapshot velocity:** rejected; formulas and time bases differ.
- **Percentile without a defined cohort:** rejected; the comparator population would be hidden.
- **Thresholds embedded ad hoc in rule classes:** rejected; thresholds are catalog-governed policy.
- **AI decides signal existence:** rejected; it is non-deterministic and violates ADR-002/ADR-006.
- **Presentation copy inside evidence:** rejected; evidence is factual and machine-readable.
- **Severity before a product prioritisation use case:** rejected for v1.
- **Generic DSL or configuration-driven engine:** rejected until multiple approved rules prove a
  runtime configuration need.

## 13. Threshold governance

Every comparison boundary must use exactly one provenance label:

- **Explicitly defined in existing requirements**
- **Derived mathematically from an existing approved definition**
- **Proposed for product approval**
- **Experimental only**
- **Not yet defined**

Approval records must cite source section, approving owner, approval date, validation evidence,
and affected catalog/rule version. Proposed and experimental thresholds must never ship as
production defaults.

For undefined thresholds, the entry must record the choice, candidate options, trade-offs, and
validation plan. Recommended methods are historical backtesting, cohort percentile analysis,
labelled-channel review, false-positive/false-negative review, sensitivity analysis, format
segmentation, and expert judgement followed by data validation.

Current threshold decisions:

| Decision | Options | Trade-off and validation |
|---|---|---|
| Hit-consistency share `P` | Fixed share; sample-adjusted lower bound; cohort percentile | Fixed is explainable; adjusted reduces small-sample false positives; cohort is contextual but operationally heavier. Backtest against labelled channels. |
| Median VSR `T` | Fixed VSR; subscriber-band threshold; cohort percentile | Fixed is transparent; bands address denominator effects; percentile aligns with ranking but needs cohorts. Run sensitivity by format/subscriber band. |
| Breakout baseline | Z-score; multiple of median VSR; snapshot velocity percentile | Each answers a different question. Compare false positives from one-hit spikes and age effects. |
| Upload-cohort materiality | Any ratio above/below `1.0`; buffer around parity; confidence interval | Parity is simple but noisy; buffer needs empirical selection; intervals need sample assumptions. Validate exposure-age bias. |
| Freshness `A` | Workflow-specific hours/days | Tighter policy improves currency but increases quota/cost. Validate against refresh schedules. |

## 14. Evidence standards

Evidence must be factual, typed, minimal, sufficient, deterministic, traceable, and free of
promotional or AI-authored language. It must contain only facts used by the rule and must not copy
the full analytics aggregate.

For threshold comparisons, evidence normally requires:

- metric identity and typed observed value;
- comparator or threshold and operator;
- semantic unit;
- sample size and eligibility basis when relevant;
- source channel and snapshot timestamp;
- rule ID and version through the containing signal.

Current emitted-signal `SignalEvidence` supports metric, numeric/null observed value, channel, and snapshot. It
does **not** support comparator, operator, unit, sample size, video identity, eligibility basis,
or canonical non-metric facts. This is a precise future contract gap, not authorization to add
generic JSON. Emitted-signal evidence should evolve only for the first approved rule, using the smallest typed
extension that satisfies that rule.

ADR-011 separately defines a policy-free `SignalEvidenceBundle` built from
`SubscriberRelativeAnalysisResult`. It exposes qualification and existing subscriber-relative
facts with typed availability, units, and shared provenance before rule evaluation. It does not
authorize a production rule, comparator, threshold, or expansion of emitted `SignalEvidence`.

## 15. Signal versioning policy

- Catalog v1 uses the `1.x` version line; editorial corrections increment the patch version.
- A threshold, operator, equality boundary, formula, missing-data behavior, sample rule, polarity,
  or intended interpretation change creates a new positive integer `rule_version`.
- Evidence additions that change reproducibility or downstream meaning create a new rule version;
  purely additive transport metadata may remain compatible after architecture review.
- Renaming display text does not change rule identity; changing machine identity or semantics does.
- Bug fixes that change emitted results require a new version and a documented correction window.
- Historical signals retain original rule ID/version and reason code. Re-evaluation creates new
  results; it does not overwrite historical meaning.
- Multiple rule versions may coexist only for migration/replay with explicit composition; a
  production policy set must identify its active version.
- Deprecated reason codes remain reserved and must not be reassigned.
- Persisted data migrations must preserve original input snapshot references and version fields.

## 16. Rule deprecation policy

A rule moves from Approved to Deprecated when its semantics are replaced, misleading, unsupported
by data, or no longer product-relevant. Deprecation requires a successor or explicit no-successor
decision, effective date, historical-query behavior, consumer migration plan, and reason-code
reservation. Deprecated rules stop new production emission after the stated policy-set change;
historical outputs remain interpretable.

## 17. AI narrative constraints

AI may translate an emitted signal and its evidence into user-facing prose. It must preserve the
metric, comparison, sample, time basis, source, limitations, and rule meaning. It must not:

- decide whether a signal exists;
- alter polarity or thresholds;
- infer causality, private analytics, subscriber growth, revenue, or future success;
- describe upload-cohort comparison as repeated-snapshot growth;
- hide missing data, approximate subscribers, or sample limitations;
- introduce facts absent from deterministic evidence.

## 18. Ranking boundary

Signal existence is independent from ranking. Ranking may later prioritize approved signals or
channels using an explicitly versioned cohort and scoring policy. A percentile is invalid without
a defined cohort, observation time, eligibility policy, and tie behavior. Ranking must consume
signals/analytics; it must not retroactively create, merge, or suppress rule outputs.

## 19. Open product decisions

1. Approve median standard-video VSR threshold `T` and validation evidence.
2. Approve hit-consistency share `P` and whether Bayesian adjustment belongs in metric or score.
3. Define breakout baseline and materiality.
4. Decide whether qualification failures are also emitted as Signals; the typed qualification
   result remains authoritative under ADR-010.
5. Decide whether future expected-channel-population coverage is required and define its
   denominator only if an authoritative source becomes available.
6. Approve a future Shorts classifier only when stronger official public facts are available.
7. Approve cohort identity/versioning and benchmark ownership.
8. Define repeated-snapshot velocity inputs and minimum history.
9. Decide whether upload-cohort signals provide enough product value to approve.
10. Approve emitted-signal evidence extensions only after threshold `T` is approved.
11. Define catalog approval workflow and record approver identities.

## 20. First implementable signal assessment

### Outcome C — Blocked by Missing Product Policy

The recommended first production signal is **SIG-002 High median subscriber-relative reach**.
It most directly serves the product objective, is robust against a single hit, is easy to explain,
and avoids misrepresenting upload-cohort comparison as growth. Its analytics prerequisites are
implemented, but the production rule is not currently implementable.

The prerequisite metric is `median_standard_video_vsr`:

```text
For each eligible standard video i:
    video_vsr_i = video_i.view_count / channel.statistics.subscriber_count

median_standard_video_vsr = median(video_vsr_i for all eligible standard videos)
```

Required inputs and rules:

- canonical public video view counts and current visible channel subscriber count;
- Eligible Video Policy v1 classifier with explicit standard basis;
- positive subscriber denominator; hidden, missing, or zero subscribers return unavailable rather
  than zero;
- one or more eligible standard videos for mathematical calculation; future qualification
  separately requires at least five;
- output `float | None`, where `None` means the ratio cannot be validly calculated;
- full precision without rounding in calculator or rule comparisons;
- `MedianStandardVideoVsrCalculator` ownership in deterministic analytics, with no signal
  threshold inside it.

Existing average/median views cannot substitute because they ignore subscriber scale. Views per
day cannot substitute because it measures age-normalized absolute reach. `view_growth_rate`
cannot substitute because it compares upload cohorts. The completed subscriber-relative pipeline
now provides the typed median standard-video VSR fact without applying signal policy.

Now that `median_standard_video_vsr` calculation exists, Product and Analytics must still approve
`T` and exact evidence/boundary semantics before SIG-002 becomes Approved and Implementable Now.

ADR-012 provides a deterministic offline capability for evaluating supplied historical snapshots
across explicitly versioned subscriber bands and `>` or `>=` threshold candidates. This capability
does not include a governed historical dataset, execute a study, select a candidate, recommend a
threshold, or change SIG-002 from **Proposed / Blocked**. Product and Analytics review remains the
only path to approving `T` and its equality boundary.

## 21. Recommended implementation sequence

1. Keep the implemented acquisition and subscriber-relative analytics pipelines unchanged.
2. Keep the ADR-011 typed evidence bundle policy-free and independent of signal thresholds.
3. Run the ADR-012 offline analysis on a governed historical dataset; Product and Analytics review
   the complete candidate report and approve threshold `T` plus its equality boundary.
4. Extend emitted `SignalEvidence` minimally for comparator, operator, unit, and sample size.
5. Mark SIG-002 Approved and Implementable Now with approval metadata.
6. Implement exactly one version-1 `SignalRule` and its boundary tests.
7. Consider hit consistency, Shorts, replay, and breakout only after the reference rule.
