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

The `app/services/backtesting` package provides deterministic offline subscriber-band median-VSR
threshold analysis. It accepts immutable historical observations and explicitly versioned band
and candidate configurations, preserving structural failures and analytical exclusions as
separate outcomes. It produces factual `ThresholdBacktestReport` objects and never selects a
threshold or emits a signal.

Backtesting is not registered in application startup and has no API, acquisition, network,
persistence, or scheduled-execution integration.

External historical research data enters through the strict versioned-JSON
`HistoricalDatasetImporter`; successful import returns the existing immutable backtest dataset but
does not execute it. The schema and trust boundary are documented in
[`docs/engineering/HISTORICAL_DATASET_FORMAT.md`](../docs/engineering/HISTORICAL_DATASET_FORMAT.md).

`BacktestExecutionService` is the controlled synchronous execution boundary. It accepts one
validated import result and one versioned study configuration bound to that dataset, invokes the
existing backtester once, and returns immutable factual metadata with the report. Execution does
not choose thresholds, approve policy, generate signals, or participate in production startup.

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
