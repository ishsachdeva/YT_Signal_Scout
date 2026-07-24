# ADR-029: Separate Product Architecture from Technical Architecture

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Engineering

## Purpose

Record why Product Architecture is a distinct source of intent and how technical decisions must
trace to it without conflating planned behaviour with implemented software.

## Supersedes

None.

## Table of contents

- [Decision summary](#1-decision-summary)
- [Context](#2-context)
- [Problem statement](#3-problem-statement)
- [Decision drivers](#4-decision-drivers)
- [Goals](#5-goals)
- [Alternatives](#6-alternatives-considered)
- [Decision](#7-decision)
- [Rationale](#8-decision-rationale)
- [Principles](#9-related-principles)
- [Consequences](#10-consequences)
- [Implementation impact](#11-implementation-impact)
- [Operational impacts](#12-security-performance-cost-and-operations)
- [Future considerations](#13-future-revisit-criteria)
- [References](#14-references)
- [Revision history](#15-revision-history)

## 1. Decision summary

Establish Product Architecture under `docs/product/` as the authority for long-term Product intent,
ubiquitous language, personas, journeys, capability relationships, principles, and roadmap. Keep
Technical Architecture under `docs/engineering/` and ADRs as the authority for system structure and
implementation decisions. Technical work must trace to applicable Product documents; it cannot
invent Product behaviour.

## 2. Context

YT Signal Scout began with channel discovery and evolved a rigorous analytics/research foundation.
Product discovery now identifies Opportunities—not channels—as the primary decision asset. Without
an explicit Product Architecture, individually correct features could accumulate around the wrong
outcome or embed unapproved product meanings in code.

Original PRD/TRD source files remain historical requirements and context. The v0.10.0 Product
Architecture expresses forward platform direction and records material changes through the Product
Decision Log. The Signal Catalog and Decision Governance retain their specialized authority.

## 3. Problem statement

Technical architecture answers how the system is structured; it cannot independently answer why a
capability exists, which user decision it supports, what an Opportunity means, or what confidence
may claim. Conflating these responsibilities risks accidental policy, terminology drift, premature
algorithms, and roadmap incoherence.

## 4. Decision drivers

- Stable ubiquitous language across Product, research, design, and engineering.
- Traceability from customer problem to capability to technical boundary.
- Prevention of unapproved algorithms and recommendation meanings.
- Preservation of historical PRD, research, and ADR records.
- Maintainable evolution from channel tooling to Opportunity Intelligence.

## 5. Goals

- Make Product intent understandable without reading source code.
- Require future features and ADRs to identify their Product purpose and constraints.
- Keep Product decisions separate from research conclusions and technical choices.
- Allow each architecture layer to evolve through its own governed records.

## 6. Alternatives considered

### Continue using only the original PRD and feature prompts

Rejected because the original channel-centric framing does not fully describe the emerging platform,
and prompts are not a durable, navigable source of truth.

### Put Product direction inside technical ADRs

Rejected because ADRs should record engineering decisions, not own personas, journeys,
recommendation philosophy, or roadmap semantics.

### Combine Product and Technical Architecture into one document

Rejected because mixed ownership encourages implementation status, Product intent, and research
evidence to drift together and makes review responsibilities unclear.

## 7. Decision

The Product Architecture index defines its document set and precedence. Future feature proposals
must reference relevant vision, principle, domain, persona/journey, capability, registry, roadmap,
and decision sources. Technical ADRs must include those Product references and explain how the
chosen architecture preserves Product boundaries. Research informs Product decisions but does not
approve them. Implementation does not redefine domain terms by naming a class or field.

When documents conflict, resolve according to specialized authority and record the resolution:
Product Architecture/Decision Log for Product intent; Signal Catalog/PDRs for approved signal
policy; Research protocols/artifacts for methods and results; ADRs/TRD for technical structure;
source code and tests for verified implementation status.

## 8. Decision rationale

Separate layers create a clear dependency direction: customer problem and Product meaning guide
research questions and technical design, while verified evidence and engineering constraints feed
back through explicit decisions. This prevents both “architecture by feature request” and Product
claims inferred from whatever code happens to exist.

## 9. Related principles

- Product Principles PP-007 (explainability), PP-009 (reproducibility), and PP-010 (explicit Product
  ownership).
- Engineering Principles EP-001 (maintainability), EP-002 (separation of concerns), and EP-003
  (single responsibility).

## 10. Consequences

**Positive:** clearer intent, consistent language, traceable ADRs, safer recommendation evolution,
and easier onboarding. **Negative:** more documentation and cross-functional review before features.
**Risks:** documents may become stale or be treated as automatic implementation authorization.
Mitigation is ownership, revision histories, the Decision Log, Feature Registry reconciliation, and
explicit implementation-status language.

## 11. Implementation impact

Affected areas are documentation and agent operating instructions only. No production module, API,
analytics, research execution, persistence, dependency, or migration changes. No breaking changes.

## 12. Security, performance, cost, and operations

There is no runtime security, performance, infrastructure, cost, deployment, or operational impact.
Future capability documents identify areas requiring later reviews but authorize none.

## 13. Future revisit criteria

Revisit if the product expands beyond YouTube, Product decision ownership changes, the documentation
set becomes too fragmented, or delivery experience demonstrates a clearer traceability model. A
replacement ADR must preserve historical intent and explicitly supersede this record.

## 14. References

- [Product Architecture](../../product/README.md)
- [Product Vision](../../product/PRODUCT_VISION.md)
- [Product Principles](../../product/PRODUCT_PRINCIPLES.md)
- [Domain Model](../../product/DOMAIN_MODEL.md)
- [Decision Log](../../product/DECISION_LOG.md)
- [Product Governance](../../product/PRODUCT_GOVERNANCE.md)
- [Product Lifecycle](../../product/PRODUCT_LIFECYCLE.md)
- [Research Questions](../../product/RESEARCH_QUESTIONS.md)
- [Decision Governance](../../governance/DECISION_GOVERNANCE.md)
- [Engineering Principles](../ENGINEERING_PRINCIPLES.md)

## 15. Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Accepted separation and traceability responsibilities. |
