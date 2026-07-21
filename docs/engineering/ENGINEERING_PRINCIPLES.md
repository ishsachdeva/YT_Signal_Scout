# Engineering Principles

This document defines the engineering philosophy for YT Signal Scout.

These principles guide architectural decisions, implementation, code reviews, testing, and maintenance. Every engineer and AI coding assistant working on this project is expected to follow them unless an approved exception exists.

---

## Product Philosophy

### EP-001: Build for Maintainability Before Optimization

**Category:** Product Philosophy

**Principle**

Prioritize code that is easy to understand, maintain, test, and extend before attempting premature optimization.

**Why**

Software spends far more of its life being maintained than being written. Readable, modular, and predictable systems reduce defects, accelerate feature delivery, and lower long-term engineering costs. Optimization should be driven by evidence, not assumptions.

**Implementation Guidelines**

- Choose clarity over cleverness.
- Prefer simple solutions unless complexity provides measurable value.
- Optimize only after identifying a real performance bottleneck through profiling or metrics.
- Keep business logic modular and easy to modify.
- Every optimization should preserve readability where possible.

**Examples**

✅ Create small, well-named services with clear responsibilities.

✅ Refactor duplicated logic into reusable components.

❌ Introduce complex caching before measuring performance.

❌ Replace readable code with clever one-liners that reduce maintainability.

---

## EP-002: Separation of Concerns

**Category:** Software Architecture

**Principle**

Each module, service, component, or layer should have a single well-defined responsibility. Different concerns such as data acquisition, business logic, persistence, presentation, AI reasoning, and infrastructure should remain isolated behind explicit boundaries.

**Why**

Clear separation of concerns improves maintainability, testability, readability, and scalability. Independent responsibilities reduce coupling, simplify debugging, and allow components to evolve without unintended side effects.

**Implementation Guidelines**

- Keep business logic separate from infrastructure concerns.
- Separate deterministic calculations from AI-generated reasoning.
- Avoid services that perform multiple unrelated responsibilities.
- Use explicit interfaces between architectural layers.
- Prevent presentation logic from leaking into business logic.

**Examples**

✅ Analytics calculators only calculate metrics.

✅ Signal Engine evaluates business rules.

✅ AI explains signals rather than calculating metrics.

❌ A single service fetches YouTube data, calculates metrics, applies business rules, and generates AI summaries.

**Exceptions**

Small utility functions that naturally combine closely related responsibilities may remain together if separation would introduce unnecessary complexity.

**Related ADRs**

- ADR-001: Adopt a Modular Monolith Architecture
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation

---

## EP-003: Single Responsibility Principle

**Category:** Software Design

**Principle**

Every class, service, module, or component should have one primary reason to change.

**Why**

Small focused components are easier to understand, test, review, and reuse. Limiting responsibilities reduces the impact of future changes and minimizes unintended side effects.

**Implementation Guidelines**

- Prefer small services over large "manager" classes.
- One calculator should produce one metric.
- One validator should validate one concern.
- Avoid accumulating unrelated responsibilities over time.
- Refactor when a component begins serving multiple domains.

**Examples**

✅ ChannelAgeCalculator calculates only channel age.

✅ AnalyticsService orchestrates but does not calculate metrics.

❌ AnalyticsService performs validation, calculations, AI prompting, reporting, and persistence.

**Exceptions**

Simple data models or value objects may naturally group closely related data without violating this principle.

**Related ADRs**

- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation

---

## EP-004: Deterministic Business Logic

**Category:** Business Logic

**Principle**

Business rules and calculations must produce consistent and repeatable outputs for identical inputs.

**Why**

Deterministic behaviour enables reliable testing, debugging, auditing, reproducibility, and predictable product behaviour.

AI-generated content should explain deterministic outputs rather than generate them.

**Implementation Guidelines**

- Business calculations must not depend on randomness.
- Avoid hidden state.
- Inject clocks and external dependencies.
- AI should consume business outputs instead of producing them.
- Business rules should remain independently testable.

**Examples**

✅ Average views always produce the same result for the same dataset.

✅ Signal detection follows documented business rules.

❌ AI determines channel scores.

❌ Business logic depends on the current system clock without dependency injection.

**Exceptions**

Features intentionally requiring randomness or probabilistic behaviour should clearly isolate those concerns and document them appropriately.

**Related ADRs**

- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation

---

## EP-005: Dependency Injection

**Category:** Architecture

**Principle**

Components should depend on abstractions and receive external dependencies through construction or explicit injection rather than creating them internally.

**Why**

Dependency injection improves testability, flexibility, modularity, and long-term maintainability while reducing coupling between components.

**Implementation Guidelines**

- Inject services rather than instantiating them internally.
- Inject clocks, repositories, clients, and external integrations.
- Depend on interfaces where appropriate.
- Avoid global mutable state.
- Keep dependencies explicit.

**Examples**

✅ AnalyticsService receives a clock dependency.

✅ Services depend on interfaces instead of concrete implementations.

❌ Services instantiate HTTP clients inside business logic.

❌ Static global service locators.

**Exceptions**

Stateless utility functions with no external dependencies may be called directly.

**Related ADRs**

- ADR-001: Adopt a Modular Monolith Architecture
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation

---

## EP-006: Immutable Models

**Category:** Data Design

**Principle**

Domain models representing business state should be immutable whenever practical.

**Why**

Immutable models improve predictability, simplify reasoning, eliminate accidental mutation, support safer concurrency, and reduce debugging complexity.

**Implementation Guidelines**

- Prefer immutable data models.
- Return new objects rather than modifying existing ones.
- Treat domain models as snapshots of state.
- Prevent hidden mutations after validation.
- Use immutable collections where practical.

**Examples**

✅ ChannelAnalytics is immutable.

✅ CalculatedChannelAnalytics is immutable.

✅ MetricResult is immutable.

❌ Updating fields inside an existing analytics model after creation.

❌ Passing mutable state across architectural layers.

**Exceptions**

Infrastructure models, ORM entities, or framework-specific objects may require mutability due to technical constraints. Such cases should be isolated from the core domain model.

**Related ADRs**

- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation

**Exceptions**

Performance-critical paths may justify additional complexity if supported by profiling, benchmarking, or production metrics. Such decisions should be documented in an ADR when they materially affect the architecture.

**Related ADRs**

- ADR-001: Adopt a Modular Monolith Architecture