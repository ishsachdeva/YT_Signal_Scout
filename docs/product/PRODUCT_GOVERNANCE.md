# Product Governance

## Purpose

Define how Product knowledge evolves, who owns each decision, which documents are authoritative, and
how a customer problem becomes measured implementation without confusing intent with reality.

## Product Knowledge Status

**Status: Validated.** The governance distinctions in this document are accepted repository policy.
They describe how work is governed; they do not validate any market hypothesis or mark a feature
implemented.

## Table of contents

- [Scope](#scope)
- [Knowledge states](#knowledge-states)
- [Responsibilities](#responsibilities)
- [Document precedence](#document-precedence)
- [Traceability](#traceability)
- [Review expectations](#review-expectations)
- [From decision to implementation](#from-decision-to-implementation)
- [Drift prevention](#drift-prevention)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Scope

This governance applies to Product Architecture, discovery, research, Product decisions, technical
architecture, implementation claims, and measurement. It does not replace repository Decision
Governance, ADR rules, research protocols, testing standards, or approval ownership.

## Knowledge states

Every Product Architecture document declares one current state:

| State | Exact meaning |
|---|---|
| **Vision** | A desired future direction or capability. It is not validated, approved for implementation, or implemented. |
| **Hypothesis** | A testable assumption that may be supported, contradicted, or refined by research. It is not validated knowledge or Product policy. |
| **Research In Progress** | A governed question or study is actively gathering/evaluating evidence. No conclusion or implementation authority is implied. |
| **Validated** | Sufficient governed evidence or an accepted governance decision supports the stated finding within explicit scope and limitations. It is not automatically implemented. |
| **Implemented** | Repository code, tests, and documentation verify the capability exists within stated boundaries. Implementation does not prove market value or validate every underlying hypothesis. |

When a document spans different realities, it may declare a composite such as **Implemented
Foundation + Future Vision**, but it must identify which parts are implemented. “Planned,” “defined,”
“documented,” and “on the roadmap” are never synonyms for Implemented.

## Responsibilities

| Layer | Primary owner | Responsibility | Output | Must not do |
|---|---|---|---|---|
| Vision | Product Owner | Define mission, users, problems, and desired outcomes | Vision and principles | Claim validation or implementation |
| Research | Research/Analytics, reviewed by Product | Ask questions and produce reproducible evidence | Plans, studies, findings | Approve Product policy automatically |
| Product | Product Owner with required reviews | Decide user-facing meaning, scope, and policy | Decision Log/PDR, registry updates | Infer implementation from intent |
| Architecture | Engineering with Product traceability | Decide technical boundaries and structure | ADR/TRD updates | Invent Product behaviour |
| Engineering | Engineering | Design and build approved scope | Code and technical documentation | Redefine domain language silently |
| Implementation | Engineering and reviewers | Verify shipped capability and boundaries | Tests, runtime docs, changelog | Claim customer outcomes from test passage |
| Testing | Engineering/QA/Research as applicable | Verify behavior or research method against stated criteria | Test/evaluation evidence | Substitute for Product acceptance |

## Document precedence

Specialized authority applies rather than one document overriding every other document:

1. Product Vision, Principles, Domain Model, and accepted Product decisions govern Product intent.
2. `RESEARCH_QUESTIONS.md` governs unanswered discovery questions; research protocols and immutable
   artifacts govern methods and findings.
3. The Signal Catalog and accepted PDRs govern signal and recommendation policy where applicable.
4. ADRs, TRD, and Engineering Principles govern technical structure.
5. Source code and tests govern verified implementation behavior.
6. The Changelog and feature documentation report verified release status.

Historical PRD/TRD files remain context. A conflict must be resolved through the owning decision
record, never by choosing whichever document is convenient.

## Traceability

Every proposed implementation should trace:

```text
Customer problem -> Vision/Principle -> Research Question -> Evidence/Finding
  -> Product Decision -> Feature Registry -> ADR/technical design
  -> Code and tests -> Release record -> Measurement -> Iteration
```

Each transition names identifiers or links. Missing traceability is a blocker, not an invitation to
invent assumptions.

## Review expectations

- Vision changes require Product review and a Decision Log entry.
- Research plans require method, cohort, evidence-quality, and limitation review.
- Validated findings require reproducible artifacts and scope statements.
- Product policy requires Product ownership and the reviews defined by Decision Governance.
- Architecture changes require an ADR that cites Product intent and accepted decisions.
- Implementation requires acceptance criteria, security/privacy review where relevant, tests, and
  synchronized documentation.
- “Implemented” claims require repository verification, not roadmap or document presence.

## From decision to implementation

An accepted Product Decision states what behavior is authorized and why. The Feature Registry binds
it to dependencies and status. Engineering then decides how through an ADR when architecture is
materially affected. Work is implemented and tested against explicit acceptance criteria. Only after
verification may documents declare Implemented. Measurement then tests whether the capability
addresses the customer problem; a poor outcome triggers iteration rather than rewriting history.

## Drift prevention

Use stable domain terms, explicit knowledge states, revision histories, append-only decisions,
versioned research, implementation audits, and cross-link checks. Never use future tense without a
Vision/Hypothesis marker, or present tense for behavior that is not verified. When mixed-state
documents exist, label paragraphs or sections whose status differs from the document default.

## Future considerations

Add named decision owners, review service levels, automated link/status linting, and implementation
traceability reports when repository scale justifies them.

Related: [Product Lifecycle](PRODUCT_LIFECYCLE.md), [Research Questions](RESEARCH_QUESTIONS.md),
[Decision Log](DECISION_LOG.md), and [Decision Governance](../governance/DECISION_GOVERNANCE.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Established Product knowledge states, ownership, precedence, and traceability. |
