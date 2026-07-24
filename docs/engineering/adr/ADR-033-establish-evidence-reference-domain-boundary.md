# ADR-033: Establish the Evidence Reference Domain Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## 1. Decision

Add an isolated `app.services.evidence_reference` module containing one immutable,
schema-versioned `EvidenceReference` value object, closed evidence-object and source-platform
vocabularies, strict validation, and a stateless canonicalizer. The object is a canonical pointer
only; it does not contain, retrieve, validate, bind, qualify, or interpret evidence.

## 2. Product alignment

The Product Domain defines Evidence as a traceable fact or governed research result and requires
Candidates to accumulate evidence without claiming qualification. PD-011 authorizes a minimal
identity boundary that later governed systems may reference without importing payloads or the
modules that own them. This foundation does not define evidence sufficiency, relevance, quality,
independence, provenance, or Candidate qualification. RQ-OPP-001 remains open.

## 3. Contract

Schema version 1 contains exactly:

- one canonical opaque Evidence Reference identity;
- one positive Evidence version;
- one closed evidence-object type: `channel` or `video`;
- one closed source platform: `youtube`; and
- one opaque source-object identity.

Every field is required. Reference and source-object identities are non-empty, canonical strings
and must be distinct. Schema and evidence versions reject Boolean, floating-point, string, zero,
and negative values. Shape and enum validation does not assert that a source object exists, matches
the declared type, is accessible, or qualifies as evidence.

## 4. Explicit exclusions

The contract contains no evidence payload, metadata, analytics, score, confidence, qualification,
recommendation, lifecycle, AI output, provenance, timestamp, URL, or discovery behavior. It has no
fetcher, validator, repository, registry, API, clock, service, workflow, or conversion behavior.

## 5. Determinism and canonical identity

Canonical serialization uses sorted object keys, compact separators, UTF-8, complete fields, and
no NaN. SHA-256 is calculated over the exact canonical bytes. The frozen value object provides
structural equality and Python hashability; SHA-256 remains the cross-runtime content identity.

## 6. Boundary and dependencies

The package depends only on the standard library and Pydantic. It has no dependency on Opportunity,
Opportunity Candidate, YouTube acquisition, research, analytics, signals, persistence, HTTP,
FastAPI, SQLAlchemy, OpenAI, external APIs, or application startup. It deliberately duplicates its
small closed identity vocabulary rather than importing a model owned by another boundary.

## 7. Alternatives rejected

- Embedding evidence payloads or metadata was rejected because the reference is identity, not
  evidence storage.
- Reusing YouTube, Candidate, Opportunity, signal-evidence, or research evidence-pack models was
  rejected because each owns different facts and behavior.
- Adding provenance, timestamps, URLs, or digests for the pointed-to content was rejected because
  those describe custody, transport, or evidence integrity rather than pointer identity.
- A generic free-form type or platform string was rejected because it weakens schema governance.
- Adding observation, study, signal, or arbitrary evidence types was rejected because schema v1 is
  limited to the established YouTube source objects authorized for this foundation.

## 8. Compatibility and future work

This is an additive public Python contract with no database, API, configuration, dependency,
startup, deployment, or operational change. Future types, non-YouTube platforms, typed Candidate
integration, evidence registries, payload retrieval, binding/integrity validation, provenance,
persistence, and qualification each require separately approved scope and architectural review
where material.

## 9. References

- [Product Domain Model](../../product/DOMAIN_MODEL.md)
- [Product Principles](../../product/PRODUCT_PRINCIPLES.md)
- [Opportunity Engine](../../product/OPPORTUNITY_ENGINE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md), RQ-OPP-001
- [Decision Log](../../product/DECISION_LOG.md), PD-011
- [Feature Registry](../../product/FEATURE_REGISTRY.md), ER-001
- ADR-001, ADR-029, ADR-031, ADR-032, and Engineering Principles EP-004/EP-006
