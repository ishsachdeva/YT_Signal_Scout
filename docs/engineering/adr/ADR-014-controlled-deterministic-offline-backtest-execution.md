# ADR-014: Controlled Deterministic Offline Backtest Execution

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision composes the offline boundaries established by ADR-012 and ADR-013.

---

# 1. Decision Summary

Introduce a synchronous `BacktestExecutionService` inside `services/backtesting`. It accepts one
validated historical import result and one immutable, versioned study configuration bound to that
dataset, invokes the existing deterministic backtester once, and returns immutable factual
execution metadata with the resulting report.

# 2. Context

ADR-012 owns deterministic threshold calculation and ADR-013 owns governed external dataset
import. Neither assigns responsibility for validating that an explicitly selected dataset and
study configuration belong together, sequencing one complete run, or packaging its factual
identity and report. Leaving that work to ad hoc scripts would weaken reproducibility.

# 3. Alternatives Considered

## Call the backtester directly from each offline caller

Rejected because every caller would separately own dataset/configuration binding, invocation
metadata, and output validation.

## Add execution behavior to the importer or backtester

Rejected because import owns the external trust boundary and the backtester owns calculations.
Combining either with execution orchestration would give it a second responsibility.

## Add a dedicated execution service

Selected. It creates one narrow orchestration boundary while reusing all existing calculation and
import contracts.

# 4. Execution Contract

The request contains an explicit execution identity, timezone-aware execution timestamp, validated
`HistoricalDatasetImportResult`, and versioned configuration. Configuration binds the dataset ID
and version to the existing ordered `SubscriberBandSet` and `MedianVsrThresholdSet`.

The result contains only factual identities, versions, the supplied execution timestamp, and the
existing `ThresholdBacktestReport`. Runtime duration and implicit wall-clock timestamps are
excluded because they would make equal inputs produce unequal results.

# 5. Ownership and Failures

The service validates request type and dataset binding, invokes the backtester synchronously once,
and verifies that the returned report matches the requested dataset, configuration, and timestamp.
Typed execution failures distinguish invalid requests, dataset mismatch, configuration mismatch,
and structural backtester failure. The existing backtester continues to own calculations and its
dataset validator continues to own analytical input invariants.

# 6. Boundary

Execution remains offline, single-threaded, and synchronous. It has no API, CLI, scheduler,
persistence, network, acquisition, analytics orchestration, signal, AI, or production-composition
integration. It cannot select or recommend thresholds, approve policy, or emit signals.

# 7. Consequences

Controlled studies gain one reproducible invocation contract and explicit provenance for dataset
and configuration versions. Offline callers must supply the execution identity and time. The
service deliberately provides no batch lifecycle, storage, optimization, or interpretation.

# 8. Implementation Impact

Adds immutable execution contracts, typed failures, one execution service, tests, and offline
architecture documentation within the existing backtesting package. No dependency or production
contract changes.

# 9. Future Revisit Criteria

Revisit only if governed research requires persisted execution custody, cryptographic input
identity, or a separately approved batch execution boundary.

# 10. Related ADRs

ADR-006, ADR-007, ADR-011, ADR-012, and ADR-013.
