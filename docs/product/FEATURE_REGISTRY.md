# Feature Registry

## Purpose

Provide the single Product source of truth for capability intent, dependencies, status, and roadmap
order. Status describes Product maturity, not code presence unless explicitly stated.

## Product Knowledge Status

**Status: Vision.** The registry is an accepted inventory of intended capability direction. Each
entry retains its own maturity; registry inclusion is never evidence of validation or implementation.

## Table of contents

- [Status vocabulary](#status-vocabulary)
- [Scope](#scope)
- [Registry](#registry)
- [Feature governance](#feature-governance)
- [Future considerations](#future-considerations)
- [Revision history](#revision-history)

## Status vocabulary

- **Foundation available:** a factual/research foundation exists; the user feature may not.
- **Defined:** Product intent is documented; discovery/research remains.
- **Research required:** material definitions or evidence policy remain unvalidated.
- **Future:** sequenced direction only, not a delivery commitment.

## Scope

The registry covers planned Product capabilities and their conceptual dependencies. It is not an
engineering backlog, release promise, implementation inventory, or authorization to build.

## Registry

| ID | Feature | Purpose / problem solved | Dependencies | Status | Future milestone | Order |
|---|---|---|---|---|---|---:|
| PF-001 | Product Architecture | Govern why capabilities exist and share language | Decision governance | Defined in v0.10.0 | Ongoing | 1 |
| PF-003 | Product Research Governance | Govern unanswered questions and the idea-to-implementation lifecycle | PF-001, Product Governance | Defined in v0.10.0a | Ongoing | 2 |
| RF-001 | Research Artifact Foundation | Produce reproducible evidence without policy leakage | Immutable observations, governance | Foundation available | Maintain | 2 |
| CD-001 | Channel Acquisition | Collect authorized canonical public facts | YouTube integration, provenance | Foundation available | Phase 2 hardening | 3 |
| CI-001 | Channel Intelligence | Produce canonical factual channel characteristics | CD-001, eligibility definitions | Foundation available | Phase 2 | 4 |
| CD-002 | Channel Discovery Experience | Find candidate evidence channels in a market context | CD-001, market definitions | Research required | Phase 2 | 5 |
| CP-001 | Competitor Reference Sets | Build diverse opportunity-specific reference sets | CD-002, CI-001 | Defined | Phase 2 | 6 |
| TD-001 | Topic Evidence | Identify governed topics from authorized content sources | CI-001, language research | Research required | Phase 3 | 7 |
| NP-001 | Content Pattern Evidence | Describe repeated framing/delivery structures | TD-001, format semantics | Research required | Phase 3 | 8 |
| ND-001 | Niche Map | Organize topics, audiences, formats, and markets | TD-001, NP-001 | Research required | Phase 3 | 9 |
| TR-001 | Trend Lifecycle Evidence | Describe time-dependent change and persistence | Longitudinal observations, TD-001 | Research required | Phase 3 | 10 |
| OE-001 | Opportunity Candidate Registry | Record bounded propositions and evidence needs | ND-001, CP-001, TR-001 | Defined | Phase 4 | 11 |
| OE-002 | Opportunity Validation | Govern when a candidate becomes an Opportunity | OE-001, research policy | Research required | Phase 4 | 12 |
| OC-001 | Opportunity Confidence | Communicate evidence quality and limitations | OE-002, interpretation research | Research required | Phase 4 | 13 |
| CR-001 | Creator Profile | Capture editable goals/capabilities/constraints | Privacy, UX, persona validation | Defined | Phase 5 | 14 |
| RC-001 | Explainable Recommendations | Contextualize Opportunities for user-controlled action | OC-001, CR-001, Product policy | Research required | Phase 5 | 15 |
| EX-001 | Experiment Planning | Turn a recommendation into a bounded learning plan | RC-001, user journeys | Future | Phase 5 | 16 |
| PL-001 | AI-assisted Content Planning | Assist ideation/planning with source-aware safeguards | EX-001, AI governance | Future | Phase 6 | 17 |
| VC-001 | AI-assisted Video Creation | Support selected production tasks under creator control | PL-001, rights/safety review | Future | Phase 7 | 18 |
| PB-001 | Publishing Assistance | Support review and publishing workflows | VC-001, OAuth/security/policy | Future | Phase 8 | 19 |
| GI-001 | Growth Intelligence | Observe outcomes and inform reassessment | Publishing/observation history | Future | Phase 9 | 20 |
| PF-002 | Portfolio and Collaboration | Support agencies/studios across governed workspaces | Mature opportunity workflows | Future | Cross-phase | 21 |

## Feature governance

Every new or changed registry entry requires a user problem, persona/journey, domain terms, governing
principles, evidence needs, dependencies, explicit exclusions, and Product owner. “Future milestone”
does not authorize design or implementation. Before engineering, a feature needs acceptance criteria,
research decisions where applicable, technical architecture review, security/privacy assessment, and
documentation updates. Implementation status should only change after repository verification.

Open discovery dependencies must cite [Research Questions](RESEARCH_QUESTIONS.md). Status changes
must follow [Product Lifecycle](PRODUCT_LIFECYCLE.md) and use the knowledge-state meanings in
[Product Governance](PRODUCT_GOVERNANCE.md); a registry row alone never proves validation or delivery.

## Future considerations

Add owners, discovery status, Product decision links, and measurable outcomes when delivery planning
begins. Split entries only when responsibilities have distinct users, policies, or dependencies.

Related: [Product Roadmap](PRODUCT_ROADMAP.md), [Decision Log](DECISION_LOG.md), and
[Product Vision](PRODUCT_VISION.md).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-24 | Created the initial ordered capability registry. |
| 1.1 | 2026-07-24 | Added Product Research Governance and lifecycle/status traceability. |
