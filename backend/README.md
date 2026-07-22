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

## Test

```text
cd backend
python -m unittest discover -s tests -v
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

## Signal engine foundation

The `app/services/signals` module is the interpretation boundary after deterministic
analytics. `SignalRule` implementations consume the immutable analytics aggregate and emit
typed signals with structured metric evidence. `SignalEngine` only orchestrates an explicit
ordered rule sequence; it is synchronous, stateless, fail-fast, and returns a tuple.

There are intentionally no production rules in this milestone. Product-approved taxonomy,
thresholds, and a defensible confidence calculation are required before those are added.
Proposed and approved definitions are governed in
[`docs/product/SIGNAL_CATALOG.md`](../docs/product/SIGNAL_CATALOG.md); catalog inclusion alone
does not authorize production composition.
