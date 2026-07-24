# ADR-034: Establish the Evidence Manifest Domain Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## 1. Decision

Add an isolated `app.services.evidence_manifest` module containing one immutable,
schema-versioned `EvidenceManifest` value object and a stateless canonicalizer. A manifest declares
one exact ordered snapshot of Evidence Reference identities. It is neither evidence nor a container
for Evidence Reference objects or evidence payloads.

## 2. Product alignment

The Product Domain requires Candidates and future Opportunity work to retain explicit evidence
bases without treating references as evidence or silently changing historical facts. PD-012
authorizes the smallest snapshot boundary: immutable manifest identity/version, an ordered
non-empty Evidence Reference identity collection, explicit creation time, and optional descriptive
text. This foundation does not establish evidence sufficiency, relevance, quality, independence,
binding validity, provenance, or qualification. RQ-OPP-001 remains open.

## 3. Contract

Schema version 1 contains exactly:

- one canonical opaque manifest identity;
- one positive manifest version;
- one non-empty immutable tuple of unique Evidence Reference identities in supplied order;
- one timezone-aware creation timestamp normalized to UTC; and
- one optional bounded human-readable description, serialized explicitly as `null` when Unknown.

The manifest imports the canonical `EvidenceReferenceIdentifier` type but stores identities only.
It does not embed `EvidenceReference` objects. Reference order is part of manifest identity and is
never sorted. Duplicate references fail construction and are never deduplicated. Mutable
collections, timestamp strings, naive timestamps, and coercive version values are rejected.

## 4. Explicit exclusions

The contract contains no evidence payload, provenance, URL, metadata, analytics, qualification,
confidence, recommendation, lifecycle, score, AI output, discovery behavior, retrieval behavior,
or persistence behavior. It does not verify that a reference exists or that referenced content is
available, consistent, relevant, or valid evidence.

## 5. Determinism and canonical identity

Canonical serialization uses sorted object keys, compact separators, UTF-8, complete fields,
UTC-normalized timestamps, and no NaN. SHA-256 is calculated over the exact canonical bytes.
Frozen models and tuple collections provide recursive immutability, structural equality, and
Python hashability. SHA-256 remains the cross-runtime content identity.

## 6. Boundary and dependencies

The module may depend only on the Evidence Reference identity contract, Pydantic, and the standard
library. It has no dependency on Opportunity, Opportunity Candidate, YouTube acquisition,
analytics, signals, research, persistence, HTTP, FastAPI, SQLAlchemy, OpenAI, external APIs, or
application startup. No registry, repository, importer, validator, fetcher, service, API, clock, or
workflow is introduced.

## 7. Alternatives rejected

- Embedding complete `EvidenceReference` objects was rejected because the authorized snapshot owns
  their identities, not copies of pointer contracts.
- Sorting or stable-deduplicating references was rejected because either operation rewrites supplied
  snapshot identity.
- Adding a digest for each reference or evidence payload was rejected because content integrity and
  evidence validation are separate future concerns.
- Adding provenance, URLs, arbitrary metadata, or lifecycle state was rejected because those facts
  lie outside manifest membership identity.
- Reusing research or dataset manifests was rejected because they own different schemas, custody,
  integrity, and workflow meanings.

## 8. Compatibility and future work

This is an additive public Python contract with no database, API, configuration, dependency,
startup, deployment, or operational change. Reference existence/binding validation, manifest
registries, Candidate or Opportunity bindings, provenance, persistence, retrieval, content
integrity, replacement relationships, and qualification each require separately approved scope and
architectural review where material.

## 9. References

- [Product Domain Model](../../product/DOMAIN_MODEL.md)
- [Product Principles](../../product/PRODUCT_PRINCIPLES.md)
- [Opportunity Engine](../../product/OPPORTUNITY_ENGINE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md), RQ-OPP-001
- [Decision Log](../../product/DECISION_LOG.md), PD-012
- [Feature Registry](../../product/FEATURE_REGISTRY.md), EM-001
- ADR-001, ADR-029, ADR-032, ADR-033, and Engineering Principles EP-004/EP-006
