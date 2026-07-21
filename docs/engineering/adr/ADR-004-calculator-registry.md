# ADR-004: Explicit Deterministic Calculator Registry

**Status:** Accepted

**Date:** 2026-07-21

**Owner:** Product & Engineering

## Supersedes

None

---

# 1. Decision Summary

Introduce a calculator registry that receives an explicitly ordered sequence of deterministic calculators through constructor injection, executes each calculator once, and returns an immutable result tuple.

The registry rejects duplicate metric identities during construction and uses fail-fast execution: calculator exceptions propagate unchanged, later calculators are not executed, and no partial result collection is returned.

---

# 2. Context

YT Signal Scout now has multiple independent deterministic calculators with a common `AnalyticsCalculator` contract. Future population of `CalculatedChannelAnalytics` requires one stable entry point that can execute these calculators without moving algorithms into a service or coupling downstream layers to individual calculator implementations.

The execution mechanism must preserve deterministic behavior, explicit dependencies, and calculator independence while remaining easy to extend.

---

# 3. Problem Statement

How should deterministic calculators be registered and executed so that ordering, metric identity, dependency ownership, and failure behavior remain explicit and predictable?

---

# 4. Decision Drivers

- Deterministic execution
- Explicit dependency injection
- Calculator independence
- Stable orchestration boundary
- Extensibility
- Strong typing
- Simple failure semantics
- Testability

---

# 5. Goals

- Provide one entry point for deterministic metric execution.
- Execute every registered calculator exactly once in a documented order.
- Prevent ambiguous duplicate metric results.
- Preserve calculator exceptions and diagnostic context.
- Keep calculation and interpretation logic outside the registry.

---

# 6. Alternatives Considered

## Option A — Explicit ordered constructor registration

### Pros

- Dependencies and execution order are visible
- Straightforward unit testing
- No global state or import side effects
- New calculators require only composition changes

### Cons

- The application composition root must list calculators explicitly

---

## Option B — Reflection or dynamic module discovery

### Pros

- Little explicit composition code
- New modules may be discovered automatically

### Cons

- Hidden dependencies
- Ordering depends on discovery behavior
- Import side effects and harder testing
- Failures are less predictable

This option was rejected because implicit discovery conflicts with deterministic, explicit architecture.

---

## Option C — Hard-code calculators inside `AnalyticsService`

### Pros

- Fewer public components

### Cons

- Couples dataset construction to calculator orchestration
- Violates dependency inversion
- Requires service modification for every calculator
- Expands the service's responsibilities

This option was rejected because it would weaken existing layer boundaries and single responsibility.

---

# 7. Decision

Create `CalculatorRegistry` in the analytics module.

The registry will:

- accept a `Sequence` of `AnalyticsCalculator` implementations through its constructor
- copy that sequence into an immutable tuple
- preserve registration order as execution and result order
- allow an empty registry and return an empty result tuple
- reject more than one calculator with the same `MetricType`
- invoke `calculate()` once for each calculator
- pass the same `ChannelAnalytics` instance to every calculator
- return a tuple of `MetricResult` objects

Execution will be synchronous and fail-fast. If a calculator raises, the exception propagates unchanged. The registry does not execute later calculators and does not return partial results. Retries, partial-success policies, and error translation belong to future application orchestration if product requirements justify them.

---

# 8. Decision Rationale

Explicit ordered registration makes dependencies and execution order reviewable at the composition boundary. Constructor injection allows production composition and tests to supply calculators without globals, reflection, or registry mutation.

Rejecting duplicate metric identities prevents ambiguous downstream aggregation. Fail-fast propagation retains the original exception type and traceback, avoids silently incomplete analytics, and provides the simplest deterministic contract while no partial-result product behavior exists.

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

- Stable deterministic execution entry point
- Explicit ordering and dependencies
- Calculator algorithms remain isolated
- Duplicate outputs fail during construction
- New calculators require only composition changes
- Failure behavior is predictable and testable

## Negative

- Application composition must maintain an explicit calculator sequence
- A calculator failure prevents subsequent calculators from executing
- Heterogeneous metric values require aggregation under their common result abstraction

## Risks

- Callers may supply a semantically inappropriate order even though the order is deterministic.
- Stateful calculator implementations could undermine repeatability despite the registry itself remaining stateless.

---

# 11. Implementation Impact

### Affected folders

- backend/app/services/analytics/
- backend/tests/
- docs/engineering/

### Affected modules

- CalculatorRegistry
- AnalyticsCalculator
- MetricResult
- Analytics exception hierarchy
- Future application composition

### Migration required?

No

### Breaking changes?

No

---

# 12. Security Impact

No direct security impact. The registry has no infrastructure access and executes only injected in-process calculators.

---

# 13. Performance Impact

Calculators execute sequentially. This preserves deterministic behavior and is appropriate for the current bounded workload. Concurrency is intentionally excluded.

---

# 14. Cost Impact

No infrastructure or operational cost impact.

---

# 15. Operational Impact

Calculator failures retain their original exception and traceback. No partial result collection is exposed, simplifying diagnosis and preventing incomplete analytics from being mistaken for complete output.

---

# 16. Future Revisit Criteria

Revisit this decision if:

- product requirements explicitly permit partial analytics results
- calculator dependencies require a dependency graph
- measured execution time justifies concurrency
- calculators require isolated retries or circuit breaking
- dynamic third-party calculator plugins become a supported product capability

---

# 17. References

- Product Requirements Document
- Technical Requirements Document
- Engineering Principles
- ADR-001: Adopt a Modular Monolith Architecture
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation
- ADR-003: Rich YouTube Domain Model Before Analytics Expansion
