# ADR-013: Govern Historical Research Dataset Import Through Strict Versioned JSON

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision extends the ADR-012 offline research boundary.

---

# 1. Decision Summary

Historical subscriber-relative research data enters the repository through one strict,
schema-versioned JSON importer inside `services/backtesting`. The importer validates a manifest
and serialized existing `SubscriberRelativeBacktestObservation` records, rejects malformed or
unknown input, canonicalizes observation order, and returns an immutable import result containing
the existing backtest dataset contract.

# 2. Context

ADR-012 defines immutable historical observations and datasets but no governed external boundary.
Directly loading arbitrary dictionaries would permit coercion, ignored fields, inconsistent
schema evolution, and nondeterministic duplicate handling. The repository also does not retain a
complete historical canonical acquisition snapshot from which the importer could safely rerun the
production analytics pipeline.

# 3. Alternatives Considered

## Recompute from complete canonical historical acquisition facts

Preferred when such snapshots exist because derived values can be reproduced through production
services. Rejected for this milestone because no complete historical snapshot contract or dataset
exists, and importer scope expressly excludes invoking acquisition, classification, qualification,
or analytics.

## Accept a versioned serialized analysis observation

Selected. It reuses the existing immutable observation and nested analysis contracts, applies
strict recursive validation, and avoids duplicating calculator or qualification logic. Structural
validation does not establish that external facts are true; dataset sourcing and review remain a
governance responsibility.

## JSON Lines or CSV

JSON Lines adds separate manifest and stream coordination without a demonstrated dataset-size
need. CSV cannot represent nested typed provenance without heuristic encoding. Both are rejected
for schema version 1.

# 4. Import Contract

Schema version 1 is one JSON object with:

```text
manifest
    schema_version = 1
    dataset_id
    dataset_version
observations
    tuple of serialized SubscriberRelativeBacktestObservation values
```

Unknown fields, missing fields, coercive primitive substitutions, invalid timestamps, invalid
identifiers, contradictory nested analysis, duplicate observation IDs, and duplicate
channel/timestamp snapshots fail import. No record is skipped and no partial result is returned.

# 5. Ordering and Errors

Successful imports sort observations by stable observation ID. Equal input facts therefore yield
equal datasets independent of JSON object-key order or record order. Typed failures distinguish
file reads, JSON syntax, unsupported schema versions, structural validation, and duplicates.
Validation messages omit raw input values.

# 6. Boundary

The importer is offline only. It is not registered in application startup and does not call the
YouTube API, analytics, qualification, evidence construction, signals, FastAPI, persistence, or
backtest execution. Backtesting consumes only the immutable imported dataset selected by an
offline caller in a later milestone.

# 7. Consequences

The repository gains a deterministic external schema and explicit evolution point without a new
dependency. Schema changes require a new supported version and compatibility decision. Factual
trust, dataset custody, checksums, study execution, and review status remain future governance
work.

# 8. Implementation Impact

Adds importer contracts, a strict JSON importer, typed import errors, tests, and format
documentation under the existing offline research boundary. No production contract changes.

# 9. Future Revisit Criteria

Revisit when complete canonical historical snapshots support safe recalculation, dataset size
justifies streaming, or research governance requires checksums and custody metadata.

# 10. Related ADRs

ADR-008, ADR-010, ADR-011, and ADR-012.
