# Product Lifecycle

## Purpose

Define the governed path from a customer problem to measured implementation and iteration.

## Product Knowledge Status

**Status: Validated.** This lifecycle is accepted governance. It does not imply that any individual
research question, Product hypothesis, feature, or outcome has completed the lifecycle.

## Table of contents

- [Scope](#scope)
- [Lifecycle](#lifecycle)
- [Stage definitions](#stage-definitions)
- [Ownership](#ownership)
- [Entry and exit discipline](#entry-and-exit-discipline)
- [Traceability](#traceability)
- [Failure and iteration](#failure-and-iteration)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Scope

The lifecycle applies to material Product capabilities and policies. It describes governance, not a
delivery methodology, workflow engine, implementation sequence inside a sprint, or automatic gate.

## Lifecycle

```text
Problem
  -> Observation
  -> Research Question
  -> Research Plan
  -> Evidence
  -> Validated Finding
  -> Product Decision
  -> Architecture
  -> Implementation
  -> Measurement
  -> Iteration
```

Stages may return to earlier stages. Skipping a stage requires an explicit rationale and cannot
erase the responsibilities of the skipped stage.

## Stage definitions

| Stage | Owner | Entry | Output | Exit criteria |
|---|---|---|---|---|
| Problem | Product | A user or market difficulty is observed | Bounded problem statement and affected persona | Problem, context, non-goals, and desired decision are clear |
| Observation | Product/Research | A bounded problem exists | Traceable qualitative or quantitative observation | Source, time, limitations, and relevance are recorded |
| Research Question | Product/Research | An unknown blocks a decision | Question with ID, priority, assumptions, and dependencies | Question is answerable, neutral, and linked to the problem |
| Research Plan | Research/Analytics | A prioritized question exists | Pre-declared method, evidence needs, review, and acceptance plan | Method and governance review complete |
| Evidence | Research/Analytics | Approved plan and inputs exist | Reproducible observations and results | Integrity, quality, limitations, and provenance validated |
| Validated Finding | Research with Product review | Sufficient evidence exists | Scoped finding that supports, contradicts, or leaves uncertainty | Required review accepts the finding within stated limits |
| Product Decision | Product Owner | Finding and alternatives are available | Accepted, rejected, or deferred Product policy | Ownership, rationale, impacts, and traceability recorded |
| Architecture | Engineering with Product | Approved Product behavior needs structure | ADR/TRD/design boundary | Product alignment and engineering review complete |
| Implementation | Engineering | Approved scope and design exist | Code, migrations/configuration if authorized, tests, docs | Acceptance, security, quality, and release gates pass |
| Measurement | Product/Analytics | Verified capability is usable | Outcome and behavior evidence | Measures are interpretable and limitations recorded |
| Iteration | Product and owning teams | Measurement or changed context warrants action | New problem, question, decision, or revision | History retained and next lifecycle path explicit |

## Ownership

Product owns customer problems, vision, user-facing meaning, and Product decisions. Research and
Analytics own method integrity and findings, not policy adoption. Engineering owns technical design
and verified implementation, not Product meaning. Testing verifies stated criteria, not market
value. Measurement is jointly interpreted but cannot retroactively alter historical evidence.

## Entry and exit discipline

An entry criterion prevents work from beginning on an undefined basis. An exit criterion establishes
the minimum artifact needed for the next stage. “Document created” does not mean “finding validated.”
“ADR accepted” does not mean “implemented.” “Tests pass” does not mean “customer problem solved.”
Each output declares its Product Knowledge Status.

## Traceability

Research IDs connect problems and questions to plans/findings. Decision IDs connect findings to
Product policy. Feature IDs connect policy to roadmap scope. ADR IDs connect approved behavior to
technical design. Commits, tests, and release notes connect design to implementation. Measurement
references the exact implemented version and decision basis.

## Failure and iteration

Contradictory or insufficient evidence returns the work to the question or plan; it does not justify
weaker standards. Rejected Product decisions remain recorded. Architecture constraints may return a
decision for Product reconsideration. Failed implementation gates return to design or engineering.
Unexpected measurements create new observations and questions rather than unsupported causal claims.

## Future considerations

Define lightweight and full lifecycle variants by risk, establish artifact templates, and automate
traceability checks only after teams have used this model and identified genuine friction.

Related: [Product Governance](PRODUCT_GOVERNANCE.md), [Research Questions](RESEARCH_QUESTIONS.md), and
[Decision Log](DECISION_LOG.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Defined stages, ownership, outputs, criteria, and feedback loops. |
