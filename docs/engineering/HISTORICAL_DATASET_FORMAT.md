# Historical Dataset JSON Format

Historical subscriber-relative research data uses strict JSON schema version 1 and must be loaded
through `HistoricalDatasetImporter`. CSV, unversioned JSON, and direct dictionary ingestion are
not supported.

## Document shape

```json
{
  "manifest": {
    "schema_version": 1,
    "dataset_id": "research-dataset-v1",
    "dataset_version": 1
  },
  "observations": []
}
```

`observations` contains serialized `SubscriberRelativeBacktestObservation` objects. Each record
requires:

- `observation_id`: stable lowercase machine identifier;
- `channel_id`: non-empty canonical channel identity;
- `observed_at`: timezone-aware ISO 8601 timestamp;
- `subscriber_count`: positive JSON integer;
- `analysis`: the complete serialized `SubscriberRelativeAnalysisResult`, including qualification,
  acquisition provenance, factual analytics, and evaluation time.

The manifest dataset identity/version becomes the imported
`SubscriberRelativeBacktestDataset` identity/version. Dataset schema version and dataset version
are different: the former governs JSON compatibility; the latter identifies the research cohort.

## Validation

The importer:

- accepts only schema version `1`;
- rejects missing and unknown fields at every nested model boundary;
- uses strict JSON validation and does not coerce strings into numeric values;
- requires timestamp, channel, subscriber state, provenance, and eligible-count consistency from
  the existing observation contract;
- rejects duplicate observation IDs and duplicate channel/timestamp snapshots;
- returns observations sorted by `observation_id`;
- returns no partial dataset after any error.

JSON object-key order and input observation order have no effect on the imported result.

## Trust boundary

Successful import proves schema and domain consistency, not factual truth. Dataset owners remain
responsible for source custody and for demonstrating that serialized facts came from an approved
historical collection process. The importer never calls YouTube or recomputes analytics.

## Programmatic use

```python
from app.services.backtesting import HistoricalDatasetImporter

result = HistoricalDatasetImporter().import_file("historical-dataset.json")
dataset = result.dataset
```

Import does not execute a backtest or write output.
