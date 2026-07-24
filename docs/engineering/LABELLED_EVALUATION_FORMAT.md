# Deterministic Labelled Evaluation Contract

Labelled Evaluation schema version 1 represents factual prediction-versus-truth outcomes for each
governed observation. It contains no aggregate result.

## Inputs

`EvaluationRequest` contains one versioned definition and configuration, one completed governed
study execution, the exact historical dataset and Ground Truth Label Set used by that execution,
one ordered prediction for every dataset observation, and a timezone-aware caller-supplied
evaluation timestamp.

The prediction vocabulary is Positive, Negative, Unknown, and Not Evaluated. Every prediction
binds a stable prediction ID to the exact observation ID and channel ID.

## Observation mapping

| Prediction | Ground truth | Observation outcome |
|---|---|---|
| Positive | Positive | True Positive |
| Negative | Negative | True Negative |
| Positive | Negative | False Positive |
| Negative | Positive | False Negative |
| Unknown | Any label | Unknown |
| Positive or Negative | Borderline or Unknown | Unknown |
| Not Evaluated | Any label | Not Evaluated |

The outcome is one categorical fact. The contract has no confusion-matrix totals, counts,
percentages, rates, statistics, metrics, scores, or recommendations.

## Output and integrity

`EvaluationResult` contains factual metadata, exactly one canonically ordered
`ObservationEvaluation` per dataset observation, and an immutable manifest. The manifest binds the
study-execution, dataset, label-set, and ordered-prediction SHA-256 digests plus the result digest.

Canonical serialization is UTF-8 JSON with sorted object keys, no insignificant whitespace,
Unicode retained, governed tuple order retained, and non-finite values rejected. The result digest
excludes only its own field.

## Failure behavior

Typed validation rejects missing/unknown fields and unsupported vocabulary. `EvaluationValidator`
rejects dataset, execution, label, observation, channel, ordering, duplicate, version, and digest
mismatches. `EvaluationDigestMismatchError` rejects corrupted source integrity or altered result
content. Validation is all-or-nothing and returns no partial evaluation.
