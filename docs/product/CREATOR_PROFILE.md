# Creator Profile

## Purpose

Define future user-supplied onboarding context for accessible, explainable personalization.

## Product Knowledge Status

**Status: Implemented Foundation + Future Vision.** An immutable deterministic contract for the
repository owner's explicit facts is implemented in v0.10.1. Personalization effects, persistence,
privacy controls, onboarding interfaces, and multi-user behavior remain unvalidated and unimplemented.

## Table of contents

- [Role and scope](#role-and-scope)
- [Potential attributes](#potential-attributes)
- [Personalization](#personalization)
- [Implemented v0.10.1 contract](#implemented-v0101-contract)
- [User control and safeguards](#user-control-and-safeguards)
- [Limitations](#limitations)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Role and scope

A Creator Profile is an editable snapshot of goals, preferences, capabilities, and constraints. It
helps assess whether an Opportunity's production demands and market context are accessible to a
specific user. It is not a prediction of talent, identity, commitment, or success.

## Potential attributes

Future onboarding may ask for country/region, content and audience languages, target market, budget
range, editing ability, comfort showing face, voice preferences including AI voice, equipment and
production capability, feasible publishing frequency, weekly hours, interests, knowledge domains,
monetization goal, preferred styles/formats, collaboration access, and existing channel context.

Every question needs a clear purpose, an option not to answer where possible, appropriate value
ranges, and a statement of how it may affect results. “Can show face” is a production preference,
not a measure of credibility. AI-voice preference does not authorize generation or imply platform
policy compliance.

## Personalization

Profile facts may help exclude clearly infeasible production patterns, prioritize relevant markets
and languages, explain resource gaps, present alternatives, or shape a bounded experiment. The
platform should distinguish market evidence from personal fit: a strong Opportunity may be a poor
fit for one profile, while low fit does not invalidate the market proposition.

The implemented foundation performs none of these actions. RQ-CRT-001 and RQ-PRD-001 remain open;
recording facts is not evidence that they improve relevance or measure feasibility.

## Implemented v0.10.1 contract

PD-008 and ADR-030 authorize one opaque profile identity, explicit schema/profile versions, and
these optional self-declared facts:

- preferred presentation style: faceless, on-camera, or mixed;
- AI-assistance preference: avoid, open, or prefer;
- one canonical lower-case language preference;
- one upper-case two-letter target-geography code shape;
- available production hours per week from zero through 168;
- self-assessed editing capability;
- narration preference;
- self-declared relative production-budget category; and
- upload-cadence goal.

`None` means Unknown and remains serialized as `null`. Zero weekly hours and “no current cadence
goal” are explicit facts, not Unknown. Categories carry no inferred quality, affordability, skill,
policy compliance, or fit meaning. The value object is immutable, rejects extra fields, uses no
clock or random defaults, and supports canonical compact UTF-8 JSON and SHA-256 content identity.

## User control and safeguards

Users must be able to review, edit, remove, and understand profile data and its influence. The
system should avoid sensitive-trait inference, stereotyping, hidden proxies, and unnecessary
collection. Missing answers mean unknown, not “no capability.” Personalization should provide
reasons and allow users to explore outside profile defaults.

## Limitations

Self-reported skill and capacity are contextual and may change. Production feasibility cannot fully
capture motivation, originality, learning speed, access, platform policy, or life circumstances.
The profile does not justify a success probability or high-stakes financial recommendation.

## Future considerations

Validate questionnaire burden, privacy/security requirements, retention and consent, accessibility,
internationalization, profile versioning, team profiles, inferred-versus-declared boundaries, and
fairness before implementation.

Related: [User Personas](USER_PERSONAS.md), [Recommendation Philosophy](RECOMMENDATION_PHILOSOPHY.md),
and [Opportunity Confidence](OPPORTUNITY_CONFIDENCE.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Defined future creator-profile inputs and safeguards. |
| 1.1 | 2026-07-24 | Marked the Creator Profile as unimplemented future Vision. |
| 1.2 | 2026-07-24 | Documented the implemented v0.10.1 factual foundation and future boundaries. |
