# Product Principles

## Purpose

Define durable rules that constrain product design, research, recommendations, and trade-offs.

## Product Knowledge Status

**Status: Validated.** These principles are accepted Product governance constraints. They do not
validate a market hypothesis or mark any governed recommendation capability implemented.

## Table of contents

- [Scope](#scope)
- [Principles](#principles)
- [Applying the principles](#applying-the-principles)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Scope

These principles apply to every capability and recommendation. Changing one requires an explicit
Product decision, documented rationale, and review of affected research and technical boundaries.

## Principles

### PP-001: An opportunity requires multiple independent observations

**Rationale:** One video or creator may reflect luck, brand carry-over, paid distribution, news, or
an anomaly. **Practical implications:** Never recommend from one viral video. Require evidence
across videos and, for market claims, across channels. Show sample coverage and contradictions.

### PP-002: Channels and videos are evidence, not the product outcome

**Rationale:** Users need a direction they can test, not a list of interesting accounts.
**Practical implications:** Discovery must connect reference channels to topics, patterns, market
conditions, repeatability, and creator feasibility. A channel shortlist alone is incomplete.

### PP-003: Evidence quality outranks popularity

**Rationale:** Large counts can be stale, inaccessible, or poorly attributable. **Practical
implications:** Surface provenance, completeness, recency, missingness, sample diversity, and
eligibility. Do not confuse absolute reach with opportunity quality.

### PP-004: Recent evidence matters, but history provides context

**Rationale:** Opportunities change, while momentary spikes mislead. **Practical implications:**
Prioritize current observations for current decisions, retain historical context, and disclose the
window. Never call a short-lived event persistent without longitudinal support.

### PP-005: Repeatability matters more than isolated upside

**Rationale:** A creator needs a pattern they can reproduce. **Practical implications:** Examine
multiple examples, formats, publication cycles, and creators. Distinguish a repeatable content
pattern from a singular premise or event.

### PP-006: Small-creator evidence is essential

**Rationale:** Established creators may succeed through assets unavailable to a new entrant.
**Practical implications:** Include credible small-creator observations and do not use celebrity or
incumbent performance alone as proof of accessibility.

### PP-007: Recommendations must be explainable

**Rationale:** Users cannot responsibly act on an unexplained output. **Practical implications:**
Present supporting and opposing evidence, limitations, data age, reference examples, and the role
of creator-profile inputs. Avoid black-box scoring whenever a transparent structure is feasible.

### PP-008: Confidence describes evidence, not destiny

**Rationale:** Market evidence cannot predict an individual's execution or future platform state.
**Practical implications:** Opportunity Confidence must never be described as success probability.
Do not use probabilistic language unless an approved study supports that exact interpretation.

### PP-009: Recommendations must be reproducible

**Rationale:** Trust requires stable reasoning and auditability. **Practical implications:** Version
definitions, inputs, methods, and policies; preserve provenance and timestamps; separate facts from
judgment; make material changes traceable.

### PP-010: Product decisions are evidence driven and explicitly owned

**Rationale:** Engineering convenience is not Product authority. **Practical implications:** Research
may inform policy but cannot approve it. Thresholds, weights, claims, and user-facing meanings need
documented Product decisions and the reviews required by Decision Governance.

### PP-011: User trust is more valuable than recommendation volume

**Rationale:** Low-quality suggestions create false confidence and decision fatigue. **Practical
implications:** It is acceptable to return no recommendation. Prefer an honest “insufficient
evidence” state to relaxing standards silently.

### PP-012: Personalization respects feasibility without stereotyping

**Rationale:** Creator constraints determine accessibility, but profiles are incomplete and change.
**Practical implications:** Use explicit user-supplied constraints, permit correction, explain their
effect, and never infer sensitive characteristics or equate resource level with talent.

### PP-013: Uncertainty and contradictory evidence remain visible

**Rationale:** Public data is partial and markets evolve. **Practical implications:** Avoid false
precision, expose missing facts and counterexamples, distinguish unavailable from zero, and state
what would change the conclusion.

### PP-014: Recommendations support experiments, not irreversible bets

**Rationale:** Evidence becomes more useful through bounded real-world learning. **Practical
implications:** Encourage feasible tests, explicit hypotheses, review points, and user control.
Never imply a user must commit major resources because a recommendation exists.

### PP-015: Responsible originality over imitation

**Rationale:** Competitor evidence should inform market understanding, not copying. **Practical
implications:** Recommend patterns and unmet audience needs rather than replication of protected
expression, identity, thumbnails, scripts, or misleading tactics.

### PP-016: Every recommendation must be falsifiable by evidence

**Purpose:** Ensure a recommendation can be challenged and revised rather than protected by vague
language. **Why it exists:** A claim that cannot identify contradictory evidence cannot earn trust or
improve through learning. **Design implications:** Explanations state the bounded proposition,
supporting facts, counterevidence, missing facts, valid context, and conditions that would change the
recommendation. **Engineering implications:** Preserve evidence identities, timestamps, policy
versions, negative outcomes, and immutable recommendation context. **Example:** A recommendation
states that loss of cross-channel persistence would invalidate its market-timing premise; “this feels
promising” without a disconfirming condition violates the principle.

### PP-017: Unknown must remain Unknown

**Purpose:** Prevent missing or ambiguous facts from becoming fabricated certainty. **Why it exists:**
Public platform data is incomplete, and zero, false, absent, hidden, unsupported, and not-yet-observed
have different meanings. **Design implications:** Show unavailable and insufficient-evidence states
plainly, and permit the product to withhold conclusions. **Engineering implications:** Use explicit
typed states, reject impossible domains, preserve missingness provenance, and never default unknown
facts into policy-friendly values. **Example:** Hidden subscriber count remains unavailable; it is
not converted to zero or estimated to produce a ratio.

### PP-018: Research precedes implementation when Product knowledge is uncertain

**Purpose:** Keep implementation from hardening assumptions into accidental policy. **Why it exists:**
Code is costly evidence of commitment but not evidence that an idea is useful or true. **Design
implications:** Material unknowns become Research Questions before feature acceptance criteria.
**Engineering implications:** Require traceability from validated finding to Product Decision and,
where needed, ADR before building; prototypes must be labelled as research and isolated from runtime.
**Example:** Confidence presentation undergoes comprehension research before any numeric confidence
UI or service is proposed.

### PP-019: Product language must remain consistent across artifacts and implementation

**Purpose:** Preserve one understandable meaning for core concepts. **Why it exists:** Terminology
drift can silently turn evidence into signals, hypotheses into facts, or confidence into probability.
**Design implications:** Interfaces and research use the Domain Model and state distinctions.
**Engineering implications:** Contracts, schemas, tests, APIs, logs, and documentation use governed
names or explicitly map technical terms; changing meaning requires a Product decision and migration
review. **Example:** A “Topic” field cannot silently contain a Niche classification, and a class named
`Opportunity` cannot make an unvalidated candidate a Product Opportunity.

### PP-020: Future AI must remain explainable and subordinate to governed evidence

**Purpose:** Prevent generative convenience from becoming opaque Product authority. **Why it exists:**
AI may produce plausible but unsupported classifications, explanations, or actions. **Design
implications:** Users can identify AI involvement, inspect sources and limitations, correct outputs,
and retain final control. **Engineering implications:** Version models and methods, preserve grounding
and provenance, evaluate failure modes, separate deterministic facts from generated text, and block
unreviewed external actions. **Example:** An AI-generated content brief cites the selected Opportunity
evidence and is editable; an unexplained model-generated Opportunity score violates the principle.

### PP-021: Product Knowledge Status must be explicit

**Purpose:** Make the difference between desired direction, assumptions, research, validated findings,
and code visible at the point of use. **Why it exists:** Documentation can otherwise make a future
idea appear real simply by describing it in present tense. **Design implications:** Product documents
declare Vision, Hypothesis, Research In Progress, Validated, Implemented, or a precisely scoped
composite. **Engineering implications:** Only repository verification supports Implemented; agents
must check status before deriving requirements, and mixed-state documents identify boundaries.
**Example:** Channel acquisition may be an Implemented Foundation while competitor selection in the
same capability area remains Future Vision.

## Applying the principles

Feature proposals must name applicable principles and document tensions. A roadmap status does not
waive a principle. Exceptions require a Product Decision Log entry and, where architecture changes,
an ADR. Reviews should ask whether the feature increases evidence quality, accessibility, clarity,
reproducibility, and user control.

## Future considerations

Validate these principles with creators and specialists in responsible recommendation systems.
Add principles only when they constrain meaningful choices; do not turn implementation preferences
into Product doctrine.

Related: [Recommendation Philosophy](RECOMMENDATION_PHILOSOPHY.md),
[Opportunity Confidence](OPPORTUNITY_CONFIDENCE.md), and [Decision Log](DECISION_LOG.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Established fifteen governing Product principles. |
| 1.1 | 2026-07-24 | Added research, falsifiability, unknown-state, language, AI, and status principles. |
