# Product Domain Model

## Purpose

Establish the ubiquitous language for Product, research, design, and engineering. These are product
concepts, not a database or class design.

## Product Knowledge Status

**Status: Validated.** The vocabulary is accepted for Product communication. Concept acceptance does
not imply that corresponding persistence models, APIs, services, or user features are implemented.

## Table of contents

- [Scope and relationship map](#scope-and-relationship-map)
- [Evidence objects](#evidence-objects)
- [Market structure](#market-structure)
- [People and feasibility](#people-and-feasibility)
- [Decision concepts](#decision-concepts)
- [Research concepts](#research-concepts)
- [Context concepts](#context-concepts)
- [Language rules](#language-rules)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Scope and relationship map

```text
Video -> Channel -> Observation -> Evidence -> Signal
  |         |                         |
  +-> Topic +-> Competitor            v
          Topic + Format + Audience -> Niche -> Opportunity Candidate
Trend -------------------------------------------|
Creator Profile + Production Complexity --------|
Research ----------------------------------------v
                                  Opportunity -> Confidence -> Recommendation
```

Relationships express conceptual flow, not approved algorithms.

## Evidence objects

### Video

**Definition:** One published YouTube content item observed through an authorized source.
**Purpose:** Supplies content, format, timing, and performance facts. **Example:** A public ten-minute
tutorial uploaded last week. **Relationships:** Belongs to a Channel; expresses Topics, Formats, and
Content Patterns; generates Observations. **Not:** Proof of a niche, a trend, or an opportunity by
itself.

### Channel

**Definition:** A YouTube publishing identity and its observable content population at a stated
time. **Purpose:** Groups creator behaviour and repeated evidence. **Example:** A public educational
channel with thirty eligible uploads. **Relationships:** Publishes Videos; may enter a Competitor
reference set; contributes Evidence. **Not:** The final recommendation, a creator's complete
business, or a stable proxy for a niche.

### Format

**Definition:** The audience-facing delivery form of content, such as standard video, Short, or
livestream replay, plus future presentation categories validated by research. **Purpose:** Prevents
inappropriate comparison and clarifies production needs. **Example:** Narrated long-form explainer.
**Relationships:** Qualifies Videos, Content Patterns, Niches, and Production Complexity. **Not:** A
Topic or a quality judgment.

### Content Pattern

**Definition:** A recurring, observable way of framing and delivering content across multiple
examples. **Purpose:** Describes potentially repeatable execution. **Example:** “Beginner mistake,
demonstration, corrected result” tutorials. **Relationships:** Combines Topics, Formats, hooks, and
structures; supports repeatability evidence. **Not:** A copied script, single title template, or
guaranteed formula.

### Evidence

**Definition:** A traceable fact or governed research result relevant to a claim. **Purpose:**
Supports, contradicts, or limits assessment. **Example:** Five unrelated small channels repeatedly
publish videos on the same problem with current audience response. **Relationships:** Derived from
Observations and Studies; evaluated across quality dimensions; supports Signals and Opportunities.
**Not:** An opinion, an unexplained score, or certainty.

### Signal

**Definition:** A versioned Product interpretation of qualified evidence under an approved rule.
**Purpose:** Expresses one bounded condition relevant to opportunity assessment. **Example:** A
governed statement that subscriber-relative reach is sustained across eligible videos.
**Relationships:** Consumes Evidence; may support or oppose an Opportunity Candidate. **Not:** Raw
metrics, Confidence, a recommendation, or an opportunity by itself.

### Observation

**Definition:** A time-bound, immutable record of specified facts about a domain object.
**Purpose:** Preserves what was known and when. **Example:** Channel statistics and canonical video
facts captured at a stated instant. **Relationships:** Enters Research and becomes Evidence after
qualification. **Not:** A live mutable profile, causal claim, or interpretation.

## Market structure

### Topic

**Definition:** A recognizable subject, question, entity, or problem addressed by content.
**Purpose:** Provides the smallest useful semantic unit for organizing demand and supply evidence.
**Example:** “Home espresso grinder calibration.” **Relationships:** Appears in Videos; groups into
Niches and Content Patterns; may trend. **Not:** Necessarily a keyword, niche, market, or opportunity.

### Trend

**Definition:** A time-dependent directional change in attention, production, behaviour, or
performance around a subject or pattern. **Purpose:** Adds lifecycle and timing evidence.
**Example:** Rapid multi-channel growth in interest around a newly released tool. **Relationships:**
May affect Topics, Niches, Formats, or Markets. **Not:** Any popular topic, one spike, or a durable
niche.

### Niche

**Definition:** A coherent audience need and content territory with recognizable creators,
subjects, formats, and expectations. **Purpose:** Defines a market context broad enough for repeated
content but specific enough for relevant comparison. **Example:** Practical espresso education for
home beginners. **Relationships:** Contains Topics and Micro-Niches; exists within Markets; provides
context for Opportunities. **Not:** A single keyword, channel category, or automatic recommendation.

### Micro-Niche

**Definition:** A narrower audience/problem/format intersection within a Niche. **Purpose:** Makes
specific supply gaps and creator accessibility inspectable. **Example:** Low-cost espresso dialing
for users of entry-level grinders. **Relationships:** Specializes a Niche and groups focused Topics
and Content Patterns. **Not:** Merely a very small audience or one video idea.

### Opportunity Candidate

**Definition:** A proposed, not-yet-validated intersection of audience need, content territory,
market timing, repeatability, and possible creator access. **Purpose:** Gives research a claim to
test. **Example:** Beginner-friendly repair explainers for an underserved device category.
**Relationships:** Accumulates supporting, opposing, and missing Evidence before becoming or failing
to become an Opportunity. **Not:** A recommendation or validated opening.

### Opportunity

**Definition:** A versioned, bounded market proposition supported by sufficient governed evidence
that a specified content direction is worth a feasible creator experiment under stated conditions.
**Purpose:** It is the platform's primary decision asset. **Example:** A persistent micro-niche with
multi-channel small-creator evidence, repeatable patterns, and production demands compatible with a
profile. **Relationships:** Synthesizes Niche, Topic, Trend, Competitor, feasibility, and research
evidence; receives Confidence; may support a Recommendation. **Not:** A success prediction, score,
channel, keyword, guarantee, or instruction to copy.

### Competitor

**Definition:** A channel selected as a relevant reference for a defined opportunity, market, and
creator context. **Purpose:** Supplies comparative evidence about content supply, expectations,
patterns, and accessibility. **Example:** A small independent channel addressing the same audience
need in the target language. **Relationships:** Belongs to a versioned reference set; may be small,
established, adjacent, or contrasting. **Not:** An enemy, permanent label, or synonymous with every
channel in a niche.

### Market

**Definition:** The bounded environment in which audience demand and creator supply are considered,
including platform, region, language, and relevant audience conditions. **Purpose:** Prevents claims
from being generalized beyond observed context. **Example:** English-language YouTube viewers in
India seeking entry-level personal finance education. **Relationships:** Contains Niches, audiences,
competitors, and opportunities. **Not:** Geography alone or total addressable market revenue.

## People and feasibility

### Creator

**Definition:** A person or team intending to produce and publish content. **Purpose:** Identifies
the decision-maker whose goals and constraints determine accessibility. **Example:** A beginner with
six weekly hours and no on-camera preference. **Relationships:** Owns a Creator Profile and evaluates
Recommendations. **Not:** Necessarily the owner of any observed Channel or a fixed persona.

### Creator Profile

**Definition:** An explicit, user-controlled snapshot of goals, preferences, capabilities, and
constraints relevant to opportunity fit. **Purpose:** Personalizes feasibility without claiming to
predict talent. **Example:** Hindi/English, low budget, screen-recording skill, weekly schedule.
**Relationships:** Filters or contextualizes Opportunities and Recommendations. **Not:** A
psychological profile, sensitive-trait inference, permanent identity, or success score.

### Audience

**Definition:** A group of viewers connected by a relevant need, context, or behaviour.
**Purpose:** Anchors content value and market boundaries. **Example:** First-time users learning a
specific editing tool. **Relationships:** Has needs addressed by Topics and Niches within a Market.
**Not:** Only demographics, subscriber counts, or guaranteed demand.

### Production Complexity

**Definition:** The observable and user-declared resources needed to produce a content pattern at a
credible cadence. **Purpose:** Assesses accessibility. **Example:** Multi-location filming, expert
demonstration, and ten editing hours per video. **Relationships:** Compared with Creator Profile
constraints. **Not:** Content quality, creator ability, or a universal numeric difficulty.

### Monetization Potential

**Definition:** Evidence about plausible monetization mechanisms available in a bounded market,
subject to eligibility and uncertainty. **Purpose:** Helps align opportunities with goals.
**Example:** Observable affiliate relevance plus advertiser-supported demand. **Relationships:** One
future evidence dimension for an Opportunity. **Not:** revenue prediction, sponsorship valuation,
financial advice, or guaranteed YPP eligibility.

## Decision concepts

### Confidence

**Definition:** A communicated assessment of the sufficiency, consistency, diversity, recency, and
quality of evidence supporting an Opportunity. **Purpose:** Shows how strongly the evidence supports
consideration. **Example:** Moderate evidence confidence due to cross-channel consistency but short
history. **Relationships:** Belongs to a specific Opportunity version and evidence basis. **Not:**
Probability of creator success, forecast, or certainty. See [Opportunity Confidence](OPPORTUNITY_CONFIDENCE.md).

### Recommendation

**Definition:** A transparent, contextual Product suggestion that a creator consider, test, defer,
or reject an Opportunity, with reasons and limitations. **Purpose:** Converts evidence into a
user-controlled next decision. **Example:** Test three low-cost explainers while monitoring whether
the observed pattern persists. **Relationships:** Binds Opportunity, Confidence, Creator Profile,
evidence, and policy. **Not:** A command, guarantee, unexplained ranking, or autonomous action.

## Research concepts

### Research

**Definition:** A governed process for producing reproducible knowledge from observations.
**Purpose:** Tests claims, data quality, definitions, and candidate policies before Product adoption.
**Example:** Evaluating whether a proposed multi-channel evidence condition distinguishes labelled
opportunities. **Relationships:** Uses Studies and Observations and produces evidence for decisions.
**Not:** Product approval, ad hoc browsing, or an implementation milestone.

### Study

**Definition:** A versioned research plan and its bound execution/evaluation artifacts.
**Purpose:** Makes a particular question, method, cohort, and result auditable. **Example:** A
pre-declared evaluation of a candidate evidence rule. **Relationships:** Part of Research; consumes
Observations and may produce Evidence. **Not:** A production experiment, Product decision, or
permission to deploy a threshold.

## Context concepts

### Region

**Definition:** A declared geographic context relevant to availability, culture, language, policy,
or audience behaviour. **Purpose:** Bounds generalization. **Example:** India. **Relationships:**
Qualifies Markets, creators, and evidence. **Not:** Nationality inference or a complete market.

### Language

**Definition:** The declared language context of content and intended audience, including relevant
multilingual combinations. **Purpose:** Supports accessibility and valid comparison. **Example:**
Hindi with English technical terms. **Relationships:** Qualifies Videos, Markets, audiences, and
Creator Profiles. **Not:** Automatically inferable from country or metadata alone.

## Language rules

Use “candidate” before evidence validation, “opportunity” only after approved qualification,
“confidence” only for evidence quality, “recommendation” only for a transparent Product output, and
“observation” for time-bound facts. Never use “viral” as evidence of repeatability, “competitor” as
a permanent channel type, or “probability” as a synonym for confidence.

## Future considerations

Research must validate classifications for content patterns, audiences, production complexity, and
monetization evidence before implementation. New terms require examples, relationships, exclusions,
and a Decision Log entry if they change Product meaning.

Related: [Niche Discovery](NICHE_DISCOVERY.md), [Opportunity Engine](OPPORTUNITY_ENGINE.md), and
[Product Principles](PRODUCT_PRINCIPLES.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Established the v0.10.0 ubiquitous language. |
| 1.1 | 2026-07-24 | Declared vocabulary knowledge status without changing definitions. |
