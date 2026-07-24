# YT Signal Scout

YT Signal Scout is evolving into a YouTube Opportunity Intelligence Platform that helps creators
identify evidence-supported, feasible content opportunities without promising individual success.
Channels, videos, topics, and trends are evidence; the Opportunity is the primary Product asset.
Channel Discovery is the first capability, not the final product.

Product drives Engineering through a governed evidence lifecycle:

```text
Customer Problems
        |
        v
Vision -> Research -> Validated Findings -> Product Decisions
                                            |
                                            v
Architecture -> Implementation -> Measurement -> Iteration
       ^                                               |
       +-----------------------------------------------+
```

Engineering implements approved Product intent; it does not define Product meaning. A documented
idea is not a validated finding, and an accepted decision or ADR is not an implemented capability.

The current implementation is a modular-monolith foundation using official public API data. Its
backend pipeline keeps acquisition, deterministic
analytics, business signal interpretation, and future AI narratives in separate typed layers.

The v0.6.0 analytics foundation includes canonical acquisition with immutable provenance,
format-specific eligible-video classification, subscriber-relative qualification and factual
analytics, and a typed policy-free evidence bundle. Acquisition preserves discovery ordering and
duplicates while exposing a stable unique canonical-video population for analytics.

Offline research is isolated in a deterministic backtesting package. It evaluates explicitly
versioned subscriber bands and median-VSR threshold candidates and produces factual immutable
reports; it does not select or recommend production policy. No production signal rule is
approved, registered, or emitted. SIG-002 remains blocked pending governed research and explicit
Product Owner decisions with required Analytics Owner review.

The governed artifact path separately imports historical datasets, evidence, rubrics, and labels;
validates one study execution; compares supplied predictions with final labels per observation;
counts those outcomes; and calculates the approved mathematical statistics. Each boundary remains
immutable, content-addressed, offline, and absent from application startup. No real study artifact
is stored in this repository.

Key documentation:

- [Product Architecture](docs/product/README.md) defines the long-term vision, ubiquitous language,
  users, capability relationships, principles, decisions, registry, and roadmap.
- [Product Vision](docs/product/PRODUCT_VISION.md) explains the Opportunity Intelligence mission and
  why Channel Discovery is foundational evidence rather than the final outcome.
- [Product Governance](docs/product/PRODUCT_GOVERNANCE.md) defines knowledge states, authority,
  precedence, reviews, and the boundary between Product and Engineering.
- [Product Lifecycle](docs/product/PRODUCT_LIFECYCLE.md) defines the traceable path from problem and
  research question through implementation, measurement, and iteration.
- [Research Questions](docs/product/RESEARCH_QUESTIONS.md) is the canonical unanswered Product
  Discovery backlog and does not authorize implementation.
- [Decision Governance](docs/governance/DECISION_GOVERNANCE.md) defines repository-wide decision
  accountability, approval, review, lifecycle, and traceability.
- [SIG-002 Research Protocol](docs/research/SIG-002_RESEARCH_PROTOCOL.md) defines the canonical
  dataset, labelling, evaluation, boundary-testing, and evidence methodology for threshold studies.
- [Historical Dataset Format](docs/engineering/HISTORICAL_DATASET_FORMAT.md) defines schema version
  2 custody, provenance, canonical serialization, and integrity validation.
- [Ground Truth Label Format](docs/engineering/GROUND_TRUTH_LABEL_FORMAT.md) defines immutable
  dataset-bound independent labels, adjudication, version history, and canonical integrity.
- [Evidence Pack Format](docs/engineering/EVIDENCE_PACK_FORMAT.md) defines immutable reviewer
  evidence definitions, snapshots, typed facts, canonical serialization, and integrity checks.
- [Labelling Rubric Format](docs/engineering/LABELLING_RUBRIC_FORMAT.md) defines closed criteria,
  decision states, reason codes, and exact evidence-definition binding.
- [Study Execution Format](docs/engineering/STUDY_EXECUTION_FORMAT.md) defines deterministic
  governed-input validation and immutable non-analytical execution artifacts.
- [Labelled Evaluation Format](docs/engineering/LABELLED_EVALUATION_FORMAT.md) defines immutable
  per-observation prediction-versus-truth outcomes without aggregation.
- [Evaluation Aggregation Format](docs/engineering/EVALUATION_AGGREGATION_FORMAT.md) defines
  immutable counts-only cohort summaries without statistical metrics.
- [Statistical Evaluation Format](docs/engineering/STATISTICAL_EVALUATION_FORMAT.md) defines the
  approved mathematical metrics, Wilson intervals, and deterministic integrity boundary.
- [Research Architecture Stabilization Audit](docs/engineering/RESEARCH_ARCHITECTURE_STABILIZATION.md)
  records verified boundary, validation, digest, mathematical, export, and dependency findings.
- [Channel Intelligence Format](docs/engineering/CHANNEL_INTELLIGENCE_FORMAT.md) defines immutable
  deterministic channel-level research facts and canonical integrity.
- [Signal Catalog v1](docs/product/SIGNAL_CATALOG.md) governs proposed and approved signal policy.
- [Backend README](backend/README.md) contains setup and test commands.
- [Changelog](CHANGELOG.md) records release capabilities and boundaries.
- [Architecture](docs/engineering/ARCHITECTURE.md) defines system boundaries.
- [Architecture Decision Records](docs/engineering/adr/README.md) record durable decisions.
