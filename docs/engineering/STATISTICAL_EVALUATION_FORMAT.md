# Governed Statistical Evaluation Contract

Statistical Evaluation schema version 1 consumes exactly one immutable Evaluation Aggregation
result and calculates the complete approved mathematical metric set. It contains no interpretation,
ranking, selection, or recommendation.

## Inputs

`StatisticalEvaluationRequest` contains one definition, one configuration, the exact aggregation
result, and a timezone-aware caller-supplied timestamp. Configuration pins the aggregation
identity/version, Aggregation schema version 1, confidence level `0.95`, and Wilson constant
`1.959963984540054`.

## Metrics

Given TP, TN, FP, and FN:

| Field | Formula |
|---|---|
| Accuracy | `(TP + TN) / (TP + TN + FP + FN)` |
| Precision | `TP / (TP + FP)` |
| Recall | `TP / (TP + FN)` |
| Sensitivity | Equal to Recall |
| Specificity | `TN / (TN + FP)` |
| Negative Predictive Value | `TN / (TN + FN)` |
| False Positive Rate | `FP / (FP + TN)` |
| False Negative Rate | `FN / (FN + TP)` |
| Balanced Accuracy | `(Recall + Specificity) / 2` |
| F1 | `2TP / (2TP + FP + FN)` |
| MCC | `(TP*TN - FP*FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))` |

Unknown and Not Evaluated do not enter binary metric formulas. All metrics must be finite;
probability-like metrics remain within `[0,1]` and MCC within `[-1,1]`.

## Wilson intervals

Accuracy, precision, recall, specificity, and balanced accuracy include an immutable
`WilsonScoreInterval` with estimate, lower/upper bounds, and sample size. Accuracy and balanced
accuracy use binary cohort size; precision uses `TP+FP`; recall uses `TP+FN`; specificity uses
`TN+FP`.

Balanced accuracy uses a specified plug-in Wilson transform over the averaged estimate and binary
cohort size. It is not represented as a raw binomial success fraction and receives no inferential
interpretation in this contract. Consumers distinguish it through the dedicated
`balanced_accuracy_interval` field; changing its convention or sample-size rule requires a new
version.

## Undefined domains and validation

Every metric is required. A zero denominator or MCC factor rejects the request; no partial result,
null, zero substitution, infinity, or NaN is emitted. Validation also rejects invalid counts or
totals, aggregation identity/version/schema mismatch, aggregation digest mismatch, duplicate
identities, unknown fields, and naive timestamps. Aggregation integrity failures are translated to
the statistical digest-error subtype; unrelated programming errors are not intercepted.

## Determinism and canonical integrity

Arithmetic uses Decimal precision 50 with exact constants before final finite floats are created.
Canonical output uses UTF-8 JSON, sorted object keys, no insignificant whitespace, retained
Unicode, and rejection of non-finite values. The manifest binds the source aggregation-result
digest and SHA-256 of all statistical metadata, metrics, and intervals.
