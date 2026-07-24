# YT Signal Scout - Engineering Portal

Welcome to the engineering documentation for YT Signal Scout.

This directory contains the technical standards, architectural decisions, and engineering practices used throughout the project.

---

## Reading Order

New contributors should read the documents in the following order:

1. Product Requirements Document (PRD)
2. Technical Requirements Document (TRD)
3. UI/UX Specification
4. Security Specification
5. Feature Catalogue
6. Decision Governance
7. Signal Catalog
8. Engineering Principles
9. Architecture Decision Records (ADRs)

---

## Engineering Documents

| Document | Purpose |
|----------|---------|
| ../governance/DECISION_GOVERNANCE.md | Repository-wide decision ownership, approval, review, lifecycle, and traceability |
| ENGINEERING_PRINCIPLES.md | Engineering philosophy and decision-making principles |
| ARCHITECTURE.md | Current and target system architecture |
| HISTORICAL_DATASET_FORMAT.md | Governed schema, custody, provenance, digest, and canonical import format |
| GROUND_TRUTH_LABEL_FORMAT.md | Immutable dataset-bound labels, independent review, adjudication, and canonical import format |
| EVIDENCE_PACK_FORMAT.md | Immutable reviewer evidence definitions, snapshots, facts, canonical import, and integrity |
| LABELLING_RUBRIC_FORMAT.md | Versioned criteria, label states, reason codes, decision guidance, and canonical import |
| STUDY_EXECUTION_FORMAT.md | Governed study definition, input compatibility, validation, execution manifest, and canonical result |
| adr/ | Architecture Decision Records |
| ../research/SIG-002_RESEARCH_PROTOCOL.md | Canonical SIG-002 research methodology |
| ../product/SIGNAL_CATALOG.md | Governed signal definitions, readiness, and threshold provenance |

---

## Development Workflow

Every feature follows this lifecycle:

1. Understand the requirement.
2. Confirm the architecture.
3. Record significant architectural decisions (ADR if required).
4. Implement in small, testable increments.
5. Test thoroughly.
6. Update documentation where necessary.

---

## Guiding Philosophy

- Build for maintainability before optimization.
- Prefer simplicity over cleverness.
- Architecture before implementation.
- Security by design.
- Documentation evolves with the product.
