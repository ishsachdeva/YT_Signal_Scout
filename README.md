# YT Signal Scout

YT Signal Scout is a modular-monolith SaaS platform for discovering promising YouTube
channels from official public API data. Its backend pipeline keeps acquisition, deterministic
analytics, business signal interpretation, and future AI narratives in separate typed layers.

Version 0.5.0 includes the complete deterministic subscriber-relative analytics pipeline:
format-specific eligible-video classification, eligible standard-video count and median
standard-video VSR calculations, explicit orchestration, structural result assembly, and an
immutable typed aggregate exposed through the composed analytics service.

Key documentation:

- [Signal Catalog v1](docs/product/SIGNAL_CATALOG.md) governs proposed and approved signal policy.
- [Backend README](backend/README.md) contains setup and test commands.
- [Architecture](docs/engineering/ARCHITECTURE.md) defines system boundaries.
- [Architecture Decision Records](docs/engineering/adr/README.md) record durable decisions.
