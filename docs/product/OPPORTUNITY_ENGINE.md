# Opportunity Engine

## Purpose

Define the long-term product boundary that organizes evidence around Opportunities. This is product
architecture only: no algorithm, formula, score, threshold, or implementation is authorized.

## Product Knowledge Status

**Status: Implemented Foundation + Future Vision.** The canonical Opportunity identity contract is
implemented under PD-009 and ADR-031. No Opportunity discovery, evidence qualification,
confidence, recommendation, lifecycle service, algorithm, or runtime workflow is implemented.

## Table of contents

- [Scope](#scope)
- [Implemented identity foundation](#implemented-identity-foundation)
- [Inputs](#inputs)
- [Evidence lifecycle](#evidence-lifecycle)
- [Opportunity lifecycle](#opportunity-lifecycle)
- [Validation and research](#validation-and-research)
- [Confidence](#confidence)
- [Recommendations](#recommendations)
- [Boundaries](#boundaries)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Scope

The Opportunity Engine is the conceptual product capability that turns qualified observations into
an inspectable opportunity proposition. “Engine” does not imply a single service. Opportunities are
repository-level domain concepts whose meaning must remain stable across research, APIs, interfaces,
and future workflows.

## Implemented identity foundation

Schema version 1 records one already-qualified Opportunity as an opaque Opportunity identity and
version, opaque Market and Niche identities, the exact bounded proposition, YouTube source-platform
identity, and explicit known-or-unknown language and region context. All fields are required. The
contract is immutable, strictly validated, canonically serialized, and content-addressable.

This foundation does not decide whether evidence is sufficient, create or promote a candidate,
classify a proposition, assign a type or lifecycle state, attach creator/channel provenance, or
judge quality. Those behaviors remain governed future work.

## Inputs

Potential inputs include immutable channel/video facts, topic and content-pattern evidence, trend
lifecycle observations, niche/market boundaries, competitor reference sets, audience needs,
production demands, monetization evidence, creator-profile constraints, governed research results,
and explicit Product policy. Each input must carry provenance, time context, availability, and
appropriate version binding.

## Evidence lifecycle

Evidence is acquired or supplied, normalized into factual observations, qualified for data quality,
grouped around a bounded claim, evaluated through governed research where necessary, and retained
as supporting, opposing, missing, or stale. Facts are not rewritten when policy changes. Evidence
from multiple channels protects against individual anomalies; diversity across creator scale and
time protects against incumbency and momentary spikes.

## Opportunity lifecycle

An Opportunity Candidate states a testable market proposition. It may progress through discovery,
evidence collection, research validation, Product qualification, profile-contextual consideration,
recommendation eligibility, monitoring, and retirement. It may also be rejected or remain
insufficient. Status must not imply creator success. Every version binds its market, audience,
niche/micro-niche, patterns, evidence, limitations, and valid time context.

## Validation and research

Validation asks whether evidence supports the defined proposition, whether alternative explanations
remain, whether observations are sufficiently independent and current, and whether claimed
repeatability and accessibility are justified. Research defines methods and measures; Product owns
the meaning and acceptance policy. No implementation should invent an evidence requirement because
it is easy to calculate.

## Confidence

Opportunity Confidence communicates quality of the supporting evidence basis, including consistency,
diversity, recency, persistence, repeatability, and known gaps. It does not predict YPP eligibility,
views, revenue, or creator success. See [Opportunity Confidence](OPPORTUNITY_CONFIDENCE.md).

## Recommendations

A recommendation contextualizes an eligible Opportunity for a Creator Profile and offers an
explainable next decision or bounded experiment. It presents rationale, contradictory evidence,
profile fit, limitations, and what could invalidate the proposition. The system may responsibly
withhold a recommendation.

## Boundaries

The engine does not guarantee outcomes, autonomously approve Product policy, hide contradictory
evidence, collapse all facts into an unexplained score, infer sensitive creator traits, or execute
publishing actions. Opportunity discovery, qualification, confidence communication, and
recommendation are separate responsibilities even if a future interface presents them together.

## Future considerations

Research must establish qualification policy, candidate provenance, evidence-independence criteria,
lifecycle states, retirement semantics, profile-fit governance, and outcome feedback before those
capabilities are implemented. The implemented identity foundation does not resolve RQ-OPP-001.

Related: [Domain Model](DOMAIN_MODEL.md), [Feature Registry](FEATURE_REGISTRY.md), and
[Product Principles](PRODUCT_PRINCIPLES.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Defined the long-term evidence-to-opportunity product boundary. |
| 1.1 | 2026-07-24 | Clarified that the engine remains Vision and is not implemented. |
| 1.2 | 2026-07-24 | Recorded the implemented canonical identity foundation and retained future policy boundaries. |
