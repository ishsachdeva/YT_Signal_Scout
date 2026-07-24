# ADR-031: Establish the Canonical Opportunity Domain Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## 1. Decision

Add an isolated `app.services.opportunity` module containing an immutable schema-versioned
`Opportunity` value object, explicit known/unknown context values, strict validation, and a
stateless canonicalizer. The module represents only canonical business identity authorized by
PD-009.

It contains no discovery, evidence validation, qualification, lifecycle transition, classification,
analytics, heuristics, filtering, scoring, ranking, quality/confidence assessment, recommendation,
AI, HTTP, persistence, or external integration.

## 2. Product alignment

The Domain Model defines Opportunity as a versioned bounded market proposition and the platform's
primary Product asset. Channels and videos are evidence; Creator Profiles contextualize later
recommendations. Accordingly, none of those identities is embedded in canonical Opportunity
identity. Construction does not prove that a proposition meets the future qualification policy;
only an approved upstream boundary may create this Product object later.

RQ-OPP-001 and lifecycle research remain open. This foundation does not answer them.

## 3. Contract

Schema version 1 contains:

- a canonical opaque Opportunity ID and positive Opportunity version;
- distinct opaque Market and Niche IDs;
- source platform fixed to the closed `youtube` vocabulary;
- an exact non-empty bounded proposition with canonical surrounding-whitespace rules; and
- required language and region values represented by a discriminated `known` or `unknown` state.

Unknown is never an empty string, `None`, guessed value, or default. Known values are non-empty and
canonical. Identifier values are non-empty, lower-case, structurally validated, and pairwise unique.
Boolean or coercible numeric versions are rejected.

## 4. Canonicalization and hashing

Canonical JSON uses UTF-8, sorted keys, compact separators, explicit tagged unknown states, and no
NaN. SHA-256 provides content identity over the exact canonical bytes. The frozen, recursively
immutable object also supports structural equality and Python hashing within a runtime; the
canonical SHA-256 digest is the cross-runtime/platform identity.

## 5. Alternatives rejected

- Embedding creator/channel/source URL facts was rejected because they are consumers, evidence, or
  provenance rather than Opportunity identity.
- Adding lifecycle/type enums was rejected because Product policy is not approved.
- Using nullable strings was rejected because Unknown must be explicit and cannot be confused with
  omission or empty input.
- Reusing Creator Profile, YouTube, analytics, signal, or research models was rejected because those
  boundaries own different concepts.
- Adding ORM/API contracts was rejected because transport and persistence are outside scope.

## 6. Dependencies and compatibility

The module depends only on the standard library and Pydantic already used for immutable domain
contracts. It is absent from application startup. This is additive and changes no existing API,
schema, database, runtime composition, or external behavior.

## 7. Future considerations

Opportunity Candidate identity, evidence/provenance manifests, qualification authority, lifecycle,
retirement, types, audience/pattern bindings, confidence, Creator Profile contextualization, APIs,
persistence, and recommendations each require later Product decisions and ADRs where architectural.

## 8. References

- [Product Vision](../../product/PRODUCT_VISION.md)
- [Product Principles](../../product/PRODUCT_PRINCIPLES.md)
- [Domain Model](../../product/DOMAIN_MODEL.md)
- [Opportunity Engine](../../product/OPPORTUNITY_ENGINE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md), RQ-OPP-001
- [Decision Log](../../product/DECISION_LOG.md), PD-009
- [Feature Registry](../../product/FEATURE_REGISTRY.md), OE-000
- ADR-001, ADR-029, ADR-030, and Engineering Principles EP-004/EP-006
