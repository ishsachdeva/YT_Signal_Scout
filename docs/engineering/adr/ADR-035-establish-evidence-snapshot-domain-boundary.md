# ADR-035: Establish the Integrity-Pinned Evidence Snapshot Domain Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## 1. Decision

Add an isolated `app.services.evidence_snapshot` module containing one immutable,
schema-versioned `EvidenceSnapshot` value object and a stateless canonicalizer. A snapshot binds
its own identity/version to exactly one Evidence Manifest identity, version, and supplied canonical
SHA-256 digest at one explicit designation instant. It stores neither the manifest nor its Evidence
References.

## 2. Product alignment

The Product Domain requires future qualification and research to remain reproducible without
turning identity artifacts into evidence or policy. PD-013 authorizes a minimal versioned binding
that integrity-pins which canonical immutable manifest representation a later governed process
refers to without requiring an identity/version registry. Snapshot construction records the
supplied digest but does not calculate or verify it and does not establish manifest existence,
relevance, sufficiency, quality, provenance, or qualification. RQ-OPP-001 remains open.

## 3. Contract

Schema version 1 contains exactly:

- one canonical opaque snapshot identity;
- one positive snapshot version;
- one canonical opaque Evidence Manifest identity;
- one positive manifest version;
- one strict lower-case 64-character hexadecimal SHA-256 digest of the selected canonical manifest
  bytes;
- one timezone-aware designation timestamp normalized to UTC; and
- one optional bounded human-readable description, serialized explicitly as `null` when Unknown.

The snapshot imports only `EvidenceManifestIdentifier`. It does not import or embed an
`EvidenceManifest`. Schema, snapshot, and manifest versions reject Boolean, floating-point, string,
zero, and negative values. The manifest digest rejects upper/mixed case, non-hexadecimal content,
wrong lengths, padding, and every non-string type. Timestamp strings and naive datetimes are
rejected.

`snapshot_timestamp` is the instant at which the exact manifest identity, version, and digest were
designated as the evidence basis for a downstream activity. It is not evidence publication or
observation time, retrieval time, manifest creation time, qualification execution time, or
persistence time.

## 4. Explicit exclusions

The contract contains no evidence payload, Evidence References, manifest object, URL, provenance,
metadata, analytics, qualification, recommendation, lifecycle, confidence, AI output, discovery,
retrieval, or persistence behavior. It neither loads nor validates the bound manifest and never
calculates or verifies `manifest_digest`.

## 5. Determinism and canonical identity

Canonical serialization includes the supplied manifest digest and uses sorted object keys, compact separators, UTF-8, complete fields,
UTC-normalized timestamps, and no NaN. SHA-256 is calculated over the exact canonical bytes. The
frozen value object provides structural equality and Python hashability; SHA-256 remains the
cross-runtime content identity.

## 6. Boundary and dependencies

The module may depend only on the Evidence Manifest identifier type, Pydantic, and the standard
library. It has no dependency on Evidence Reference, Opportunity, Opportunity Candidate,
analytics, signals, research, persistence, HTTP, FastAPI, SQLAlchemy, OpenAI, external APIs, or
application startup. No repository, importer, validator, resolver, fetcher, service, API, clock,
registry, or workflow is introduced.

## 7. Alternatives rejected

- Embedding an `EvidenceManifest` was rejected because the snapshot owns only an identity/version
  and digest binding.
- Including Evidence Reference identities was rejected because manifest membership belongs to the
  manifest boundary.
- Calculating or verifying the manifest digest was rejected because the Snapshot accepts no
  manifest object and owns recording, not integrity validation.
- Adding provenance, URLs, metadata, or qualification status was rejected because those facts lie
  outside snapshot identity.
- Reusing research evidence snapshots was rejected because they own evidence payload, dataset
  binding, and research-specific semantics.

## 8. Compatibility and future work

This is an additive public Python contract with no database, API, configuration, dependency,
startup, deployment, or operational change. Manifest lookup, digest verification,
registries, Candidate/Opportunity binding, research inputs, qualification inputs, provenance,
persistence, retrieval, replacement relationships, and retention each require separately approved
scope and architectural review where material.

## 9. References

- [Product Domain Model](../../product/DOMAIN_MODEL.md)
- [Product Principles](../../product/PRODUCT_PRINCIPLES.md)
- [Opportunity Engine](../../product/OPPORTUNITY_ENGINE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md), RQ-OPP-001
- [Decision Log](../../product/DECISION_LOG.md), PD-013
- [Feature Registry](../../product/FEATURE_REGISTRY.md), ES-001
- ADR-001, ADR-029, ADR-033, ADR-034, and Engineering Principles EP-004/EP-006
