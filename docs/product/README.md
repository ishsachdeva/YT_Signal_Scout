# Product Architecture

## Purpose

This directory is the authoritative product-architecture layer for YT Signal Scout. It explains
what product is being built, for whom, why its capabilities exist, and how evidence becomes a
responsible opportunity recommendation. Technical architecture implements this intent; it does not
define or expand Product behaviour independently.

## Product Knowledge Status

**Status: Validated.** This index and its authority model are accepted governance. Individual linked
documents retain their own status; inclusion here does not validate or implement their content.

## Table of contents

- [Authority and scope](#authority-and-scope)
- [Foundation documents](#foundation-documents)
- [Capability documents](#capability-documents)
- [Governance documents](#governance-documents)
- [Product knowledge states](#product-knowledge-states)
- [Using this documentation](#using-this-documentation)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Authority and scope

The source documents in `source/` record the original channel-discovery product and remain required
historical context. The v0.10.0 Markdown foundation defines the long-term Opportunity Intelligence
Platform direction. Where future direction differs from an original assumption, a Product decision
must be appended to `DECISION_LOG.md`; accepted technical structure belongs in an ADR.

Product documents authorize intent, terminology, outcomes, and constraints. They do not mark a
feature implemented, approve a formula, or override verified runtime status. The Signal Catalog
continues to govern signal policy. Decision Governance continues to govern approvals.

## Foundation documents

| Document | Authority |
|---|---|
| [Product Vision](PRODUCT_VISION.md) | Mission, customers, positioning, outcomes, and non-goals |
| [Product Principles](PRODUCT_PRINCIPLES.md) | Durable rules for evidence and trusted recommendations |
| [Domain Model](DOMAIN_MODEL.md) | Ubiquitous language and conceptual relationships |
| [User Personas](USER_PERSONAS.md) | Intended users, constraints, and success measures |
| [User Journeys](USER_JOURNEYS.md) | End-to-end product experiences |
| [Recommendation Philosophy](RECOMMENDATION_PHILOSOPHY.md) | Responsible recommendation behaviour |

## Capability documents

| Document | Capability |
|---|---|
| [Opportunity Engine](OPPORTUNITY_ENGINE.md) | Evidence-to-opportunity product boundary |
| [Channel Discovery](CHANNEL_DISCOVERY.md) | Channels as market evidence and references |
| [Niche Discovery](NICHE_DISCOVERY.md) | Niche and micro-niche structure |
| [Topic Discovery](TOPIC_DISCOVERY.md) | Topic evidence and future extraction research |
| [Trend Discovery](TREND_DISCOVERY.md) | Time-bounded change and lifecycle evidence |
| [Competitor Discovery](COMPETITOR_DISCOVERY.md) | Comparable reference-channel selection |
| [Creator Profile](CREATOR_PROFILE.md) | Personalization inputs and safeguards |
| [Opportunity Confidence](OPPORTUNITY_CONFIDENCE.md) | Confidence in evidence quality, not creator success |

## Governance documents

| Document | Role |
|---|---|
| [Feature Registry](FEATURE_REGISTRY.md) | Product capability inventory and dependency order |
| [Product Roadmap](PRODUCT_ROADMAP.md) | Phased long-term evolution, not delivery commitment |
| [Decision Log](DECISION_LOG.md) | Living record of major Product decisions |
| [Product Governance](PRODUCT_GOVERNANCE.md) | Knowledge states, ownership, precedence, and reviews |
| [Product Lifecycle](PRODUCT_LIFECYCLE.md) | Governed evolution from problem to measured implementation |
| [Research Questions](RESEARCH_QUESTIONS.md) | Canonical unanswered Product Discovery backlog |
| [Signal Catalog](SIGNAL_CATALOG.md) | Approved/proposed signal semantics and readiness |
| [Decision Governance](../governance/DECISION_GOVERNANCE.md) | Approval ownership and lifecycle |

## Product knowledge states

Every Product Architecture document declares one status governed by
[Product Governance](PRODUCT_GOVERNANCE.md): **Vision**, **Hypothesis**, **Research In Progress**,
**Validated**, or **Implemented**. Vision is desired direction; Hypothesis is an unvalidated
assumption; Research In Progress indicates active governed inquiry; Validated indicates evidence or
governance acceptance within stated scope; Implemented requires verified code, tests, and
documentation. Composite status must identify its boundaries explicitly.

## Using this documentation

Every future feature proposal should identify the user problem, relevant persona and journey,
domain terms, governing principles, registry entry, roadmap phase, evidence requirements, and
limitations. It must also identify its knowledge state and applicable Research Questions.
Architecture work must cite these sources and an ADR when boundaries change. Research
must distinguish observations from Product decisions. Documentation never substitutes for explicit
acceptance criteria or implementation verification.

## Future considerations

Review this index whenever a new capability, persona, recommendation class, or material Product
decision is introduced. Prefer extending the existing ubiquitous language over creating synonyms.

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Established Product Architecture as the v0.10.0 source of future product intent. |
| 1.1 | 2026-07-24 | Added knowledge states, research governance, and lifecycle references. |
