# ADR-028: Govern Channel Intelligence as a Factual Research Boundary

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## 1. Decision

Add a versioned immutable Channel Intelligence context under offline research. It consumes one
canonical channel and video population, invokes Eligible Video Policy v1 once, and emits
channel-level descriptive facts with source and result SHA-256 integrity. It is the canonical
source of channel-level research characteristics.

## 2. Boundaries

The pure synchronous service owns binding, canonical-order validation, factual population and
quality summaries, subscriber-relative arithmetic, upload timing, descriptive distributions, and
serialization. It performs no acquisition, persistence, API, workflow, AI, interpretation,
inference, confidence, comparison, ranking, scoring, recommendation, policy, or signal generation.
It is absent from application startup.

Standard videos, Shorts, and completed livestream replays remain separately counted under ADR-008.
Whole-eligible-population statistics are descriptive and are not a format baseline or policy input.

## 3. Ordering and integrity

Schema v1 orders publication time ascending, then video ID, with missing times last. This research
order does not alter acquisition discovery order; callers construct it explicitly. The request
digest covers the immutable channel and ordered population. The result binds source digest,
versions, identities, evaluation time, schema, and canonical result digest.

## 4. Mathematical availability

Empty populations are valid and expose unavailable distribution/interval fields. Ratios require a
visible positive subscriber count; hidden, missing, or zero counts are factual states with nullable
derived fields. Emitted numbers must be finite and within declared domains.

## 5. Consequences

- Future research can consume one stable factual artifact without duplicating policy.
- Mutation, ordering drift, identity mismatch, and corruption fail explicitly.
- Formula or ordering changes require versioned schema evolution.
