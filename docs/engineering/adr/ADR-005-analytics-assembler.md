# ADR-005: Separate Metric Execution from Analytics Assembly

**Status:** Accepted

**Date:** 2026-07-21

**Owner:** Product & Engineering

## Supersedes

None

---

# 1. Decision Summary

Introduce an analytics assembler between the calculator registry and `CalculatedChannelAnalytics`.

The calculator registry will remain responsible only for executing calculators and returning ordered `MetricResult` objects. The assembler will consume metric results, validate completeness and uniqueness, and construct the strongly typed aggregate. `CalculatedChannelAnalytics` will remain a pure immutable domain model.

---

# 2. Context

The calculator registry provides a deterministic execution boundary for heterogeneous calculators. The next analytics stage needs to transform those generic metric results into a strongly typed aggregate suitable for the Signal Engine and AI Narrative Engine.

Execution results may eventually come from more than the live registry. Cached analytics, persisted results, replays, migrations, and alternative execution pipelines must be able to construct the same aggregate without invoking calculators.

The location of mapping and validation responsibilities therefore determines the coupling and future adaptability of the analytics pipeline.

---

# 3. Problem Statement

Which component should transform a collection of `MetricResult` objects into `CalculatedChannelAnalytics` while preserving clean boundaries, strong typing, and compatibility with alternative result sources?

---

# 4. Decision Drivers

- Separation of concerns
- Dependency inversion
- Strongly typed domain contracts
- Testability
- Support for cached and persisted analytics
- Compatibility with alternative execution pipelines
- Stable downstream contracts
- Maintainability and extensibility

---

# 5. Goals

- Keep calculator execution independent from aggregate construction.
- Keep mapping and completeness validation outside the domain model.
- Allow results from live, cached, persisted, or replayed sources to use the same assembly path.
- Present a strongly typed immutable contract to downstream engines.
- Prevent transport, infrastructure, and interpretation concerns from entering the assembler.

---

# 6. Alternatives Considered

## Option A — Registry constructs `CalculatedChannelAnalytics` directly

### Separation of concerns

Poor. Execution and representation mapping would share one component.

### Coupling and dependency direction

The registry would depend on the aggregate schema and require modification whenever that schema changed. A component currently depending only on calculator contracts would acquire knowledge of a downstream domain model.

### Maintainability, extensibility, and testability

Registry tests would need to cover both execution and mapping behavior. New aggregate fields or validation rules would change the registry even when calculator execution remained unchanged.

### Future compatibility

Cached, persisted, or alternatively produced results would either need to invoke the registry unnecessarily or duplicate its mapping logic. This would make the registry an unsuitable reusable execution boundary for the Signal Engine and AI Narrative Engine.

This option was rejected because it violates single responsibility and couples execution to one output representation.

---

## Option B — Dedicated analytics assembler maps results into the aggregate

### Separation of concerns

Strong. The registry executes, the assembler maps and validates, and the aggregate stores typed data.

### Coupling and dependency direction

The assembler depends on `MetricResult`, `MetricType`, and `CalculatedChannelAnalytics`. The registry remains independent of downstream models. The aggregate knows neither component.

### Maintainability, extensibility, and testability

Execution, mapping, and domain-model tests remain independent. Adding or changing a metric requires an intentional aggregate and assembler update without modifying registry execution.

### Future compatibility

Live registry results, cache reads, persistence adapters, replay jobs, and alternative execution pipelines can all feed the same assembler. The Signal Engine and AI Narrative Engine consume the stable typed aggregate rather than generic result collections.

This option provides the clearest responsibility boundaries with minimal additional structure.

---

## Option C — Aggregate factory or generic projection framework

Two variants were considered:

1. A `CalculatedChannelAnalytics.from_results()` factory.
2. A generic projection or mapper framework supporting arbitrary aggregates.

### Separation of concerns

The factory would place mapping, validation, and `MetricResult` knowledge inside a model required to remain a pure data contract. The generic framework could preserve separation but would add a new abstraction layer before a second projection use case exists.

### Coupling and dependency direction

The factory would couple the aggregate backward to calculator output representations. A generic framework would reduce concrete coupling but introduce framework contracts throughout a currently simple in-process pipeline.

### Maintainability, extensibility, and testability

The factory is convenient initially but causes the domain model to accumulate construction rules. The generic framework is extensible but increases conceptual and testing overhead without demonstrated need.

### Future compatibility

Both could support alternative result sources, but the factory weakens model purity and the framework adds premature generalization. Neither improves current cache, persistence, Signal Engine, or narrative requirements beyond a focused assembler.

This option was rejected because its variants either violate the domain-model boundary or introduce speculative abstraction.

---

# 7. Decision

Adopt Option B.

The target pipeline is:

```text
Deterministic Calculators
        |
        v
Calculator Registry
(execution only)
        |
        v
Analytics Assembler
(mapping and structural validation only)
        |
        v
CalculatedChannelAnalytics
(immutable typed data contract)
        |
        v
Signal Engine
        |
        v
AI Narrative Engine
```

The registry must remain unaware of `CalculatedChannelAnalytics`.

The assembler will:

- consume a source analytics dataset and a collection of `MetricResult` objects
- validate required metric completeness
- validate metric uniqueness independently of the result source
- map metric identities to strongly typed aggregate fields
- construct and return `CalculatedChannelAnalytics`

The assembler will not execute calculators, calculate values, interpret metrics, access YouTube transport or domain models directly, infer signals, or perform persistence and caching.

`CalculatedChannelAnalytics` will expose strongly typed metric properties and contain no registry, `MetricResult`, mapping, validation, or orchestration knowledge.

---

# 8. Decision Rationale

A dedicated assembler is a narrow application boundary that isolates change in the aggregate schema from calculator execution. It also creates one reusable path for assembling live, cached, persisted, or replayed results.

This design follows dependency inversion: calculators and the registry do not depend on downstream consumers, while the assembler depends on stable analytics contracts. Downstream engines receive a strongly typed immutable model and do not need to interpret generic result collections.

The additional component is justified because it owns a distinct transformation and validation responsibility that would otherwise contaminate either the registry or the domain model.

---

# 9. Related Engineering Principles

- EP-001 Build for Maintainability Before Optimization
- EP-002 Separation of Concerns
- EP-003 Single Responsibility Principle
- EP-004 Deterministic Business Logic
- EP-005 Dependency Injection
- EP-006 Immutable Models

---

# 10. Consequences

## Positive

- Registry remains reusable and focused on execution.
- Aggregate remains a pure immutable domain contract.
- Mapping and structural validation have one owner.
- Cached and persisted results can bypass calculator execution safely.
- Alternative pipelines can produce results without duplicating aggregate construction.
- Signal and narrative engines receive a stable strongly typed input.
- Each boundary can be unit tested independently.

## Negative

- Adds one explicit component to the analytics pipeline.
- Adding a metric requires coordinated changes to the typed aggregate and assembler.
- Completeness rules must evolve with the aggregate schema.

## Risks

- The assembler could accumulate business interpretation if its mapping-only boundary is not enforced.
- Persistence-specific serialization could leak into the assembler instead of remaining in infrastructure adapters.
- Metric schema evolution will require deliberate compatibility and migration policies once results are persisted.

---

# 11. Implementation Impact

### Affected folders

- backend/app/services/analytics/
- backend/tests/
- docs/engineering/

### Affected modules

- AnalyticsAssembler
- Strongly typed `CalculatedChannelAnalytics`
- Future Signal Engine
- Future AI Narrative Engine

### Migration required?

No. This ADR defines the boundary before aggregate population is implemented.

### Breaking changes?

No

---

# 12. Security Impact

No direct security impact. Keeping persistence and transport concerns outside the assembler reduces the chance that external representations leak into domain contracts.

---

# 13. Performance Impact

Assembly is an in-memory linear pass over a bounded metric collection. Cache or persistence access remains outside this component.

---

# 14. Cost Impact

No infrastructure or operational cost impact.

---

# 15. Operational Impact

Future persisted metric schemas will require explicit versioning and migration policies. Those policies are not introduced by this decision and remain outside the assembler.

---

# 16. Future Revisit Criteria

Revisit this decision if:

- multiple aggregate projections demonstrate a need for a shared mapper abstraction
- persisted metric versions require compatibility assembly across schemas
- partial aggregate construction becomes an explicit product requirement
- streaming or distributed result assembly is introduced

---

# 17. References

- Product Requirements Document
- Technical Requirements Document
- Engineering Principles
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation
- ADR-004: Explicit Deterministic Calculator Registry
