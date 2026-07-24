# Historical Dataset JSON Format

Historical subscriber-relative research data uses strict JSON schema version 2 and enters only
through `HistoricalDatasetImporter`. CSV, unversioned JSON, schema version 1, unknown fields,
coercive values, and direct dictionary ingestion are not supported.

## Document shape

```json
{
  "manifest": {
    "schema_version": 2,
    "dataset_id": "research-dataset-v1",
    "dataset_version": 1,
    "custody": {
      "creator_identity": "analytics-owner",
      "created_at": "2026-07-24T12:00:00Z"
    },
    "provenance": {
      "source_description": "Governed historical channel snapshots",
      "collection_methodology": "Versioned bounded collection procedure",
      "selection_methodology_id": "selection-v1",
      "selection_methodology_version": 1,
      "collection_started_at": "2026-07-23T12:00:00Z",
      "collection_ended_at": "2026-07-24T11:00:00Z",
      "observation_cutoff": "2026-07-24T10:00:00Z",
      "known_limitations": ["Query-bounded discovery"]
    },
    "digest": {
      "algorithm": "sha256",
      "value": "<64 lowercase hexadecimal characters>"
    }
  },
  "observations": []
}
```

`observations` contains serialized `SubscriberRelativeBacktestObservation` objects. Each record
requires:

- `observation_id`: stable lowercase machine identifier;
- `channel_id`: non-empty canonical channel identity;
- `observed_at`: timezone-aware ISO 8601 timestamp at or before the manifest cutoff;
- `subscriber_count`: positive JSON integer; and
- `analysis`: complete serialized `SubscriberRelativeAnalysisResult`, including qualification,
  acquisition provenance, factual analytics, and evaluation time.

Schema version governs JSON compatibility. Dataset ID and positive dataset version identify the
factual cohort. Changing any manifest fact or observation requires a new dataset version and
digest.

## Custody and provenance

Custody records who created the dataset version and when. Provenance records its source,
collection method, versioned selection methodology, collection window, observation cutoff, and
ordered known limitations. Every timestamp is timezone-aware. Collection end must not precede
collection start or cutoff, and dataset creation must not precede collection end. Known
limitations are ordered and unique.

These fields preserve supplied custody claims; they do not authenticate the creator or prove that
upstream facts are true.

## Canonical serialization and digest

The mandatory digest algorithm is SHA-256. Digest input is canonical UTF-8 JSON containing:

1. the complete manifest except its `digest` field; and
2. every observation sorted by `observation_id`.

Canonical JSON retains Unicode, sorts every object key lexicographically, uses no insignificant
whitespace, and rejects non-finite numbers. Original whitespace, object-key order, and observation
order therefore do not affect the digest.

`HistoricalDatasetCanonicalizer.calculate_digest(...)` calculates the required lowercase digest.
`serialize_import_result(...)` returns canonical bytes for an already validated import result.
Digest mismatch is a typed validation failure and returns no partial dataset.

## Validation

The importer:

- accepts only schema version `2`;
- rejects missing and unknown fields at every nested model boundary;
- uses strict JSON validation without primitive coercion;
- validates timezone and collection/custody ordering;
- rejects observations after the manifest cutoff;
- requires timestamp, channel, subscriber state, provenance, and eligible-count consistency;
- rejects duplicate observation IDs and duplicate channel/timestamp snapshots;
- verifies the canonical SHA-256 digest;
- returns observations sorted by `observation_id`; and
- returns no partial dataset after any error.

Typed errors distinguish file reads, JSON syntax, unsupported schema versions, structural
validation, duplicates, and digest mismatches. Error messages do not include raw input values.

## Trust boundary

Successful import proves schema consistency, domain consistency, declared metadata completeness,
and content integrity relative to the supplied digest. It does not prove factual truth,
authenticate custody, or establish representative sampling. Dataset owners remain responsible for
source custody and Research Protocol conformance.

The importer never calls YouTube, creates data, runs analytics, executes a backtest, labels a
channel, writes persistence, or changes Product policy.

## Programmatic use

```python
from app.services.backtesting import (
    HistoricalDatasetCanonicalizer,
    HistoricalDatasetImporter,
)

result = HistoricalDatasetImporter().import_file("historical-dataset.json")
canonical_bytes = HistoricalDatasetCanonicalizer.serialize_import_result(result)
dataset = result.dataset
```

Import and canonical serialization do not execute research or write output.

See ADR-013 for the original strict import boundary and ADR-020 for schema version 2 custody and
canonical integrity.
