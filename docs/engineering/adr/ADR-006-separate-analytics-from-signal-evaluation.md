# ADR-006: Separate Deterministic Analytics from Business Signal Evaluation

**Status:** Accepted  
**Date:** 2026-07-22  
**Owner:** Product & Engineering

## Supersedes

None

---

# 1. Decision Summary

Business interpretation belongs in independent typed `SignalRule` objects orchestrated by a
deterministic `SignalEngine` after `CalculatedChannelAnalytics`. Signals carry immutable,
structured evidence and stable rule provenance. The engine uses explicit injection order,
rejects duplicate rule identities, and fails fast.

# 2. Context

The analytics pipeline produces a complete immutable factual aggregate. The next boundary must
interpret those facts without contaminating calculators, the assembler, or the aggregate, and
without delegating deterministic policy to the future AI narrative layer.

# 3. Problem Statement

Business meaning must be derived so rules remain explicit, independently testable,
reproducible, explainable, and replaceable as policy evolves.

# 4. Decision Drivers

Separation of facts from interpretation, determinism, static typing, immutable contracts, rule
isolation, transparent evidence, explicit ordering, and simple failure behavior.

# 5. Goals

Preserve factual analytics, give each rule one coherent policy, provide a stable downstream
contract, make orchestration deterministic, and reserve thresholds for approved product policy.

# 6. Non-goals

Production rules, scoring, ranking, persistence, runtime configuration, AI narratives,
presentation text, concurrency, caching, and APIs are excluded.

# 7. Alternatives Considered

## Option A — interpretation inside `CalculatedChannelAnalytics`

Rejected: it mixes facts with policy, violates single responsibility, couples aggregate and
rule changes, hinders isolated tests and versioning, and blocks alternative policies.

## Option B — one monolithic engine containing every rule

Rejected: rule growth creates a high-change conditional hub with poor isolated testing,
unclear ownership, expanding configuration complexity, and open/closed violations.

## Option C — independent typed rules with deterministic orchestration

Selected: rules are isolated and discoverable, dependency direction remains clean, tests are
focused, and orchestration stays small. Stable rule IDs and integer versions support replay.

## Option D — configuration-driven generic rules

Rejected: runtime policy editing is not required. JSON/YAML/database expressions would lose
static guarantees, add validation and operational complexity, complicate debugging, and create
expression-injection or unsafe-evaluation risks.

# 8. Selected Architecture

```text
CalculatedChannelAnalytics
        |
        v
Independent SignalRule implementations
        |
        v
SignalEngine
        |
        v
tuple[Signal, ...]
        |
        v
Future AI Narrative Engine
```

The bounded context lives in `app/services/signals`, beside analytics, because it owns
interpretation and may serve multiple downstream consumers.

# 9. Signal Model Responsibility

`Signal` contains deterministic machine semantics only: signal identity, polarity, reason code,
rule identity/version, and evidence. It contains no narrative, formatting, generated evaluation
time, score, or persistence concern. Signal identities are frozen validated value objects,
avoiding speculative enum members before production rules exist.

# 10. Evidence Strategy

One generic typed evidence model contains `MetricType`, the original numeric or missing value,
and the source channel ID plus `generated_at`. This retains value types and identifies the
source snapshot without copying the aggregate. Metric-specific unions are premature;
comparison fields wait for an approved rule that defines their semantics.

# 11. Rule Contract

A runtime-checkable `Protocol` exposes only `rule_id`, `rule_version`, and
`evaluate(CalculatedChannelAnalytics) -> tuple[Signal, ...]`. This follows calculator
conventions without mandatory inheritance.

# 12. Rule Identity

Every rule exposes a frozen validated `RuleId`, independent of its class name and suitable for
future persistence. It is unique within an engine.

# 13. Rule Versioning Decision

A positive integer is implemented and copied into signals. Interpretation changes increment
it. Semantic-version machinery and persistence compatibility policy are deferred.

# 14. Category, Polarity, and Severity Decisions

Polarity is retained as positive, negative, or informational because its meaning is stable,
presentation-independent, and does not require a threshold scale. Category is deferred until
approved production signals establish a taxonomy; defining broad buckets now would freeze
speculative names without rule owners. Severity is also deferred because no approved policy
defines importance levels independently of business thresholds. Both can be added deliberately
before the first production signal contract has downstream consumers.

# 15. Confidence Decision

Deferred. Product documents tie confidence to sample size, eligibility, completeness, cohorts,
and observation context, but the aggregate lacks a complete defensible input contract. No
placeholder or arbitrary confidence is emitted.

# 16. Execution Ordering

Rules execute synchronously once in injection order. Signals preserve rule order and each
rule's output order. Construction snapshots the sequence. Empty rules and outputs are valid;
the engine is stateless and reusable.

# 17. Duplicate-rule Behavior

Duplicate `RuleId` values fail during construction. Duplicate `SignalType` values from distinct
rules remain ordered and separate because independently versioned policies may support the same
broad observation. No unsupported merge semantics are invented.

# 18. Failure Semantics

Rule exceptions propagate unchanged, later rules do not execute, and no partial collection is
returned.

# 19. Threshold Governance

Product sources discuss configurable thresholds and scores but contain no approved production
conditions for this aggregate. No production rule is implemented. Each future threshold needs
an approved definition, boundaries, evidence, reason code, identity, and version.

# 20. Dependency Direction

Signals depend only on the typed aggregate and metric identities. Analytics does not depend on
signals. Rules may not use transport models, persistence, networks, AI, or hidden clocks.

# 21. Testing Consequences

Fake rules cover model validation and immutability, structural contracts, zero/one/many output,
sequence snapshots, ordering, duplicate IDs, duplicate signal preservation, repeatability,
same-instance delivery, and fail-fast propagation.

# 22. Positive Consequences

Facts remain policy-neutral; rules evolve independently; evidence and provenance enable audits;
execution is reproducible; adding a rule changes composition rather than the engine.

# 23. Negative Consequences

The design adds a service boundary and explicit composition. Rule authors must maintain identity,
version, evidence, and taxonomy consistency.

# 24. Risks

Taxonomy may evolve. Stateful rules could undermine repeatability. Persistence will require
schema evolution and exact input references beyond timestamps. Reviews must enforce boundaries.

# 25. Security Impact

There is no I/O, discovery, expression parsing, `eval`, arbitrary loading, configuration
execution, network call, or secret. Evidence contains existing public analytics values. Future
API layers must authorize data and translate exceptions safely.

# 26. Performance Impact

Execution is `O(R + S)` for rules and emitted signals. Bounded tuples are copied once; analytics
are not serialized or duplicated. No optimization is warranted.

# 27. Operational Impact

No service, dependency, configuration, persistence, or deployment change. Original exceptions
and tracebacks remain available for in-process diagnosis.

# 28. Future Revisit Criteria

Revisit for richer evidence comparisons, historical replay, confidence inputs, multiple policy
sets, partial success, measured concurrency needs, or a real runtime-administration requirement.

# 29. Related ADRs

ADR-001, ADR-002, ADR-003, ADR-004, and ADR-005.

# 30. Implementation Impact

Adds `backend/app/services/signals`, tests, architecture documentation, and README guidance.
Deterministic analytics, APIs, persistence, dependencies, and deployment remain unchanged.
