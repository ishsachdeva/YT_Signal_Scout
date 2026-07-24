# ADR-024: Govern Study Definition and Execution

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## 1. Decision

Add a separate synchronous `StudyExecutionService` that accepts one immutable study definition and
one input bundle containing one governed historical dataset, one canonically ordered evidence-pack
collection, one labelling rubric, one ground-truth label set, and one study configuration. It
validates the complete cohort and returns only immutable metadata, a factual binding context, and a
content-addressed manifest.

This boundary is distinct from `BacktestExecutionService`. The older service evaluates supplied
threshold candidates and returns a factual analytical report. The new service performs no
analytics: execution means validation and deterministic packaging of governed inputs.

## 2. Validation and compatibility

The validator requires exact dataset identity/version across every artifact, exact observation and
channel coverage, evidence timestamps matching historical observations, one evidence pack and one
label per observation, shared evidence-definition binding, exact rubric and label references,
canonical digests, configured schema versions, chronological timezone-aware timestamps, canonical
evidence order, and unique identities inside the execution request. Any failure rejects the entire
request; no partial artifact is returned.

Schema compatibility is explicit and closed at study configuration version 1: Historical Dataset
schema 2 and Evidence Pack, Labelling Rubric, Ground Truth Label, and Study Execution schemas 1.
Support for later schemas requires a new typed contract and deliberate compatibility decision.

Global execution-ID uniqueness cannot be discovered by a stateless service. This boundary rejects
identity reuse within its complete request; a future artifact registry must enforce uniqueness
across separately submitted requests if persistence is approved.

## 3. Determinism and canonical integrity

All timestamps are caller-supplied governed facts; the service does not read a clock. Canonical
UTF-8 JSON sorts object keys, removes insignificant whitespace, retains array order, rejects
non-finite numbers, and covers metadata, context, and every input digest with SHA-256. Equal typed
requests produce byte-identical results.

No importer is added for execution requests. Every governed artifact already enters through its
strict importer, while configuration and definition are typed in-process contracts. A future
external execution-file format may add an importer without changing orchestration semantics.

## 4. Boundary

The service is pure, deterministic, synchronous, stateless, fail-fast, immutable, side-effect
free, and offline. It does not download, generate, modify, persist, label, evaluate, calculate,
rank, recommend, approve, call AI, call YouTube, access a database, or change runtime signals.

In particular, the result contains no threshold, confusion matrix, precision, recall, F1, ROC,
confidence interval, sensitivity analysis, policy recommendation, or Product decision.

## 5. Consequences

Governed research inputs can now cross one explicit execution boundary and yield a reproducible
immutable execution artifact before any separately approved analytical milestone. The public
backtesting package gains study execution contracts, validation, orchestration, canonicalization,
and typed failures. No application API or persistence layer changes.

## 6. Related decisions

ADR-013, ADR-014, ADR-020, ADR-022, ADR-023, and the SIG-002 Research Protocol.

