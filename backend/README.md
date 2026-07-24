# YT Signal Scout backend

## Setup

The backend targets Python 3.12. From the repository root:

```text
python -m pip install -r backend/requirements-dev.txt
```

Copy `backend/.env.example` values into your process environment as needed. The application
reads only the variables documented in `.env.example`. It does not load a `.env` file
implicitly.

`DEBUG` is validated and retained as application configuration, but HTTP traceback responses
remain disabled in every environment so internal exception details cannot reach clients.

## Run

```text
cd backend
python -m uvicorn app.main:app
```

Development OpenAPI documentation is available at `/docs`. Operational endpoints remain
outside API versioning:

- `GET /health/live` reports process and HTTP liveness.
- `GET /health/ready` reports bootstrap readiness. M1 has no external dependency checks.

Future product endpoints compose beneath `API_V1_PREFIX`, which defaults to `/api/v1`.

## Personal Creator Profile

`app.services.creator_profile` exposes the immutable schema-versioned Personal Creator Profile fact
contract approved by PD-008 and ADR-030. Optional self-declared preferences and constraints preserve
`None` as explicit Unknown; the module performs strict validation and stable compact UTF-8 JSON plus
SHA-256 canonicalization. It has no API, persistence, inference, clock, AI, feasibility,
personalization, filtering, or recommendation behavior.

## Canonical Opportunity

`app.services.opportunity` exposes the immutable schema-versioned Opportunity identity contract
approved by PD-009 and ADR-031. Every field is required; language and region use explicit tagged
known-or-unknown values. Strict validation, stable compact UTF-8 JSON, and SHA-256 content identity
are framework-independent and perform no discovery, evidence qualification, lifecycle transition,
classification, analytics, scoring, ranking, filtering, recommendation, persistence, or I/O.

## Opportunity Candidate

`app.services.opportunity_candidate` exposes the immutable schema-versioned pre-qualification
Candidate contract approved by PD-010 and ADR-032. It preserves opaque discovery-source, ordered
evidence-reference, UTC acquisition-time, and ordered provenance-reference facts using strict
validation, compact UTF-8 canonical JSON, and SHA-256 content identity. It has no dependency on
YouTube acquisition or canonical Opportunity models and performs no discovery, evidence validation,
qualification, lifecycle, interpretation, scoring, ranking, confidence, recommendation,
persistence, I/O, AI, or startup behavior.

## Evidence Reference

`app.services.evidence_reference` exposes the immutable schema-versioned canonical pointer approved
by PD-011 and ADR-033. Schema v1 identifies a YouTube channel or video using an opaque reference ID
and version plus an opaque source-object ID. Strict validation, compact sorted-key UTF-8 JSON, and
SHA-256 provide deterministic identity. The module contains no evidence payload, metadata,
provenance, timestamp, URL, retrieval, validation, discovery, analytics, interpretation,
qualification, scoring, confidence, recommendation, persistence, I/O, AI, or startup behavior.

## YouTube data acquisition

Set `YOUTUBE_API_KEY` before constructing a `YouTubeClient`. `YOUTUBE_TIMEOUT`,
`YOUTUBE_MAX_RETRIES`, and `YOUTUBE_PAGE_SIZE` control transport timeout, Google client retry
attempts, and the default bounded page size. The service uses only documented YouTube Data
API v3 endpoints and makes no API request until a service method is called.

The acquisition layer is under `app/services/youtube`. Instantiate `YouTubeClient` from the
application settings and inject it into `YouTubeService`; neither object is global or a
singleton. Tests inject a mock Google resource and never contact YouTube.

Video search and uploads-playlist responses are discovery inputs. `YouTubeService` extracts and
stably deduplicates their video IDs, requests complete `videos.list` resources, parses canonical
metadata, and reconstructs results in discovery order. Duplicate positions are retained using the
same immutable canonical object. A resource omitted by `videos.list` is skipped; omission alone is
not interpreted as deletion and never produces a placeholder.

Both video-acquisition paths return an immutable `VideoAcquisitionResult`. It retains resolved
discovery positions, a stable unique canonical-video collection, and typed population and
pagination provenance. Subscriber-relative analytics consume only the unique canonical videos.

## Test

```text
cd backend
python -m pytest
```

## Analytics calculator registry

`CalculatorRegistry` is the deterministic entry point for executing analytics calculators.
Callers inject calculators in the required execution order; the registry preserves that order,
rejects duplicate metric identities, and returns an immutable tuple of results. Calculator
failures propagate immediately and no partial result collection is returned.

## Analytics assembly

`AnalyticsAssembler` accepts metric results from any source, validates structural
completeness and uniqueness, and explicitly maps them into immutable
`CalculatedChannelAnalytics`. It does not execute calculators or interpret metric values.

## Subscriber-relative analytics

`SubscriberRelativeAnalyticsService.analyze(...)` is the public entry point for the separate
subscriber-relative execution path. It accepts a canonical `Channel`, a
`VideoAcquisitionResult`, and an explicit evaluation time. It constructs analytics from the
unique canonical videos, classifies them once, qualifies the dataset once, invokes each factual
calculator once, and delegates structural mapping to `SubscriberRelativeResultAssembler`.

The result is an immutable `SubscriberRelativeAnalysisResult` containing both
`SubscriberRelativeQualification` and factual `SubscriberRelativeAnalytics`. Calculators still
run for unqualified datasets; qualification determines downstream usability rather than whether
factual results exist. Normal qualification failures remain typed result values, while malformed
structural input fails validation.

This path does not use `CalculatorRegistry` or `AnalyticsAssembler`.

## Signal evidence

`SignalEvidenceBuilder` projects a `SubscriberRelativeAnalysisResult` into an immutable,
policy-free `SignalEvidenceBundle`. The bundle exposes qualification and existing analytics facts
with typed units, availability, evaluation time, and shared acquisition provenance. It performs
no threshold comparison, signal evaluation, ranking, or recommendation.

## Offline threshold research

`ChannelIntelligenceService` is the offline canonical boundary for channel-level research facts.
It verifies one immutable channel and ordered video tuple, reuses Eligible Video Policy v1, and
returns population, format, subscriber-relative, upload, distribution, and data-quality summaries
with source/result integrity. It performs no I/O or policy evaluation. See
[`CHANNEL_INTELLIGENCE_FORMAT.md`](../docs/engineering/CHANNEL_INTELLIGENCE_FORMAT.md) and ADR-028.

The `app/services/backtesting` package provides deterministic offline subscriber-band median-VSR
threshold analysis. It accepts immutable historical observations and explicitly versioned band
and candidate configurations, preserving structural failures and analytical exclusions as
separate outcomes. It produces factual `ThresholdBacktestReport` objects and never selects a
threshold or emits a signal.

Backtesting is not registered in application startup and has no API, acquisition, network,
persistence, or scheduled-execution integration.

External historical research data enters through the strict versioned-JSON
`HistoricalDatasetImporter`; successful import returns the existing immutable backtest dataset but
does not execute it. Schema version 2 requires immutable custody and collection provenance,
enforces the observation cutoff, verifies a canonical SHA-256 digest, and can emit stable canonical
JSON through `HistoricalDatasetCanonicalizer`. The schema and trust boundary are documented in
[`docs/engineering/HISTORICAL_DATASET_FORMAT.md`](../docs/engineering/HISTORICAL_DATASET_FORMAT.md).

Ground-truth research labels are a separate immutable boundary. `GroundTruthLabelImporter` loads
one strict dataset-bound label set containing only Positive, Negative, Borderline, and Unknown.
Every artifact has exactly two independent reviews; disagreement requires an independent later
adjudication. Evidence-pack and rubric versions/digests, supersession history, canonical ordering,
and SHA-256 integrity remain explicit. `GroundTruthLabelCanonicalizer` emits stable canonical JSON.
This framework does not create labels, calculate agreement or threshold metrics, or execute a
study. The format is documented in
[`docs/engineering/GROUND_TRUTH_LABEL_FORMAT.md`](../docs/engineering/GROUND_TRUTH_LABEL_FORMAT.md).

Reviewer evidence packs and labelling rubrics have their own strict schema-versioned import
boundaries. `EvidencePackImporter` and `RubricImporter` verify canonical SHA-256 digests and return
immutable typed documents; `GroundTruthLabelBindingValidator` verifies exact dataset, snapshot,
definition, pack, rubric, observation, and channel bindings without choosing a label. The
framework neither generates evidence nor runs a review workflow. See
[`docs/engineering/EVIDENCE_PACK_FORMAT.md`](../docs/engineering/EVIDENCE_PACK_FORMAT.md) and
[`docs/engineering/LABELLING_RUBRIC_FORMAT.md`](../docs/engineering/LABELLING_RUBRIC_FORMAT.md).

Governed study execution composes those imported artifacts with one historical dataset, one
ground-truth label set, and one version-pinned configuration. `StudyExecutionService` validates
complete cohort coverage and exact bindings and returns only an immutable canonical manifest; it
does not run threshold analysis or calculate research metrics. See
[`docs/engineering/STUDY_EXECUTION_FORMAT.md`](../docs/engineering/STUDY_EXECUTION_FORMAT.md) and
ADR-024.

`LabelledEvaluationService` consumes that completed execution together with its exact dataset,
Ground Truth Label Set, and one ordered supplied prediction per observation. It emits immutable
per-observation factual outcomes only. It never aggregates counts or calculates research metrics.
See
[`docs/engineering/LABELLED_EVALUATION_FORMAT.md`](../docs/engineering/LABELLED_EVALUATION_FORMAT.md)
and ADR-025.

`EvaluationAggregationService` consumes exactly one immutable labelled-evaluation result and emits
only six outcome counts plus Total Evaluated and Total Observations. Unknown contributes to Total
Evaluated; Not Evaluated does not. The service performs no division and exposes no percentage,
rate, statistical metric, threshold recommendation, or policy decision. See
[`docs/engineering/EVALUATION_AGGREGATION_FORMAT.md`](../docs/engineering/EVALUATION_AGGREGATION_FORMAT.md)
and ADR-026.

`StatisticalEvaluationService` consumes exactly one immutable aggregation result and calculates the
approved binary-classification metrics and five configured Wilson intervals using Decimal
arithmetic. Every metric is required, so any undefined denominator rejects the whole request. It
does not compare candidates or thresholds and contains no interpretation or recommendation. See
[`docs/engineering/STATISTICAL_EVALUATION_FORMAT.md`](../docs/engineering/STATISTICAL_EVALUATION_FORMAT.md)
and ADR-027.

The complete governed research chain and its negative-validation, canonicalization, mathematical,
export, exception, and dependency properties are reconciled in the
[`Research Architecture Stabilization Audit`](../docs/engineering/RESEARCH_ARCHITECTURE_STABILIZATION.md).
The audit executes synthetic fixtures only and adds no research or runtime capability.

`BacktestExecutionService` is the controlled synchronous execution boundary. It accepts one
validated import result and one versioned study configuration bound to that dataset, invokes the
existing backtester once, and returns immutable factual metadata with the report. Execution does
not choose thresholds, approve policy, generate signals, or participate in production startup.

Governed threshold research is represented by immutable `BacktestStudyArtifact` snapshots. A
versioned definition binds the study to an execution configuration; executed artifacts retain the
complete factual report, and typed reviews may approve or reject only the research artifact.
Study approval does not publish a threshold, authorize production policy, or activate a signal.

`ThresholdEvaluationMethodology` defines an ordered, versioned set of factual report concepts that
research evaluators may inspect and the closed research-only recommendations they may record. It
contains no weights, scores, calculated summary, ranking, threshold recommendation, or production
approval state.

`BacktestStudyEvaluation` records one immutable human evaluation of an executed study using one
methodology. It preserves the methodology's criterion order, records qualitative observation
status and notes, and uses the existing research-only recommendation vocabulary. It contains no
scores, weights, percentages, calculations, or production decision.

`ProductionPromotionPolicy` declaratively versions development-time release prerequisites. Its
typed requirements cover approved research status, exact methodology version, an approved
versioned Product Decision Record with effective release, and recorded Analytics and Architecture
release reviews. Human research evaluations may inform the Product decision but are not structural
promotion prerequisites. The policy neither determines eligibility nor contains, publishes,
registers, or activates a threshold.

`ProductionEligibilityAssessment` is an immutable factual snapshot binding one promotion policy,
one executed study, its governed evaluations, and one ordered satisfaction result per policy
requirement. Eligibility and failed requirement IDs must agree exactly with those results. The
assessment records no Product approval and cannot publish, register, activate, or execute a
threshold. It may be eligible when all release-governance results are satisfied.

Once an approved Product policy and conforming implementation are released, production evaluation
is deterministic and autonomous. No runtime human approval, review queue, research label, study
evaluation, or per-signal authorization participates in execution.

## Signal engine foundation

The `app/services/signals` module is the interpretation boundary after deterministic
analytics. `SignalRule` implementations consume the immutable analytics aggregate and emit
typed signals with structured metric evidence. `SignalEngine` only orchestrates an explicit
ordered rule sequence; it is synchronous, stateless, fail-fast, and returns a tuple.

There are currently no production rules. SIG-002 remains blocked until governed research
produces an explicitly approved production threshold policy. Any future production rule must use
approved, versioned policy and typed evidence; confidence scoring, composite scoring, and ranking
are outside the current release scope.
Proposed and approved definitions are governed in
[`docs/product/SIGNAL_CATALOG.md`](../docs/product/SIGNAL_CATALOG.md); catalog inclusion alone
does not authorize production composition.
