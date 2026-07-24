# Governed Evaluation Aggregation Contract

Evaluation Aggregation schema version 1 converts exactly one immutable observation-level
`EvaluationResult` into factual cohort counts. It contains no statistical metric.

## Inputs

`EvaluationAggregationRequest` contains one versioned definition and configuration, one exact
evaluation result, and a caller-supplied timezone-aware aggregation timestamp. The configuration
binds the evaluation identity/version, Evaluation schema version 1, and its pre-declared expected
observation count.

## Summary

`EvaluationAggregationSummary` exposes only non-negative integer counts:

- True Positive
- True Negative
- False Positive
- False Negative
- Unknown
- Not Evaluated
- Total Evaluated
- Total Observations

Unknown is evaluated; Not Evaluated is skipped. Structural invariants require Total Evaluated to
equal the five completed outcome counts and Total Observations to equal Total Evaluated plus Not
Evaluated. No percentage, ratio, rate, score, or interval exists.

## Validation

The validator requires exact definition/configuration/evaluation bindings, supported schema and
outcome vocabulary, the declared observation count, unique observation identities, canonical
observation ordering, unique aggregation identities, and a valid source evaluation digest.
Unknown fields fail typed validation. Validation is all-or-nothing.

## Output and canonicalization

`EvaluationAggregationResult` contains factual metadata, one summary, and an immutable manifest
binding the source evaluation-result digest and aggregation-result digest.

Canonical serialization uses UTF-8 JSON, sorted object keys, no insignificant whitespace, retained
Unicode, and rejection of non-finite values. SHA-256 covers all metadata, counts, and the source
digest while excluding only the result digest's own field.

This boundary has no importer because it consumes an already typed and integrity-validated
`EvaluationResult`; a future external artifact format requires separate approval.

