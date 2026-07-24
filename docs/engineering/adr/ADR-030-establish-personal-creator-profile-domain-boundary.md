# ADR-030: Establish a Personal Creator Profile Domain Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## 1. Decision

Add an isolated `app.services.creator_profile` module containing an immutable schema-versioned
`CreatorProfile` value object, closed factual vocabularies, strict validation, and a stateless
canonicalizer. The module represents only user-supplied facts authorized by PD-008.

No service, repository, database model, API, UI, clock, external dependency, AI behavior,
personalization, feasibility evaluation, filtering, or recommendation belongs to this milestone.

## 2. Context

The Product Domain defines a Creator Profile as an explicit, user-controlled snapshot of goals,
preferences, capabilities, and constraints. The repository previously had no corresponding domain
contract. Future Opportunity work needs a stable factual boundary, but RQ-CRT-001 and RQ-PRD-001
remain unanswered; implementation therefore cannot claim that these facts improve relevance or
define production feasibility.

## 3. Alternatives considered

- **Reuse YouTube or analytics models:** rejected because creator facts are neither vendor data nor
  channel analytics and would violate domain ownership.
- **Add an ORM model and API now:** rejected because persistence, identity ownership, authorization,
  and UI are explicitly outside scope.
- **Use free-form dictionaries/strings:** rejected because they weaken validation, terminology,
  reproducibility, and future explainability.
- **Create the isolated immutable value boundary:** accepted as the smallest reusable foundation.

## 4. Contract decisions

- Schema version and profile version are explicit positive integers; profile identity is opaque and
  contains no required personal information.
- Optional fact fields default to `None`, which means Unknown. No value is inferred or substituted.
- Closed enums represent self-declared categories; categories do not assert objective skill,
  affordability, production quality, or suitability.
- Language tags use a conservative canonical lower-case tag shape; geography uses an upper-case
  two-letter code shape. Shape validation does not claim that a code is assigned or suitable.
- Weekly production hours distinguish explicit zero from Unknown and reject Boolean/coerced values.
- Canonical serialization uses UTF-8, sorted keys, compact JSON, no NaN, and SHA-256 digest support.

## 5. Boundary and dependencies

The module depends only on the standard library and Pydantic already used by the application. It is
independent of HTTP, persistence, analytics, research, signals, YouTube acquisition, and application
startup. Future consumers may depend on this value object only after their Product behavior is
approved; this ADR does not authorize those consumers.

## 6. Consequences

**Positive:** deterministic facts, explicit Unknown semantics, immutable snapshots, stable
serialization, no sensitive identity requirement, and a clear future dependency boundary.
**Negative:** self-declared categorical values remain coarse and unvalidated for usefulness.
**Risk:** consumers may mistake a preference or skill category for objective capability. Mitigation
is naming, documentation, and prohibiting inference or fit evaluation in this milestone.

## 7. Compatibility and operations

This is an additive public Python contract. No existing contract changes, migration, deployment,
security secret, runtime composition, performance path, or operational process is affected.

## 8. Future considerations

Persistence, ownership/authentication binding, history, consent, profile updates, localization,
multi-language or multi-market needs, richer feasibility facts, APIs, and downstream use each
require their own approved Product scope and, where architectural, a later ADR. RQ-CRT-001 and
RQ-PRD-001 remain open.

## 9. References

- [Product Vision](../../product/PRODUCT_VISION.md)
- [Product Principles](../../product/PRODUCT_PRINCIPLES.md)
- [Domain Model](../../product/DOMAIN_MODEL.md)
- [Creator Profile](../../product/CREATOR_PROFILE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md)
- [Decision Log](../../product/DECISION_LOG.md), PD-008
- [Feature Registry](../../product/FEATURE_REGISTRY.md), CR-001
- ADR-001, ADR-029, and Engineering Principle EP-006
