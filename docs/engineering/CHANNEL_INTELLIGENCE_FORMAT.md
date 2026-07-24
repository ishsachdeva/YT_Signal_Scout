# Channel Intelligence Format

## Purpose

Channel Intelligence schema version 1 transforms exactly one immutable canonical `Channel` and
its canonical `Video` population into content-addressed descriptive facts. It is an offline
research boundary. It does not interpret metrics, compare or rank channels, create signals,
recommend action, call AI or external services, persist data, or expose an API.

## Input and ordering

`ChannelIntelligenceRequest` contains a timezone-aware evaluation time, one versioned definition,
one versioned configuration, one immutable channel, an immutable tuple of canonical videos, and a
SHA-256 source digest. Bindings must match exactly. Schema v1 order is publication time ascending,
then video ID ascending, with missing publication times last. Video IDs must be unique and every
video must bind to the supplied channel. Malformed or future timestamps are rejected.

## Populations and calculations

The service invokes Eligible Video Policy v1 once. `eligible_videos` is the union of eligible
standard videos, Shorts, and completed livestream replays; format counts remain separate. Earliest
and latest upload describe all supplied videos with publication times. Upload behaviour and view
distributions describe eligible videos.

- Upload frequency is eligible uploads per seven elapsed days over a minimum one-day span; a
  single video returns `1.0`.
- Consecutive intervals use ascending eligible timestamps. Empty and single-video populations have
  no interval statistics. Days since latest upload uses the explicit evaluation time.
- View distribution includes count, minimum, maximum, mean, median, and population deviation.
- Subscriber comparisons use strict `>` and `<`; percentages use the eligible count and range from
  0 through 100. Empty eligibility yields zero comparison counts and percentages.
- Ratios divide eligible views by current visible positive subscribers. Hidden, missing, or zero
  subscribers make all derived subscriber-relative values unavailable (`null`).

These are descriptive observations only—never inference, prediction, confidence, threshold policy,
scoring, comparison, ranking, or recommendation.

## Data quality and integrity

Data quality reports qualified/excluded counts, ordered non-zero policy exclusion counts, ordered
non-zero missing-value counts, and canonical-order confirmation. Missing values are never guessed.

Canonical JSON uses UTF-8, sorted keys, compact separators, and forbids NaN/Infinity. The source
digest covers the channel and ordered videos. The result digest covers metadata, summary, schema,
and source digest while excluding its own value. Serialization validates result integrity first.
Both digests use SHA-256. Formula, ordering, or meaning changes require a new schema/config version.
