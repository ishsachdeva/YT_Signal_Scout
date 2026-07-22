# ADR-009: Separate Subscriber-Relative Orchestration from the ChannelAnalytics Calculator Registry

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

ADR-008 only where it states that subscriber-relative calculators consume `ChannelAnalytics`,
receive the classifier through injection, conform to the existing `AnalyticsCalculator` protocol,
or execute through the existing Calculator Registry. All other ADR-008 decisions remain accepted.

---

# 1. Decision Summary

Preserve the narrow typed inputs of `EligibleStandardVideoCountCalculator` and
`MedianStandardVideoVsrCalculator`. Do not generalize the homogeneous `CalculatorRegistry` or add
adapters. A future dedicated subscriber-relative analytics orchestrator will apply explicit
dependency sequencing and deliver precomputed classification and subscriber inputs to those
calculators. A separate future result-assembly boundary will map their metric results.

# 2. Context

ADR-004 established a homogeneous execution registry. Every registered calculator implements
`calculate(ChannelAnalytics)`, and the registry passes the same dataset instance to every
calculator. ADR-005 then established the existing Analytics Assembler for mapping that registry's
results into `CalculatedChannelAnalytics`.

ADR-008 correctly separated canonical facts, eligibility classification, calculations,
qualification, signals, and narratives. It also assumed that subscriber-relative calculators
would consume `ChannelAnalytics`, receive a classifier through injection, and remain compatible
with the existing registry.

The implemented subscriber-relative calculators instead expose narrower factual contracts:

```text
EligibleStandardVideoCountCalculator.calculate(
    EligibleVideoClassification
)

MedianStandardVideoVsrCalculator.calculate(
    EligibleVideoClassification,
    subscriber_count
)
```

Attempted registry integration exposed the incompatibility. The existing registry has no
heterogeneous inputs, dependency binding, classification-aware execution, adapters,
registration-only discovery, or multiple execution stages.

# 3. Problem Statement

How should subscriber-relative calculators receive their explicit prerequisite values without
weakening their focused contracts or turning the existing homogeneous registry into implicit
dependency orchestration?

# 4. Decision Drivers

- Preserve narrow calculator responsibilities
- Preserve ADR-004 registry semantics
- Make dependencies and ordering explicit
- Avoid repeated policy application inside calculators
- Avoid runtime signature inspection and implicit dispatch
- Keep calculation separate from orchestration and assembly
- Minimize the next implementation boundary
- Maintain deterministic, fail-fast execution

# 5. Goals

- Keep eligibility policy exclusively in `EligibleVideoClassifier`.
- Keep each subscriber-relative calculator responsible for one metric.
- Keep the existing Calculator Registry limited to homogeneous `ChannelAnalytics` calculators.
- Introduce one future typed owner for subscriber-relative sequencing and input delivery.
- Keep subscriber-relative result mapping outside calculators and orchestration.

# 6. Alternatives Considered

## Option A — Change subscriber-relative calculators to consume ChannelAnalytics

### Pros

- Structural compatibility with the existing registry
- No new orchestration component

### Cons

- Forces calculators to obtain or create eligibility dependencies
- Weakens their narrow typed contracts
- Risks repeated classification and hidden dependency construction
- Couples pure mathematics to a broader source dataset

Rejected.

## Option B — Generalize CalculatorRegistry for heterogeneous signatures

### Pros

- One execution component for all calculators

### Cons

- Requires runtime dispatch, dependency binding, or a generalized context
- Changes the simple ADR-004 contract for one specialized path
- Makes registry behavior depend on calculator-specific inputs
- Introduces speculative framework complexity

Rejected.

## Option C — Add adapters around subscriber-relative calculators

### Pros

- Preserves existing calculator signatures
- Could satisfy the current registry protocol

### Cons

- Adapters would own classification, subscriber extraction, or both
- Dependency sequencing becomes less visible
- Adds indirection before the orchestration contract is implemented and tested

Rejected for the current architecture. Reconsider only if a concrete external integration later
requires an adapter.

## Option D — Add a second calculator registry

### Pros

- Could provide lookup and ordered ownership for the specialized calculators

### Cons

- Duplicates registry concepts
- Does not itself solve typed input delivery
- Encourages a parallel framework rather than a focused orchestration boundary

Rejected.

## Option E — Dedicated subscriber-relative analytics orchestrator

### Pros

- Makes classification and subscriber dependencies explicit
- Preserves narrow calculator contracts
- Preserves the existing registry unchanged
- Provides deterministic ordering and one fail-fast execution boundary
- Keeps result assembly separate

### Cons

- Adds one specialized application component
- Creates a second deterministic execution path that must remain clearly documented

Selected.

# 7. Decision

Adopt Option E.

Analytics has two deterministic paths:

```text
Path A
ChannelAnalytics
    -> homogeneous ChannelAnalytics calculators
    -> CalculatorRegistry
    -> existing AnalyticsAssembler

Path B
canonical channel/video data + explicit evaluation time
    -> EligibleVideoClassifier
    -> EligibleVideoClassification
    -> future SubscriberRelativeAnalyticsOrchestrator
    -> subscriber-relative metric results
    -> future subscriber-relative result assembler
```

The future subscriber-relative orchestrator will:

- receive `EligibleVideoClassification` and subscriber count explicitly;
- deliver the same immutable `EligibleVideoClassification` to both calculators;
- deliver the explicit canonical subscriber count to `MedianStandardVideoVsrCalculator`;
- invoke `EligibleStandardVideoCountCalculator` first;
- invoke `MedianStandardVideoVsrCalculator` second;
- execute each calculator exactly once;
- return one immutable ordered metric-result tuple;
- reject duplicate configured metric identities during construction;
- remain synchronous and fail-fast, returning no partial collection after a failure.

The orchestrator will not invoke the classifier, classify videos itself, calculate values, infer subscriber counts,
assemble aggregates, perform qualification, evaluate signals, persist data, cache results, or
generate narratives. Dependencies will be constructor-injected or method inputs; no component may
infer dependencies through reflection, globals, or service location.

The future subscriber-relative result assembler will consume the orchestrator's metric results,
validate structural completeness and uniqueness, and map them into a typed subscriber-relative
result. Its exact result contract belongs to its implementation milestone. It will not execute
classifiers or calculators.

# 8. Decision Rationale

The specialized path has real prerequisite structure that the existing homogeneous registry was
not designed to express. A focused orchestrator makes that structure visible without weakening the
calculators or generalizing a stable registry. Keeping result mapping separate preserves ADR-005's
execution-versus-assembly principle even though Path B uses a different execution boundary.

# 9. Related Engineering Principles

- EP-001 Build for Maintainability Before Optimization
- EP-002 Separation of Concerns
- EP-003 Single Responsibility Principle
- EP-004 Deterministic Business Logic
- EP-005 Dependency Injection
- EP-006 Immutable Models

# 10. Consequences

## Positive

- Calculator inputs remain narrow, typed, and independently testable.
- Eligibility executes once per subscriber-relative orchestration run.
- Existing registry behavior and typing remain unchanged.
- Dependency sequencing and calculator order become explicit.
- Assembly and qualification remain separate downstream concerns.

## Negative

- Analytics has two execution paths instead of one universal registry.
- A dedicated orchestrator and result assembler require separate tests and composition.
- Shared observability must distinguish the two paths.

## Risks

- The specialized orchestrator could accumulate calculation or policy logic if its boundary is not
  enforced.
- Future developers could mistakenly register narrow-input calculators in `CalculatorRegistry`.
- Result ordering could drift unless defined as part of the orchestrator contract and tested.

# 11. Implementation Impact

### Affected folders

- `backend/app/services/analytics/`
- `backend/tests/`
- `docs/engineering/`
- `docs/product/`

### Affected modules

- Future `SubscriberRelativeAnalyticsOrchestrator`
- `EligibleVideoClassifier`
- `EligibleStandardVideoCountCalculator`
- `MedianStandardVideoVsrCalculator`
- Future subscriber-relative result assembler
- Application composition

The existing `CalculatorRegistry`, `AnalyticsCalculator`, and `AnalyticsAssembler` are explicitly
unaffected.

### Migration required?

No. No subscriber-relative orchestration result is persisted.

### Breaking changes?

No production API is changed. This decision supersedes an unimplemented ADR-008 integration
assumption and preserves the implemented calculator APIs.

# 12. Security Impact

No new data source or privilege is introduced. Explicit dependencies reduce the risk of hidden
service access or unintended transport coupling.

# 13. Performance Impact

One precomputed eligibility classification is shared by both calculators. Execution remains
sequential over bounded in-memory data. No concurrency, network access, caching, or persistence is
introduced.

# 14. Cost Impact

No infrastructure cost. The future boundary is an in-process deterministic component.

# 15. Operational Impact

Future diagnostics should identify the subscriber-relative orchestration path, policy version,
ordered metric identities, and failure stage without logging sensitive or excessive source data.
No operational behavior changes in this documentation milestone.

# 16. Future Revisit Criteria

Revisit when:

- a third subscriber-relative calculator introduces materially different dependencies;
- measured execution cost justifies shared precomputation beyond classification;
- multiple specialized paths demonstrate a justified common typed orchestration abstraction;
- persistence or replay requires a versioned subscriber-relative result contract;
- partial-success behavior becomes an approved product requirement.

# 17. References

- Architecture
- Signal Catalog v1.1
- Eligible Video Policy v1
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation
- ADR-004: Explicit Deterministic Calculator Registry
- ADR-005: Separate Metric Execution from Analytics Assembly
- ADR-008: Establish Explicit Format-Specific Eligible Video Bases for Subscriber-Relative Analytics
