# YT Signal Scout — Signal Catalog v1

**Catalog version:** 1.0  
**Status:** Active — No production signals approved  
**Date:** 2026-07-22  
**Owners:** Product and Analytics  
**Architecture authority:** ADR-006 and ADR-007

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

## 4. Analytics inventory

All fields below are exposed by `CalculatedChannelAnalytics`. `source_dataset` is snapshot
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

### 4.1 Capability distinctions

- **Current aggregate performance:** average views, median views, views per day, and engagement
  rate describe the supplied snapshot only.
- **Upload-cohort comparison:** `view_growth_rate` compares newer and older uploads. It is not
  repeated-snapshot view growth.
- **Distribution:** view distribution, view outlier, and upload consistency summarize variation
  inside the supplied collection.
- **Repeated-snapshot growth:** not available.
- **Subscriber-relative performance:** not available as a calculated metric.
- **Benchmark-relative performance:** not available.
- **Ranking-relative performance:** not available.
- **Eligible-video population:** not available as an explicit validated dataset or count.

## 5. Product requirement mapping

Sources are the Product Requirements Document (PRD), Technical Requirements Document (TRD),
UI/UX Specification, Security Specification, and Feature Catalogue under
`docs/product/source/`.

| Product concept | Source | Classification | Finding |
|---|---|---|---|
| High views relative to subscriber base | PRD §§1, 5, 8.2; FR-SCO-001 | Requires new canonical metrics | Subscriber count exists, but per-video/aggregate VSR and eligibility do not |
| Median VSR | PRD §5 and §8.2 | Requires new canonical metric | Exact ratio concept is approved; aggregate metric is absent |
| Repeated video overperformance / hit consistency | PRD §5 and §8.2 | Requires new metrics | Approved component uses share of eligible videos with VSR `>= 1.0`; eligibility and VSR are absent |
| Breakout video | PRD §9; FR-ALT-001; Feature Catalogue E04 | Ambiguous product policy | Product intent exists, but “materially exceeds baseline” and baseline are undefined |
| Momentum score | PRD §8.2; TRD scoring sections | Requires cohort, snapshots, and ranking context | Components and weights are documented, but supporting cohort and history infrastructure are absent |
| Observed velocity / acceleration | PRD §§5, 8.2; FR-SCO-003 | Requires repeated snapshots | Current views-per-day and upload-cohort ratio cannot substitute for public view-count deltas |
| Consistent performance | PRD §8.2; FR-SCO-003 | Requires new metrics | Product consistency means repeated VSR overperformance, not upload schedule consistency |
| Upload consistency | Existing analytics only | Ambiguous product policy | Factual cadence metric exists but product discovery value and thresholds are not approved |
| Engagement | UI filters and current analytics | Requires external benchmark data | “Unusual” needs peer/format baseline plus eligible sample count |
| High views per day | Current analytics; related to PRD velocity intent | Partially supported | Metric exists, but it is lifetime age-normalized reach, not snapshot velocity; threshold/benchmark absent |
| Declining performance | General monitoring intent | Ambiguous product policy | Upload-cohort ratio exists, but naming, boundary, and minimum sample need approval |
| Cohort percentile | PRD §8.2 | Requires ranking/cohort context | Cohort definition is approved conceptually; no cohort service or values exist |
| Qualification / insufficient data | PRD §8.1; FR-SCO-002 | Requires eligibility analytics | Gates are explicit, but current source videos are not proven eligible and retrieval completeness is absent |
| Confidence | PRD §8.3 | Requires new metrics and snapshots | Conditions are documented; current aggregate lacks eligible counts, completeness, anomaly state, and history |
| Hidden subscriber handling | PRD guardrail GR-01 and §9 | Supported canonically, not analytically | Canonical channel retains hidden state; no VSR pipeline consumes it yet |
| Stale snapshot | General traceability requirement | Ambiguous product policy | Timestamp exists; maximum acceptable age and evaluation clock policy are undefined |

## 6. Signal catalog schema

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

## 7. Candidate signal catalog

### SIG-001 — Sustained subscriber-relative overperformance

**Identity:** `RuleId=discovery.sustained_subscriber_relative_overperformance`;
`SignalType=discovery.sustained_subscriber_relative_overperformance`;
`ReasonCode=discovery.consistent_vsr_at_or_above_one`; name “Sustained subscriber-relative
overperformance”; version 1; **Blocked**.

**Business meaning:** Answers whether a channel repeatedly earns at least as many views per
eligible video as its visible subscriber count. It supports discovery analysts. It does not mean
subscriber growth, revenue, audience quality, or guaranteed future performance.

**Inputs:** Per-video VSR, eligible-video count, qualifying-hit count, format classification,
visible non-zero subscriber count, snapshot provenance; no benchmark or history. Minimum five
eligible videos under PRD §8.1; missing/hidden/zero subscribers or fewer than five eligible
videos emit no signal and produce qualification state outside this rule.

**Deterministic policy:** Emit when `qualifying_hit_count / eligible_video_count >= P`, where a
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

**Dependencies:** New per-video VSR and hit-consistency metrics; eligibility policy/calculator;
no benchmark, history, or ranking service.

**Approval:** Product must approve `P`; Analytics must approve eligibility and ratio semantics;
Architecture reviews evidence evolution. Not implementable now.

### SIG-002 — High median subscriber-relative reach

**Identity:** `RuleId=discovery.high_median_vsr`; `SignalType=discovery.high_median_vsr`;
`ReasonCode=discovery.median_vsr_above_policy_threshold`; name “High median subscriber-relative
reach”; version 1; **Blocked**.

**Business meaning:** Answers whether the typical eligible recent video materially outperforms
the channel's subscriber scale. It is a core discovery signal, not a growth rate or cohort rank.

**Inputs:** Median eligible-video VSR, eligible count, visible positive subscribers, format and
age eligibility; no snapshots. Minimum five eligible videos. Missing/hidden/zero subscriber
count or insufficient sample emits no signal.

**Deterministic policy:** Emit when `median_vsr >= T`. `T` is **Not yet defined**; equality is
included in the proposed operator. No rounding before comparison. Zero or one; may coexist with
SIG-001 and SIG-003.

**Signal output:** Positive. Evidence: median VSR, observed ratio, `T`, `>=`, ratio unit, sample
count, subscriber count, channel/snapshot, rule version. Current evidence has the same comparison
and sample gaps described in SIG-001.

**Explanation contract:** Say “typical eligible recent video views relative to current public
subscribers.” Prohibit “subscriber growth,” “audience conversion,” and unqualified “viral.” AI
must retain eligibility window, format, sample, and approximate-subscriber caveats.

**Limitations:** Same-time denominator, rounded subscribers, video-age exposure, format mixing,
and traffic-source ambiguity. Median reduces but does not eliminate selection bias.

**Dependencies:** New median VSR and eligibility metrics. Product and Analytics must approve `T`
through cohort percentile analysis, labelled-channel review, and sensitivity testing. Not ready.

**Approval:** Product approves `T` and intended interpretation; Analytics approves eligibility,
denominator, and validation method; Architecture reviews evidence evolution. Not implementable now.

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
age exposure, and format mixing. Current z-score extrema are not approved significance tests.

**Dependencies:** Eligibility, baseline policy, possibly VSR/velocity and richer evidence. Product
and Analytics approval required; architecture unchanged unless evidence contract evolves.

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

**Inputs:** Eligible-video count and exclusion reasons, retrieval completeness, visible subscriber
state. Minimum five eligible videos is **Explicitly defined in existing requirements** (PRD §8.1).

**Deterministic policy:** Emit informational signal when `eligible_video_count < 5`; equality at
five emits none. Count comparison uses integers without rounding. Missing eligibility calculation
is a pipeline failure, not zero. Zero or one; may coexist with missing-subscriber qualification
state if product approves multiple reasons.

**Signal output:** Informational with observed count, threshold five, `<`, video-count unit,
exclusion summary, source/provenance. Current evidence lacks comparator, unit, and exclusion/sample
structure.

**Explanation contract:** “Fewer than five videos met the approved eligibility policy.” Prohibit
“poor performance” or claims that the channel has fewer than five total videos. AI may explain
exclusion facts only.

**Limitations:** Correctness depends entirely on explicit format, age, privacy, deletion, and
retrieval rules. Incomplete acquisition may cause false insufficiency.

**Dependencies:** Eligible-video classifier/count and retrieval completeness. Product eligibility
policy exists in outline but implementation details need Analytics approval. Not ready.

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

## 8. Approved signals

None. Existing requirements approve several component definitions and qualification boundaries,
but no complete catalog entry has all semantics, inputs, evidence, and approvals needed for a
production `SignalRule`.

## 9. Implementable-now signals

None. SIG-004 and SIG-008 use an existing metric, but materiality, minimum sample, infinity
handling, and evidence comparison fields remain unresolved. They are proposals, not production
policy.

## 10. Blocked signals

| Signal | Primary blocker |
|---|---|
| SIG-001 | Hit-consistency metric, eligible-video basis, and approved share threshold |
| SIG-002 | Median VSR metric, eligibility, and approved threshold |
| SIG-003 | Approved breakout baseline and significance policy |
| SIG-005 | Eligible sample evidence and cohort benchmark |
| SIG-006 | Cohort benchmark and eligibility/sample evidence |
| SIG-010 | Eligible-video classifier/count and evidence shape |
| SIG-011 | Decision on qualification-result boundary and canonical-fact evidence |

Deferred supporting signals SIG-007, SIG-009, and SIG-012 should not displace core discovery
work. Proposed SIG-004 and SIG-008 require approval and validation.

## 11. Rejected signals and designs

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

## 12. Threshold governance

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

## 13. Evidence standards

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

Current `SignalEvidence` supports metric, numeric/null observed value, channel, and snapshot. It
does **not** support comparator, operator, unit, sample size, video identity, eligibility basis,
or canonical non-metric facts. This is a precise future contract gap, not authorization to add
generic JSON. Evidence should evolve only for the first approved rule, using the smallest typed
extension that satisfies that rule.

## 14. Signal versioning policy

- Catalog v1 uses document version `1.0`; editorial corrections increment the patch version.
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

## 15. Rule deprecation policy

A rule moves from Approved to Deprecated when its semantics are replaced, misleading, unsupported
by data, or no longer product-relevant. Deprecation requires a successor or explicit no-successor
decision, effective date, historical-query behavior, consumer migration plan, and reason-code
reservation. Deprecated rules stop new production emission after the stated policy-set change;
historical outputs remain interpretable.

## 16. AI narrative constraints

AI may translate an emitted signal and its evidence into user-facing prose. It must preserve the
metric, comparison, sample, time basis, source, limitations, and rule meaning. It must not:

- decide whether a signal exists;
- alter polarity or thresholds;
- infer causality, private analytics, subscriber growth, revenue, or future success;
- describe upload-cohort comparison as repeated-snapshot growth;
- hide missing data, approximate subscribers, or sample limitations;
- introduce facts absent from deterministic evidence.

## 17. Ranking boundary

Signal existence is independent from ranking. Ranking may later prioritize approved signals or
channels using an explicitly versioned cohort and scoring policy. A percentile is invalid without
a defined cohort, observation time, eligibility policy, and tie behavior. Ranking must consume
signals/analytics; it must not retroactively create, merge, or suppress rule outputs.

## 18. Open product decisions

1. Approve eligible-video rules: public status, age 24–90 days, format separation, deletion,
   livestream replay, retrieval completeness, and sample ownership.
2. Approve median VSR threshold strategy and subscriber-band/rounding behavior.
3. Approve hit-consistency share `P` and whether Bayesian adjustment belongs in the metric or score.
4. Define breakout baseline and materiality.
5. Decide whether qualification outcomes are Signals or a separate typed qualification result.
6. Approve cohort identity/versioning and benchmark ownership.
7. Define repeated-snapshot velocity inputs and minimum history.
8. Decide whether upload-cohort signals provide enough product value to approve.
9. Approve evidence extensions only after choosing the first rule.
10. Define catalog approval workflow and record Product/Analytics approver identities.

## 19. First implementable signal assessment

### Outcome C — Blocked by Missing Analytics

The recommended first production signal is **SIG-002 High median subscriber-relative reach**.
It most directly serves the product objective, is robust against a single hit, is easy to explain,
and avoids misrepresenting upload-cohort comparison as growth. It is not currently implementable.

The prerequisite metric is `median_vsr`:

```text
For each eligible video i:
    video_vsr_i = video_i.view_count / channel.subscriber_count

median_vsr = median(video_vsr_i for all eligible videos)
```

Required inputs and rules:

- canonical public video view counts and current visible channel subscriber count;
- explicit eligible-video classifier with format separation and approved age window;
- positive subscriber denominator; hidden, missing, or zero subscribers return unavailable rather
  than zero;
- minimum five eligible videos, as explicitly required by PRD §8.1;
- output `float | None`, where `None` means the ratio cannot be validly calculated;
- full precision without rounding in calculator or rule comparisons;
- `MedianVsrCalculator` ownership in deterministic analytics, with no signal threshold inside it.

Existing average/median views cannot substitute because they ignore subscriber scale. Views per
day cannot substitute because it measures age-normalized absolute reach. `view_growth_rate`
cannot substitute because it compares upload cohorts. No current metric answers the core product
question.

After `median_vsr` exists, Product and Analytics must approve `T` and exact evidence/boundary
semantics before SIG-002 becomes Approved and Implementable Now.

## 20. Recommended implementation sequence

1. Approve eligible-video and subscriber-denominator policy.
2. Implement an immutable eligible-video basis and deterministic `median_vsr` calculator/aggregate
   field, with ADR review if the eligibility boundary is material.
3. Backtest median VSR by content format and subscriber band; approve threshold `T`.
4. Extend `SignalEvidence` minimally for comparator, operator, unit, and sample size.
5. Mark SIG-002 Approved and Implementable Now with approval metadata.
6. Implement exactly one version-1 `SignalRule` and its boundary tests.
7. Consider hit consistency and breakout only after the reference rule is validated.
