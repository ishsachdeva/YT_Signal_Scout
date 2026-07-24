# Recommendation Philosophy

## Purpose

Define how future Opportunity recommendations should earn trust and support responsible decisions.

## Product Knowledge Status

**Status: Vision.** These are desired recommendation behaviors and constraints. No recommendation
policy, engine, ranking, narrative, UI, AI system, or external action is implemented.

## Table of contents

- [Role](#role)
- [Required behaviour](#required-behaviour)
- [Explanation anatomy](#explanation-anatomy)
- [Uncertainty and limitations](#uncertainty-and-limitations)
- [Responsible recommendations](#responsible-recommendations)
- [Scope](#scope)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Role

A recommendation is a contextual suggestion that a user consider, test, defer, or reject a bounded
Opportunity. It converts governed evidence and Product policy into a user-controlled next decision.
It is not an instruction, promise, channel ranking, or substitute for creative judgment.

## Required behaviour

Recommendations should be transparent, explainable, evidence-linked, reproducible, current,
profile-aware where consented, proportionate to evidence, and candid about uncertainty. They should
prefer a smaller number of defensible options over volume, preserve contradictory evidence, allow
inspection and correction, and make “insufficient evidence” a normal outcome.

Recommendations must separate:

1. observable facts;
2. governed research conclusions;
3. Product interpretation and policy;
4. creator-profile fit;
5. the suggested next experiment or decision.

## Explanation anatomy

A future explanation should identify the Opportunity and market, why it was considered, relevant
audience need, evidence basis and freshness, multiple reference channels/videos, repeatable patterns,
profile-fit factors, Opportunity Confidence meaning, counterevidence, missing facts, important
limitations, and conditions that would trigger reassessment. Users should be able to trace material
claims to source or governed artifact identities without being overwhelmed by implementation detail.

## Uncertainty and limitations

Use qualified language such as “evidence supports considering” rather than “will succeed.” State
when public data is incomplete, subscriber facts are hidden/rounded, classifications are uncertain,
trends may be temporary, or creator resources are unknown. Avoid pseudo-precision. Do not translate
Opportunity Confidence into outcome probability.

## Responsible recommendations

Recommendations should encourage bounded, affordable, reversible experiments and original value.
They must not encourage copyright infringement, deceptive tactics, unsafe conduct, exploitative
content, policy evasion, or major financial commitment based solely on platform evidence. Users
retain control over publishing and creative decisions. Profile personalization must avoid sensitive
inference and stereotypes.

When evidence is weak or conflicting, the system should ask for context, recommend further research,
offer a safer alternative, or decline to recommend. Withholding is a quality feature.

## Scope

No recommendation policy, ranking, threshold, UI, generative narrative, AI system, workflow, or
autonomous action is approved here. Exact claims and behaviours require future Product decisions,
research validation, safety review, and implementation ADRs.

## Future considerations

Test explanation comprehension, confidence misinterpretation, comparison effects, recommendation
fatigue, fairness across languages/markets, creator agency, experimentation support, feedback loops,
and AI-generated explanation safeguards before implementation.

Related: [Product Principles](PRODUCT_PRINCIPLES.md), [Creator Profile](CREATOR_PROFILE.md), and
[Opportunity Confidence](OPPORTUNITY_CONFIDENCE.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Established transparent and responsible recommendation behaviour. |
| 1.1 | 2026-07-24 | Marked recommendation behavior as Vision rather than implementation. |
