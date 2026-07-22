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

---

## Guidelines

- Every significant architectural decision must have its own ADR.
- ADRs are immutable historical records. If a decision changes, create a new ADR and supersede the old one rather than rewriting history.
- Each ADR must follow the `ADR_TEMPLATE.md` format.
