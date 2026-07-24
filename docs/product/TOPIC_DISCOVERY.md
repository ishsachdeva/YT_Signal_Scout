# Topic Discovery

## Purpose

Define the future philosophy for identifying and validating the subjects addressed by content.

## Product Knowledge Status

**Status: Hypothesis.** Potential sources and safeguards are research assumptions. No topic
extraction, semantic analysis, taxonomy, LLM workflow, or Product feature is implemented.

## Table of contents

- [Role of topics](#role-of-topics)
- [Potential sources](#potential-sources)
- [Discovery philosophy](#discovery-philosophy)
- [Quality and governance](#quality-and-governance)
- [Scope and limitations](#scope-and-limitations)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Role of topics

A Topic is a subject, question, entity, or problem expressed by content. Topic evidence helps group
videos, identify recurring audience needs, describe channel portfolios, find content patterns, and
form niche hypotheses. A topic is not automatically a keyword, trend, niche, or opportunity.

## Potential sources

Future research may examine titles, descriptions, transcripts/captions, thumbnails, tags and other
metadata, playlists, linked entities, semantic representations, and language models. Sources differ
in reliability and meaning: a title may frame a promise, a transcript may reveal actual coverage,
and a thumbnail may communicate positioning. No source should silently dominate without validation.

LLMs and semantic analysis are possible research tools only. Their outputs would require explicit
models, versions, prompts or method identity, reproducibility expectations, human review, error
analysis, privacy/security review, and evidence provenance before Product use.

## Discovery philosophy

Topic Discovery should preserve source evidence, distinguish explicit mention from inferred meaning,
allow multiple topics and hierarchy, retain uncertainty, and respect language/region context. Human
understandability matters more than taxonomic cleverness. Topic identity must be stable enough for
longitudinal comparison while permitting governed aliases and evolution.

## Quality and governance

Validation should examine precision, recall, ambiguity, multilingual behaviour, entity confusion,
spam/metadata mismatch, transcript availability, and thumbnail interpretation. Research datasets
must represent different formats, creator scales, languages, and domains. Product decisions must
define what level of topic evidence is sufficient for each user-facing use.

## Scope and limitations

No extraction, clustering, embedding, ontology, AI feature, algorithm, or confidence formula is
approved here. Topics derived from public metadata may misrepresent the actual audience need.
Copyrighted content must not be reproduced beyond authorized and necessary evidence use.

## Future considerations

Study topic granularity, hierarchy, identity/versioning, multilingual normalization, human review,
semantic drift, source conflicts, and the boundary between topic and content pattern.

Related: [Niche Discovery](NICHE_DISCOVERY.md), [Trend Discovery](TREND_DISCOVERY.md), and
[Product Principles](PRODUCT_PRINCIPLES.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Defined future topic-discovery philosophy and research boundaries. |
| 1.1 | 2026-07-24 | Marked source and method concepts as unvalidated hypotheses. |
