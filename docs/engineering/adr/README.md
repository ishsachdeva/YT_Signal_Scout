# Architecture Decision Records (ADR)

This directory contains all significant architectural decisions for the YT Signal Scout project.

## ADR Status Legend

- 🟢 Accepted
- 🟡 Proposed
- 🔵 Superseded
- 🔴 Deprecated

## Decision Log

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Adopt a Modular Monolith Architecture | 🟢 Accepted | 2026-07-20 |
| ADR-002 | Separate Raw Analytics, Deterministic Metrics, and Signal Generation | 🟢 Accepted | 2026-07-21 |
| ADR-003 | YT-003 — Rich YouTube Domain Model Before Analytics Expansion | 🟢 Accepted | 2026-07-21 |
| ADR-004 | Explicit Deterministic Calculator Registry | 🟢 Accepted | 2026-07-21 |
| ADR-005 | Separate Metric Execution from Analytics Assembly | 🟢 Accepted | 2026-07-21 |
| ADR-006 | Separate Deterministic Analytics from Business Signal Evaluation | 🟢 Accepted | 2026-07-22 |
| ADR-007 | Govern Production Signals Through a Versioned Signal Catalog | 🟢 Accepted | 2026-07-22 |
| ADR-008 | Establish Explicit Format-Specific Eligible Video Bases for Subscriber-Relative Analytics | 🟢 Accepted | 2026-07-22 |
| ADR-009 | Separate Subscriber-Relative Orchestration from the ChannelAnalytics Calculator Registry | 🟢 Accepted | 2026-07-22 |
| ADR-010 | Acquisition Provenance and Subscriber-Relative Qualification | 🟢 Accepted | 2026-07-22 |
| ADR-011 | Typed Subscriber-Relative Signal Evidence Layer | 🟢 Accepted | 2026-07-22 |
| ADR-012 | Deterministic Offline Subscriber-Band Threshold Backtesting | 🟢 Accepted | 2026-07-22 |
| ADR-013 | Govern Historical Research Dataset Import Through Strict Versioned JSON | 🟢 Accepted | 2026-07-22 |
| ADR-014 | Controlled Deterministic Offline Backtest Execution | 🟢 Accepted | 2026-07-22 |
| ADR-015 | Govern Threshold Research Through Immutable Study Artifacts | 🟢 Accepted | 2026-07-22 |
| ADR-016 | Define Versioned Factual Threshold Evaluation Methodology | 🟢 Accepted; amended by ADR-021 | 2026-07-22 |
| ADR-017 | Record Human Threshold Evaluation as an Immutable Bound Artifact | 🟢 Accepted | 2026-07-22 |
| ADR-018 | Govern Production Threshold Promotion Through Declarative Policy | 🔵 Superseded by ADR-021 | 2026-07-22 |
| ADR-019 | Represent Production Eligibility as an Immutable Assessment | 🔵 Superseded in part by ADR-021 | 2026-07-22 |
| ADR-020 | Govern Historical Dataset Custody and Canonical Integrity | 🟢 Accepted | 2026-07-24 |
| ADR-021 | Separate Release Governance from Autonomous Runtime Evaluation | 🟢 Accepted | 2026-07-24 |
| ADR-022 | Govern Ground-Truth Labels as Immutable Dataset-Bound Artifacts | 🟢 Accepted | 2026-07-24 |
| ADR-023 | Govern Reviewer Evidence Packs and Labelling Rubrics | 🟢 Accepted | 2026-07-24 |
| ADR-024 | Govern Study Definition and Execution | 🟢 Accepted | 2026-07-24 |
| ADR-025 | Deterministic Observation-Level Labelled Evaluation | 🟢 Accepted | 2026-07-24 |
| ADR-026 | Govern Counts-Only Evaluation Aggregation | 🟢 Accepted | 2026-07-24 |

---

## Guidelines

- Every significant architectural decision must have its own ADR.
- ADRs are immutable historical records. If a decision changes, create a new ADR and supersede the old one rather than rewriting history.
- Each ADR must follow the `ADR_TEMPLATE.md` format.
