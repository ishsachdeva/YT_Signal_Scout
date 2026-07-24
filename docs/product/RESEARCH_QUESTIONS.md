# Product Research Questions

## Purpose

Maintain the canonical backlog of unanswered Product Discovery questions. This document records
questions and unvalidated assumptions; it does not contain findings, answers, Product decisions,
algorithms, formulas, or implementation authority.

## Product Knowledge Status

**Status: Hypothesis.** Every current assumption below is explicitly unvalidated. Individual items
may move to Research In Progress or Validated only through governed research artifacts; this backlog
retains the question and links its disposition.

## Table of contents

- [Scope](#scope)
- [Status vocabulary](#status-vocabulary)
- [Question evolution](#question-evolution)
- [Opportunity Discovery](#opportunity-discovery)
- [Channel Discovery](#channel-discovery)
- [Topic Discovery](#topic-discovery)
- [Trend Discovery](#trend-discovery)
- [Creator Intelligence](#creator-intelligence)
- [Production Feasibility](#production-feasibility)
- [Competition](#competition)
- [Monetization](#monetization)
- [Recommendation Explainability](#recommendation-explainability)
- [Confidence](#confidence)
- [Future AI](#future-ai)
- [Ethics](#ethics)
- [Relationships and traceability](#relationships-and-traceability)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Scope

This backlog covers unknowns that could materially affect Product meaning, user trust, evidence
requirements, prioritization, or feasibility. Engineering questions belong in ADR/design work;
research-method details belong in a future research plan linked from the relevant Research ID.

## Status vocabulary

| Validation status | Meaning |
|---|---|
| Not started | Question is recorded; no governed plan has begun. |
| Planned | A research plan is being prepared or reviewed. |
| Research In Progress | An approved plan is gathering or evaluating evidence. |
| Finding available | A governed finding exists and awaits or has completed Product review. |
| Closed | A Product decision records the disposition; the historical question remains. |

Priority is **Critical**, **High**, **Medium**, or **Exploratory** and reflects decision dependency,
not expected outcome. All initial evidence fields remain “to be inventoried” to avoid implying an
answer before a governed audit.

## Question evolution

A question begins with an observed problem and testable assumption. Product and Research refine it
without biasing the answer, create a plan, bind evidence, and produce a scoped finding. A Product
Decision may accept, reject, defer, or request further research. Findings link here; they do not
replace the question. ADRs follow only after approved Product behavior needs technical structure.
Implementation follows accepted decisions and architecture, never the backlog alone.

## Opportunity Discovery

### RQ-OPP-001

- **Question:** Which observable conditions distinguish a repeatable, accessible YouTube Opportunity
  from an interesting but non-repeatable market anomaly?
- **Why it matters:** This distinction governs the platform's primary Product asset.
- **Current assumption:** Multiple independent, recent, persistent observations may be necessary.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Domain Model, Channel Intelligence, topic/niche definitions, labelled evidence.
- **Potential future experiments:** Could blinded expert labels and out-of-sample case review test
  whether proposed evidence conditions distinguish repeatable candidates?
- **Priority:** Critical.

## Channel Discovery

### RQ-CHN-001

- **Question:** What channel-discovery and reference-set coverage is sufficient to support a market
  claim without mistaking search rank or acquisition gaps for representative evidence?
- **Why it matters:** Opportunity evidence depends on the quality and diversity of observed channels.
- **Current assumption:** Market-scoped, cross-channel coverage and explicit completeness are needed.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Acquisition provenance, Channel Intelligence, market boundaries.
- **Potential future experiments:** Could stratified query audits and independent channel sampling
  reveal coverage and selection bias?
- **Priority:** Critical.

## Topic Discovery

### RQ-TOP-001

- **Question:** Which authorized evidence sources and review process identify useful Topics across
  formats and languages with acceptable ambiguity and error?
- **Why it matters:** Topics organize future niche, trend, and opportunity evidence.
- **Current assumption:** Multiple source types may be more reliable than title-only classification.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Topic definition, multilingual datasets, source authorization.
- **Potential future experiments:** Could independently labelled title/description/transcript samples
  compare source combinations without selecting an algorithm in advance?
- **Priority:** High.

## Trend Discovery

### RQ-TRD-001

- **Question:** What longitudinal evidence distinguishes an emerging Trend from seasonality, news,
  coordinated activity, or a short-lived distribution spike?
- **Why it matters:** False trend claims could cause creators to act on temporary noise.
- **Current assumption:** Multiple windows, channels, and counterfactual contexts may be required.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Stable Topic identity, observation history, market/season context.
- **Potential future experiments:** Could historical blinded lifecycle labelling evaluate candidate
  persistence definitions across known seasonal and event-driven cases?
- **Priority:** High.

## Creator Intelligence

### RQ-CRT-001

- **Question:** Which creator-supplied attributes materially improve opportunity relevance without
  creating excessive burden, sensitive inference, or unfair exclusion?
- **Why it matters:** Personalization should improve feasibility while preserving agency and privacy.
- **Current assumption:** Explicit constraints and goals may be more useful than inferred traits.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Persona research, privacy/security review, Creator Profile vocabulary.
- **Potential future experiments:** Could interviews and prototype choice studies identify attributes
  users understand, control, and find decision-relevant?
- **Priority:** High.

## Production Feasibility

### RQ-PRD-001

- **Question:** How can users and researchers describe production demands consistently enough to
  assess accessibility without reducing creative work to a universal difficulty score?
- **Why it matters:** A market opening is not actionable when its repeatable patterns are inaccessible.
- **Current assumption:** Resource dimensions and user-declared constraints may be preferable to one score.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Format and Content Pattern definitions, Creator Profile research.
- **Potential future experiments:** Could creator diary studies and independent task decomposition
  establish understandable feasibility dimensions?
- **Priority:** High.

## Competition

### RQ-CMP-001

- **Question:** What evidence demonstrates that a competitor reference set is relevant, diverse, and
  sufficiently independent for a specific Opportunity?
- **Why it matters:** Large but homogeneous reference sets can create false cross-channel confidence.
- **Current assumption:** Creator scale, ownership, format, time, market, and opposing examples matter.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Competitor roles, channel identity, market boundaries, Opportunity Candidates.
- **Potential future experiments:** Could expert review of constructed sets test relevance and hidden
  dependence before any selection policy is proposed?
- **Priority:** Critical.

## Monetization

### RQ-MON-001

- **Question:** Which public or creator-supplied facts can responsibly describe monetization
  mechanisms without implying revenue, sponsorship value, or YPP success?
- **Why it matters:** Monetization goals affect creator decisions but invite harmful overstatement.
- **Current assumption:** Mechanism availability may be describable even when financial outcome is not.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Market context, policy/legal review, persona goals, authorized data.
- **Potential future experiments:** Could expert review and user-comprehension studies identify useful
  evidence language that users do not interpret as a forecast?
- **Priority:** Medium.

## Recommendation Explainability

### RQ-EXP-001

- **Question:** What explanation content enables creators to understand, challenge, and safely act on
  an Opportunity recommendation without information overload?
- **Why it matters:** Explainability is necessary for trust, falsifiability, and user control.
- **Current assumption:** Evidence, counterevidence, limitations, profile effects, and reassessment
  conditions should be visible.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Opportunity definition, Confidence research, Creator Profile, user journeys.
- **Potential future experiments:** Could comprehension and decision-quality studies compare layered
  explanation prototypes without ranking recommendations?
- **Priority:** Critical.

## Confidence

### RQ-CON-001

- **Question:** How should Opportunity Confidence be communicated so users understand evidence
  quality and do not interpret it as probability of personal success?
- **Why it matters:** Misinterpretation would violate the central confidence boundary.
- **Current assumption:** Dimension-level, limitation-rich language may be safer than one number.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Opportunity validation, evidence dimensions, explainability research.
- **Potential future experiments:** Could blinded comprehension interviews compare categorical,
  narrative, and dimension-profile presentations without inventing a formula?
- **Priority:** Critical.

## Future AI

### RQ-AI-001

- **Question:** Under what conditions can future AI assistance remain source-aware, reproducible,
  explainable, original, and under creator control?
- **Why it matters:** AI convenience must not become the source of market truth or opaque action.
- **Current assumption:** Grounding, provenance, evaluation, disclosure, and human approval are necessary.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** Mature Opportunity workflows, AI governance, rights/privacy/security review.
- **Potential future experiments:** Could red-team and user-control studies evaluate bounded planning
  assistance before creation or publishing capabilities are considered?
- **Priority:** Exploratory.

## Ethics

### RQ-ETH-001

- **Question:** Which harms, biases, incentives, and unequal data conditions could cause Opportunity
  Intelligence to disadvantage creators, audiences, markets, or existing creators?
- **Why it matters:** Evidence quality and explainability are incomplete without harm assessment.
- **Current assumption:** Language, region, creator scale, accessibility, privacy, and engagement
  incentives require explicit review.
- **Evidence available:** To be inventoried through a governed research plan.
- **Validation status:** Not started.
- **Dependencies:** All discovery capabilities, personas, recommendation philosophy, governance.
- **Potential future experiments:** Could participatory review, representative audits, and abuse-case
  analysis identify harms before user-facing recommendation policy?
- **Priority:** Critical.

## Relationships and traceability

Research questions do not authorize ADRs or implementation. A future plan cites its Research ID; a
finding cites the plan and evidence; a Product Decision cites the finding; a Feature Registry entry
and ADR cite the accepted decision; implementation and measurement cite the feature and ADR. Closed
questions remain here with links so conclusions cannot be detached from their original uncertainty.

## Future considerations

Add observations, owners, target review dates, plan/finding identifiers, and disposition links when
governed discovery begins. New questions should be neutral, bounded, falsifiable, and decision-relevant.

Related: [Product Lifecycle](PRODUCT_LIFECYCLE.md), [Product Governance](PRODUCT_GOVERNANCE.md),
[Feature Registry](FEATURE_REGISTRY.md), and [Decision Log](DECISION_LOG.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Created the canonical Product Discovery backlog with eleven unanswered questions. |
