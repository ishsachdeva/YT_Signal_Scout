# ADR-027: Govern Deterministic Statistical Evaluation

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## 1. Decision

Add a pure `StatisticalEvaluationService` that consumes exactly one immutable ADR-026 aggregation
result and calculates the approved metric set: accuracy, precision, recall/sensitivity,
specificity, negative predictive value, false-positive rate, false-negative rate, balanced
accuracy, F1, and Matthews correlation coefficient (MCC). It also emits two-sided 95% Wilson score
intervals for accuracy, precision, recall, specificity, and balanced accuracy.

This boundary calculates mathematics only. It does not compare candidates or thresholds,
interpret values, rank alternatives, select policy, or recommend action. Optional likelihood and
odds metrics are deferred to avoid expanding the approved contract without need.

## 2. Mathematical definitions

For TP, TN, FP, and FN:

```text
accuracy = (TP + TN) / (TP + TN + FP + FN)
precision = TP / (TP + FP)
recall = sensitivity = TP / (TP + FN)
specificity = TN / (TN + FP)
negative predictive value = TN / (TN + FN)
false-positive rate = FP / (FP + TN)
false-negative rate = FN / (FN + TP)
balanced accuracy = (recall + specificity) / 2
F1 = 2TP / (2TP + FP + FN)
MCC = (TP*TN - FP*FN) /
      sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
```

Unknown and Not Evaluated counts remain preserved in the source artifact but do not enter these
binary-classification formulas.

## 3. Undefined-domain policy

Every configured metric is mandatory. Zero accuracy, precision, recall, specificity, negative
predictive-value, F1, or MCC denominators reject the entire request. The service never substitutes
zero, infinity, NaN, null, or a partial result. This strict engineering artifact is emitted only
for cohorts on which the complete approved metric set is mathematically defined.

## 4. Wilson convention

Use `z = 1.959963984540054` and the canonical two-sided Wilson transform:

```text
center = (p + z²/(2n)) / (1 + z²/n)
half_width = z * sqrt((p(1-p) + z²/(4n))/n) / (1 + z²/n)
```

Accuracy uses binary cohort size; precision uses predicted-positive support; recall uses
actual-positive support; and specificity uses actual-negative support. At the handoff's explicit
direction, balanced accuracy applies the same transform to the balanced-accuracy estimate using
binary cohort size. This is a governed plug-in convention: balanced accuracy is an average of two
conditional proportions, not itself a raw binomial success fraction. The artifact makes the
estimate and sample-size convention explicit and makes no inferential interpretation.

## 5. Determinism and integrity

Calculations use Python `Decimal` with precision 50 and exact decimal constants. Only final finite,
bounded contract values convert to binary64 floats. All times are caller supplied. Canonical UTF-8
JSON sorts object keys, removes insignificant whitespace, retains Unicode, rejects non-finite
numbers, and hashes metadata, metrics, intervals, and the exact aggregation-result digest with
SHA-256.

## 6. Validation and boundary

Validation rejects negative/non-integer or inconsistent counts, aggregation identity/version or
schema mismatch, invalid aggregation integrity, undefined domains, duplicate statistical
identities, unknown fields, and naive/invalid times.

The boundary is pure, deterministic, offline, immutable, stateless, synchronous, fail-fast,
side-effect free, and without persistence. It contains no threshold comparison/ranking/selection,
optimization, weighting, scoring model, business interpretation, recommendation, Product
decision, runtime signal, API, workflow, or AI.

## 7. Consequences

The repository can now produce a complete reproducible mathematical artifact from governed cohort
counts. Human research interpretation, sensitivity analysis, candidate comparison, and Product
policy remain separate future responsibilities.

## 8. Related decisions

ADR-016, ADR-024 through ADR-026, and the SIG-002 Research Protocol.

