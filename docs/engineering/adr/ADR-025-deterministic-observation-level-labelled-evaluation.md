# ADR-025: Deterministic Observation-Level Labelled Evaluation

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## 1. Decision

Add a pure `LabelledEvaluationService` that compares one supplied prediction for every governed
dataset observation with that observation's final Ground Truth Label. The service returns a
canonically ordered tuple of immutable `ObservationEvaluation` facts and no aggregate.

This boundary is separate from the qualitative human `BacktestStudyEvaluation`, the analytical
threshold backtester, and the non-analytical governed `StudyExecutionService`.

## 2. Outcome vocabulary

Predictions are closed to Positive, Negative, Unknown, and Not Evaluated. Ground truth remains
Positive, Negative, Borderline, and Unknown under ADR-022. Binary comparisons produce True
Positive, True Negative, False Positive, or False Negative. Borderline or Unknown truth and an
Unknown prediction produce Unknown. An explicit Not Evaluated prediction produces Not Evaluated.

These names describe one observation's factual relationship only. They are not confusion-matrix
totals. No counts, rates, statistics, metrics, ranking, threshold selection, or recommendation are
present.

## 3. Inputs and validation

One request binds a versioned definition and configuration to one completed governed study
execution, its exact historical dataset, exact Ground Truth Label Set, and one canonically ordered
prediction per dataset observation. The validator rejects mismatched identities/versions,
incomplete or unknown observations, channel mismatch, duplicate observations/predictions,
duplicate evaluation identities, unsupported prediction vocabulary, non-canonical order, and
dataset, label, or study-execution digest corruption.

The prediction vocabulary is explicitly version 1. Compatibility with a later vocabulary or
schema requires a new versioned configuration and deliberate contract change.

## 4. Canonical integrity

All times are caller supplied. Canonical UTF-8 JSON sorts object keys, removes insignificant
whitespace, preserves observation order and Unicode, and rejects non-finite values. SHA-256 covers
the ordered predictions, governed input digests, metadata, every observation evaluation, and the
result manifest. Equal typed inputs produce byte-identical results.

## 5. Boundary

Evaluation is deterministic, offline, immutable, stateless, synchronous, fail-fast, side-effect
free, and without persistence. It does not calculate precision, recall, specificity, sensitivity,
F1, MCC, ROC, AUC, intervals, totals, or any other aggregation. It does not generate predictions,
evaluate thresholds, recommend policy, create Product decisions, emit runtime signals, call AI,
expose an API, or run a workflow.

## 6. Consequences

The repository can now preserve the complete observation-level factual basis needed by a later,
separately governed aggregation milestone. The public offline contract surface gains prediction,
evaluation, manifest, validation, canonicalization, and typed error contracts without changing
runtime application behavior.

## 7. Related decisions

ADR-012, ADR-016, ADR-022 through ADR-024, and the SIG-002 Research Protocol.

