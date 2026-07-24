# ADR-032: Establish the Opportunity Candidate Domain Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## 1. Decision

Add an isolated `app.services.opportunity_candidate` module containing one immutable,
schema-versioned `OpportunityCandidate` value object and a stateless canonicalizer. The module
records only the pre-qualification discovery, evidence-reference, acquisition-time, and provenance
identities authorized by PD-010.

It does not discover, interpret, explain, qualify, promote, reject, prioritize, score, rank, assess
confidence, recommend, execute AI, or manage lifecycle.

## 2. Product alignment

The Product Domain defines a Candidate as a proposed, not-yet-validated claim that accumulates
evidence before becoming or failing to become an Opportunity. The Candidate therefore remains a
separate type and package from the already-qualified canonical `Opportunity`. Construction asserts
only that specified references were recorded by a discovery source at a stated instant. It makes no
claim about evidence sufficiency, independence, quality, repeatability, accessibility, or Product
qualification. RQ-OPP-001 remains open.

## 3. Contract

Schema version 1 contains:

- one opaque Candidate identity and positive discovery version;
- the closed `youtube` source-platform identity;
- one opaque discovery-source identity;
- one non-empty ordered tuple of unique evidence-reference identities;
- one timezone-aware acquisition timestamp normalized to UTC; and
- one non-empty ordered tuple of unique provenance-reference identities.

Every field is required. Identifier shapes are canonical and non-empty. Boolean, floating-point,
string, zero, and negative versions are rejected. Reference collections must already be immutable
tuples; list and scalar coercion is rejected. Reference order is source meaning and remains part of
Candidate identity. Duplicate evidence identities and duplicate provenance identities are rejected
rather than silently removed.

## 4. Determinism and canonical identity

Canonical JSON uses sorted object keys, compact separators, UTF-8, explicit complete fields, UTC
timestamps, and no NaN. SHA-256 is calculated over those exact bytes. Frozen models and tuple
collections provide recursive immutability, structural equality, and Python hashability. The
canonical digest, rather than Python's runtime hash, is the cross-runtime content identity.

## 5. Boundary and dependencies

The package depends only on the standard library and Pydantic. It has no dependency on YouTube
acquisition, Opportunity, analytics, signals, research, persistence, HTTP, OpenAI, external APIs,
or application startup. It accepts opaque reference identities rather than importing the models
owned by those boundaries.

No registry, repository, API, discovery service, clock, workflow, conversion service, or promotion
service is introduced.

## 6. Alternatives rejected

- Reusing `Opportunity` was rejected because that would erase the Product qualification boundary.
- Embedding source observations or YouTube models was rejected because the Candidate owns
  references, not acquisition payloads or evidence facts.
- Sorting reference identities was rejected because source order is a supplied fact and sorting
  would silently rewrite the snapshot.
- Accepting free-form dictionaries, nullable facts, or mutable lists was rejected because they
  weaken validation, immutability, and canonical identity.
- Adding a proposition, lifecycle state, qualification result, or explanation was rejected because
  those semantics are not authorized for this factual foundation.

## 7. Compatibility and future work

This is an additive public Python contract with no database, API, configuration, dependency,
startup, or operational change. Candidate creation policy, a Candidate registry, evidence content
and binding validation, discovery execution, Product qualification, Candidate-to-Opportunity
conversion, persistence, and lifecycle each require separately approved behavior and architectural
review where material.

## 8. References

- [Product Domain Model](../../product/DOMAIN_MODEL.md)
- [Opportunity Engine](../../product/OPPORTUNITY_ENGINE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md), RQ-OPP-001
- [Decision Log](../../product/DECISION_LOG.md), PD-010
- [Feature Registry](../../product/FEATURE_REGISTRY.md), OE-001
- ADR-001, ADR-029, ADR-031, and Engineering Principles EP-004/EP-006
