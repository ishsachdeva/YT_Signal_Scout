# Product Documentation

The source DOCX documents in `source/` define the original product, technical, UI/UX, security,
and feature requirements. The repository-authored Signal Catalog governs deterministic signal
policy and approved eligibility semantics that refine those requirements without duplicating the
source documents.

## Documents

| Document | Authority |
|---|---|
| `source/01_PRD_YT_Signal_Scout.docx` | Product goals, requirements, qualification intent, and scoring direction |
| `source/02_TRD_YT_Signal_Scout.docx` | Target system and data architecture |
| `source/03_UI_UX_Spec_YT_Signal_Scout.docx` | User experience and presentation requirements |
| `source/04_Security_Spec_YT_Signal_Scout.docx` | Security, privacy, and compliance requirements |
| `source/05_Feature_Catalogue_YT_Signal_Scout.docx` | Delivery backlog and acceptance intent |
| `../governance/DECISION_GOVERNANCE.md` | Repository-wide decision ownership, approval, review, lifecycle, and traceability |
| `SIGNAL_CATALOG.md` | Authoritative signal policy, Eligible Video Policy v1, readiness, and threshold provenance |

Where an original source document states a configurable or incomplete signal condition, the
approved Signal Catalog definition supplies the exact implementation boundary. It does not mark a
feature implemented. Architecture decisions remain governed by `docs/engineering/adr/`.
