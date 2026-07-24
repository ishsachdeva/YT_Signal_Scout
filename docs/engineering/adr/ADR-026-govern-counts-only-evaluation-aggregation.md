# ADR-026: Govern Counts-Only Evaluation Aggregation

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## 1. Decision

Add a pure `EvaluationAggregationService` that consumes exactly one immutable ADR-025
`EvaluationResult` and counts its closed observation outcomes once. It returns only True Positive,
True Negative, False Positive, False Negative, Unknown, Not Evaluated, Total Evaluated, and Total
Observations integer counts.

This boundary is separate from observation-level comparison, threshold analysis, statistical
methodology, qualitative review, and Product governance.

## 2. Count semantics

Unknown is a completed factual evaluation state and contributes to Total Evaluated. Not Evaluated
is an explicit skipped state and does not. Therefore:

```text
Total Evaluated = TP + TN + FP + FN + Unknown
Total Observations = Total Evaluated + Not Evaluated
```

These identities are structural validation rules, not statistical calculations. The contract has
no division, ratio, percentage, rate, interval, score, ranking, or recommendation.

## 3. Input governance and validation

One versioned aggregation definition binds one configuration to one evaluation identity/version,
Evaluation schema version 1, and a pre-declared expected observation count. Validation rejects
mismatched evaluation identities or versions, missing/count-mismatched observations, duplicate
observation outcomes, non-canonical observation order, duplicate aggregation identities, unknown
fields or outcome states, and invalid evaluation-result integrity.

The supplied evaluation result remains authoritative. Aggregation does not reconstruct outcomes,
inspect predictions or labels, or alter observation facts.

## 4. Canonical integrity

The caller supplies all timestamps. Canonical UTF-8 JSON sorts object keys, removes insignificant
whitespace, retains Unicode, and rejects non-finite values. The immutable manifest binds the exact
source evaluation-result digest. SHA-256 covers metadata, every summary count, and that source
digest. Equal typed input produces byte-identical output.

## 5. Boundary

Aggregation is pure, deterministic, offline, immutable, stateless, synchronous, fail-fast,
side-effect free, and without persistence. It calculates no precision, recall, specificity,
sensitivity, accuracy, F1, MCC, ROC, AUC, confidence interval, confidence bound, significance test,
or other derived statistic. It does not evaluate or recommend thresholds, rank alternatives,
create Product decisions, emit runtime signals, call AI, expose an API, or run a workflow.

## 6. Consequences

The repository now has an explicit factual cohort-count boundary that can support a later,
separately governed statistical metric layer. The public offline contract surface grows by one
small aggregation module without changing runtime application behavior.

## 7. Related decisions

ADR-012, ADR-016, ADR-024, ADR-025, and the SIG-002 Research Protocol.

