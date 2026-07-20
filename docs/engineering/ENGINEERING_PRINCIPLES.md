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

**Exceptions**

Performance-critical paths may justify additional complexity if supported by profiling, benchmarking, or production metrics. Such decisions should be documented in an ADR when they materially affect the architecture.

**Related ADRs**

- ADR-001: Adopt a Modular Monolith Architecture