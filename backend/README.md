# YT Signal Scout backend

## Setup

The backend targets Python 3.12. From the repository root:

```text
python -m pip install -r backend/requirements-dev.txt
```

Copy `backend/.env.example` values into your process environment as needed. The application
reads only `APP_NAME`, `APP_VERSION`, `ENVIRONMENT`, `DEBUG`, `API_V1_PREFIX`, and `LOG_LEVEL`.
It does not load a `.env` file implicitly.

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

## Test

```text
cd backend
python -m unittest discover -s tests -v
```
