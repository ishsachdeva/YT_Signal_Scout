# YT Signal Scout

YT Signal Scout is a modular-monolith SaaS platform for discovering promising YouTube
channels from official public API data. Its backend pipeline keeps acquisition, deterministic
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

Key documentation:

- [Decision Governance](docs/governance/DECISION_GOVERNANCE.md) defines repository-wide decision
  accountability, approval, review, lifecycle, and traceability.
- [SIG-002 Research Protocol](docs/research/SIG-002_RESEARCH_PROTOCOL.md) defines the canonical
  dataset, labelling, evaluation, boundary-testing, and evidence methodology for threshold studies.
- [Historical Dataset Format](docs/engineering/HISTORICAL_DATASET_FORMAT.md) defines schema version
  2 custody, provenance, canonical serialization, and integrity validation.
- [Ground Truth Label Format](docs/engineering/GROUND_TRUTH_LABEL_FORMAT.md) defines immutable
  dataset-bound independent labels, adjudication, version history, and canonical integrity.
- [Signal Catalog v1](docs/product/SIGNAL_CATALOG.md) governs proposed and approved signal policy.
- [Backend README](backend/README.md) contains setup and test commands.
- [Changelog](CHANGELOG.md) records release capabilities and boundaries.
- [Architecture](docs/engineering/ARCHITECTURE.md) defines system boundaries.
- [Architecture Decision Records](docs/engineering/adr/README.md) record durable decisions.
