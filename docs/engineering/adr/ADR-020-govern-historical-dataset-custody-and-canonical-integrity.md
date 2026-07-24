# ADR-020: Govern Historical Dataset Custody and Canonical Integrity

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## Supersedes

The schema version 1 manifest defined by ADR-013 for new imports. ADR-013's strict-import,
all-or-nothing validation, offline boundary, and deterministic-ordering decisions remain accepted.

---

# 1. Decision Summary

Historical Dataset JSON schema version 2 extends the existing strict import boundary with immutable
custody, collection provenance, observation cutoff, known limitations, and a mandatory SHA-256
digest. The digest covers canonical UTF-8 JSON for the complete manifest except the digest itself
plus observations sorted by stable observation ID. Import validates temporal consistency,
observation cutoff, and digest integrity before returning the existing immutable backtest dataset.

# 2. Context

ADR-013 deliberately deferred factual custody and checksums. The SIG-002 Research Protocol now
requires source description, collection method and window, cutoff, creator, creation time, content
digest, algorithm, schema/dataset versions, and limitations. Schema version 1 cannot represent or
enforce those facts, and hashing original JSON bytes would make semantically identical formatting
produce different identities.

No historical dataset exists, so replacing schema version 1 for new imports does not require data
migration or compatibility with a committed artifact.

# 3. Alternatives Considered

## Preserve schema version 1 with optional metadata

Rejected because optional custody and integrity would permit future inputs that do not conform to
the canonical Research Protocol.

## Hash original file bytes

Rejected because whitespace, object-key order, and input observation order would change the digest
without changing governed facts.

## Hash only observations

Rejected because source, custody, cutoff, and limitations could then change without detection.

## Canonical schema version 2

Selected. It requires complete metadata and hashes normalized typed content while preserving the
existing importer, observation, dataset, and execution boundaries.

# 4. Contract

`HistoricalDatasetManifest` retains dataset and schema identities and embeds:

- `HistoricalDatasetCustody`: creator identity and timezone-aware creation time;
- `HistoricalDatasetProvenance`: source description, collection methodology, timezone-aware
  collection start/end, versioned selection methodology, observation cutoff, and ordered unique
  known limitations; and
- `HistoricalDatasetDigest`: closed `sha256` algorithm and lowercase 64-character digest.

Creation cannot precede collection end. Collection end cannot precede collection start or the
observation cutoff. Every observation timestamp must be at or before the cutoff.

# 5. Canonicalization and Integrity

Digest input is UTF-8 JSON with Unicode retained, no insignificant whitespace, lexicographically
sorted object keys, and observations sorted by stable observation ID. It includes the complete
manifest except `digest` and every serialized observation. Non-finite JSON numbers are prohibited.

`HistoricalDatasetCanonicalizer` calculates and validates the digest and serializes a successful
import result into canonical schema-versioned JSON. Equivalent input key and observation order
therefore produce identical canonical bytes. A mismatch raises a typed
`HistoricalDatasetDigestMismatchError`; no partial result is returned.

SHA-256 detects accidental or unauthorized content changes but does not authenticate the named
creator or prove upstream facts. Signatures and authenticated custody remain out of scope.

# 6. Versioning and Compatibility

The supported schema version becomes 2. Schema version identifies JSON compatibility; dataset ID
and dataset version identify the governed factual cohort. Any content or metadata change requires
a new dataset version and recomputed digest. The importer rejects schema version 1 rather than
presenting incomplete legacy metadata as protocol-conforming custody.

# 7. Boundary

This framework reads local supplied JSON only. It creates or collects no datasets, calls no API,
performs no research or threshold evaluation, labels no channel, and adds no persistence, API,
CLI, scheduler, AI, ranking, or production composition.

# 8. Consequences

Future dataset producers must supply complete custody and provenance and calculate canonical
digests. Import results become reproducible and tamper-evident at the content level. Schema version
1 fixtures must be updated, which is safe because no governed dataset exists.

# 9. Implementation Impact

Extends the existing backtesting import models, importer, public package exports, typed failures,
tests, historical format documentation, architecture, and navigation. Existing production and
backtest execution behavior is unchanged.

# 10. Future Revisit Criteria

Revisit if dataset custody requires digital signatures, authenticated creators, content-addressed
storage, streaming canonicalization, multiple digest algorithms, or complete canonical acquisition
snapshots from which analytics can be recomputed.

# 11. Related Decisions

ADR-010 through ADR-014 and the SIG-002 Research Protocol.
