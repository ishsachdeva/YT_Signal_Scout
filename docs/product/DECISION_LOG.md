# Product Decision Log

## Purpose

Maintain a living, append-only summary of major Product decisions. Detailed Product Decision Records
may expand individual decisions. Technical implementation decisions remain in ADRs.

## Product Knowledge Status

**Status: Validated.** Recorded decisions are accepted within their stated classification and scope.
Open decisions and referenced hypotheses remain unvalidated; decision presence does not imply code.

## Table of contents

- [Usage](#usage)
- [Scope](#scope)
- [Decision classifications](#decision-classifications)
- [Decisions](#decisions)
- [Open decisions](#open-decisions)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Usage

Append decisions; do not rewrite historical rationale. A changed decision should supersede an earlier
entry and link it. Each entry identifies the decision, rationale, implications, and related sources.
“Decided” establishes Product intent but does not mark implementation complete.

## Scope

This log covers durable Product meaning and direction. Research findings, technical choices,
delivery status, and routine editorial changes belong in their respective governed records.

Research questions and their disposition are governed by [Research Questions](RESEARCH_QUESTIONS.md)
and [Product Lifecycle](PRODUCT_LIFECYCLE.md). Decision authority, document precedence, and the
meaning of knowledge states are governed by [Product Governance](PRODUCT_GOVERNANCE.md).

## Decision classifications

Every future decision belongs to exactly one classification. Cross-references do not change its
owner or authority.

| Classification | Decides | Canonical record | Does not establish |
|---|---|---|---|
| **Vision Decision** | Mission, target users, long-term direction, and enduring desired outcomes | Product Decision Log or approved vision record | Research validity, architecture, or implementation |
| **Research Decision** | Research question, method, evidence sufficiency for a finding, or study disposition | Research plan, artifact, or research decision record | Product policy or runtime behavior |
| **Product Decision** | User-facing meaning, behavior, scope, policy, prioritization, or acceptance | Product Decision Log or PDR | Technical design or completed implementation |
| **Architecture Decision** | Durable technical boundary, dependency, structure, or technology choice | ADR | Product need, market validation, or code completion |
| **Implementation Decision** | Local approved-scope construction detail that does not alter architecture or Product behavior | Code review, design note, commit, or test record | New Product behavior or architectural authority |

If one proposal contains multiple classifications, split it into linked records. For example, a
Product Decision may authorize explainable recommendation behavior; a later ADR decides technical
boundaries; implementation decisions choose local construction details.

## Decisions

### PD-001: Opportunities are the primary Product asset

**Classification:** Vision Decision. **Date:** 2026-07-24. **Status:** Decided. **Decision:** The platform exists to identify and explain
bounded Opportunities; channels, videos, topics, and trends are evidence. **Rationale:** Channel lists
do not answer whether a direction is repeatable, accessible, timely, or worth testing. **Implication:**
Future capabilities must connect evidence to an Opportunity lifecycle. **Related:**
[Product Vision](PRODUCT_VISION.md), [Domain Model](DOMAIN_MODEL.md).

### PD-002: Channel Discovery is a foundation, not the final goal

**Classification:** Vision Decision. **Date:** 2026-07-24. **Status:** Decided. **Decision:** Continue channel capabilities as evidence
infrastructure within a larger platform. **Rationale:** Channels group repeated public observations
but cannot alone establish market gaps or creator fit. **Implication:** Avoid roadmaps or interfaces
that equate promising channels with complete recommendations. **Related:**
[Channel Discovery](CHANNEL_DISCOVERY.md).

### PD-003: Cross-channel evidence is required for market recommendations

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided at principle level; exact policy unapproved. **Decision:**
No market recommendation may rely on one creator or one viral video. **Rationale:** Individual
outcomes have many alternative explanations. **Implication:** Future research must define sufficient
independence, diversity, and coverage. **Related:** [Product Principles](PRODUCT_PRINCIPLES.md).

### PD-004: Small-creator evidence is necessary

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided at principle level. **Decision:** Evidence from established
creators alone cannot establish accessibility for aspiring creators. **Rationale:** Incumbents have
audience, brand, team, capital, and distribution advantages. **Implication:** Reference sets and
validation must represent credible small creators and disclose scale. **Related:**
[Competitor Discovery](COMPETITOR_DISCOVERY.md).

### PD-005: Opportunity Confidence concerns evidence quality

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided; presentation unapproved. **Decision:** Confidence must never
be interpreted as probability of creator success, YPP attainment, views, or revenue. **Rationale:**
Public market evidence cannot model individual execution and future platform state reliably.
**Implication:** No confidence formula or user-facing score exists until governed research and a
separate Product decision approve its meaning. **Related:**
[Opportunity Confidence](OPPORTUNITY_CONFIDENCE.md).

### PD-006: Recommendations must be transparent and may be withheld

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided at principle level. **Decision:** Recommendations expose
rationale, counterevidence, limitations, and profile effects; insufficient evidence is a valid
result. **Rationale:** Trust and user agency outweigh recommendation volume. **Implication:** No
black-box or always-return-something design. **Related:**
[Recommendation Philosophy](RECOMMENDATION_PHILOSOPHY.md).

### PD-007: Product Architecture and Technical Architecture are separate

**Classification:** Architecture Decision. **Date:** 2026-07-24. **Status:** Decided. **Decision:** Product architecture governs intent and
ubiquitous language; technical architecture governs implementation structure. **Rationale:** Feature
requests must follow an explicit product model rather than accumulate into accidental architecture.
**Implication:** Future technical ADRs cite relevant Product documents. **Related:** ADR-029.

### PD-008: Authorize a deterministic Personal Creator Profile foundation

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided for v0.10.1.
**Decision:** Authorize one immutable, versioned profile containing only explicit owner-supplied
production preferences and constraints: presentation style, AI-assistance preference, preferred
language, target geography, available weekly production hours, self-assessed editing capability,
narration preference, self-declared budget category, and upload-cadence goal. Every fact may remain
Unknown. **Rationale:** Later market and feasibility work needs a stable factual input, while the
usefulness and personalization effect of these attributes remain unvalidated. **Implication:** The
foundation may validate and canonically serialize facts, but may not infer preferences, persist
them, evaluate fit, filter Opportunities, recommend action, execute AI, or claim that the profile
improves outcomes. **Related:** [Creator Profile](CREATOR_PROFILE.md), RQ-CRT-001, RQ-PRD-001,
Feature CR-001, and ADR-030.

### PD-009: Authorize the canonical Opportunity identity foundation

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided for the foundational
Opportunity domain milestone.
**Decision:** Authorize one immutable, versioned Opportunity value object containing only its opaque
Opportunity, Market, and Niche identities; an exact bounded proposition; YouTube source-platform
identity; and explicit known-or-unknown language and region context. Identifier values must be
unique within one Opportunity snapshot. **Rationale:** Opportunity is the primary Product asset and
requires a stable canonical identity before later governed capabilities can reference it.
**Implication:** Construction records an Opportunity already qualified under future Product policy;
it does not discover, classify, validate evidence, qualify, score, rank, assess quality, recommend,
or change lifecycle. Creator/profile IDs, channel IDs/handles, source URLs, discovery timestamps,
Opportunity types, and lifecycle states are excluded because they are consumer, evidence,
provenance, or still-unapproved policy concerns. RQ-OPP-001 remains open. **Related:**
[Domain Model](DOMAIN_MODEL.md), [Opportunity Engine](OPPORTUNITY_ENGINE.md), Feature OE-000, and
ADR-031.

### PD-010: Authorize the factual Opportunity Candidate foundation

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided for the foundational
Opportunity Candidate milestone. **Decision:** Authorize one immutable, versioned Candidate value
object containing only opaque Candidate and discovery-source identity, YouTube source-platform
identity, ordered evidence-reference and provenance-reference identities, and an explicit
acquisition timestamp. **Rationale:** Potential Opportunities require a stable pre-qualification
snapshot that preserves what discovery supplied without using the governed term Opportunity or
asserting evidence quality. **Implication:** Candidate construction records source facts only. It
does not discover, interpret, explain, qualify, promote, reject, prioritize, score, rank, assess
confidence, recommend, execute AI, or manage lifecycle. The Candidate does not depend on or embed
the canonical Opportunity. RQ-OPP-001 and Candidate qualification policy remain open. **Related:**
[Domain Model](DOMAIN_MODEL.md), [Opportunity Engine](OPPORTUNITY_ENGINE.md), Feature OE-001, and
ADR-032.

### PD-011: Authorize the canonical Evidence Reference foundation

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided for the foundational
Evidence Reference milestone. **Decision:** Authorize one immutable, versioned pointer containing
only an opaque Evidence Reference identity, evidence version, closed YouTube channel-or-video
evidence type, YouTube source-platform identity, and opaque source-object identity. **Rationale:**
Candidates and future governed systems require stable evidence identities without embedding source
facts or asserting that those facts qualify as Evidence. **Implication:** The reference contains no
payload, metadata, analytics, score, confidence, qualification, recommendation, lifecycle, AI
output, provenance, timestamp, URL, or discovery behavior. It neither fetches nor validates the
pointed-to object and remains independent of Opportunity and Candidate. Evidence sufficiency,
binding, provenance, retrieval, and qualification remain open. **Related:** [Domain Model](DOMAIN_MODEL.md),
[Opportunity Engine](OPPORTUNITY_ENGINE.md), Feature ER-001, and ADR-033.

### PD-012: Authorize the immutable Evidence Manifest foundation

**Classification:** Product Decision. **Date:** 2026-07-24. **Status:** Decided for the foundational
Evidence Manifest milestone. **Decision:** Authorize one immutable, versioned snapshot containing
only an opaque manifest identity, an ordered non-empty collection of unique Evidence Reference
identities, an explicit UTC-normalized creation time, and optional bounded human-readable
description. **Rationale:** Future governed systems require an exact, reproducible declaration of
which references belonged to a snapshot without embedding evidence or silently rewriting reference
membership. **Implication:** Reference order is identity and must never be sorted; duplicates are
rejected, not removed. A manifest neither retrieves nor validates references and contains no
payload, provenance, URL, metadata, analytics, qualification, confidence, recommendation,
lifecycle, score, AI output, discovery, retrieval, or persistence behavior. Evidence sufficiency,
binding, provenance, and downstream use remain open. **Related:** [Domain Model](DOMAIN_MODEL.md),
[Opportunity Engine](OPPORTUNITY_ENGINE.md), Feature EM-001, and ADR-034.

## Open decisions

Opportunity qualification and lifecycle, evidence sufficiency, reference-set independence,
topic/niche validation, confidence presentation, broader creator-profile data policy and personalization,
recommendation eligibility, and outcome feedback remain open. Roadmap inclusion is not approval.

## Future considerations

Create detailed PDRs when a decision establishes acceptance policy, user-facing claims, safety
constraints, or measurable targets. Reconcile the Feature Registry after every material decision.

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Recorded seven foundational Product decisions. |
| 1.1 | 2026-07-24 | Added exclusive decision classifications and governance cross-references. |
| 1.2 | 2026-07-24 | Authorized the bounded v0.10.1 Personal Creator Profile facts. |
| 1.3 | 2026-07-24 | Authorized the bounded canonical Opportunity identity foundation. |
| 1.4 | 2026-07-24 | Authorized the factual pre-qualification Opportunity Candidate foundation. |
| 1.5 | 2026-07-24 | Authorized the canonical payload-free Evidence Reference foundation. |
| 1.6 | 2026-07-24 | Authorized the ordered immutable Evidence Manifest snapshot foundation. |
