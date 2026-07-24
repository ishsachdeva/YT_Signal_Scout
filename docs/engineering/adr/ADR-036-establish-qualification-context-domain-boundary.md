# ADR-036: Establish the Qualification Context Domain Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## 1. Decision

Add an isolated `app.services.qualification_context` module containing one immutable,
schema-versioned `QualificationContext` value object and a stateless canonicalizer. A context
records the complete identity-only request supplied to a future Qualification Engine: what
Candidate is to be evaluated, which Evidence Snapshot and Creator Profile apply, which versioned
Qualification Policy governs the request, and the explicit evaluation instant.

## 2. Product alignment

The Product Domain distinguishes a request to evaluate from evaluation, qualification, and an
Opportunity. PD-014 authorizes this context so a future governed process can receive a stable,
reproducible set of identities without embedding referenced objects or inventing policy behavior.
The context makes no claim that its identities resolve, that evidence is sufficient, or that a
Candidate qualifies. RQ-OPP-001 remains open.

## 3. Contract

Schema version 1 contains exactly:

- one canonical opaque Qualification Context identity;
- one positive Qualification Context version;
- one canonical opaque Opportunity Candidate identity;
- one canonical opaque Evidence Snapshot identity;
- one canonical opaque Creator Profile identity;
- one canonical opaque Qualification Policy identity;
- one positive Qualification Policy version;
- one timezone-aware evaluation timestamp normalized to UTC; and
- one optional bounded human-readable description, serialized explicitly as `null` when Unknown.

The context imports only the identifier types owned by Opportunity Candidate, Evidence Snapshot,
and Creator Profile. Qualification Policy identity is defined locally because this decision does
not authorize a policy domain. Schema and version fields reject Boolean, floating-point, string,
zero, and negative values. Timestamp strings and naive datetimes are rejected.

`evaluation_timestamp` is the instant for which this exact identity set requests future
evaluation. It does not state that evaluation occurred and is not discovery, evidence designation,
retrieval, qualification-result, workflow, or persistence time.

## 4. Explicit exclusions

The contract contains no Opportunity, Candidate object, Evidence Snapshot object, Creator Profile
object, Evidence, Manifest, URL, provenance, metadata, analytics, signals, confidence, score,
recommendation, AI output, qualification result, lifecycle, persistence, retrieval, registry, or
workflow. It performs no evaluation, scoring, ranking, recommendation, or qualification.

## 5. Determinism and canonical identity

Canonical serialization uses sorted object keys, compact separators, UTF-8, complete fields,
UTC-normalized timestamps, and no NaN. SHA-256 is calculated over the exact canonical bytes. The
frozen value object provides structural equality and Python hashability; SHA-256 remains the
cross-runtime content identity.

## 6. Boundary and dependencies

The module may depend only on identifier types from Opportunity Candidate, Evidence Snapshot, and
Creator Profile, plus Pydantic and the standard library. It has no dependency on Opportunity,
Evidence Manifest, Evidence Reference, analytics, signals, research, persistence, HTTP, FastAPI,
SQLAlchemy, OpenAI, external APIs, or application startup. No policy, engine, repository, resolver,
validator, service, API, clock, registry, or workflow is introduced.

## 7. Alternatives rejected

- Embedding referenced domain objects was rejected because the context owns only their identities.
- Adding referenced-object versions not authorized by the Product contract was rejected because
  schema version 1 contains only the specified Candidate, Snapshot, and Profile identities.
- Creating a Qualification Policy contract was rejected because this milestone records only its
  supplied identity and version.
- Adding results, scores, confidence, explanations, or lifecycle was rejected because those are
  outputs or policy concerns, not evaluation-request identity.
- Resolving or validating referenced identities was rejected because retrieval and registries are
  outside this boundary.

## 8. Compatibility and future work

This is an additive public Python contract with no database, API, configuration, dependency,
startup, deployment, or operational change. Qualification Policy definition, identity resolution,
binding validation, evaluation, results, persistence, retention, and workflows each require
separately approved Product and architectural decisions.

## 9. References

- [Product Domain Model](../../product/DOMAIN_MODEL.md)
- [Product Principles](../../product/PRODUCT_PRINCIPLES.md)
- [Opportunity Engine](../../product/OPPORTUNITY_ENGINE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md), RQ-OPP-001
- [Decision Log](../../product/DECISION_LOG.md), PD-014
- [Feature Registry](../../product/FEATURE_REGISTRY.md), QC-001
- ADR-001, ADR-029, ADR-030, ADR-032, ADR-035, and Engineering Principles EP-004/EP-006
