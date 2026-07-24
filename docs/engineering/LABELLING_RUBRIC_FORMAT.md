# Labelling Rubric JSON Format

Ground-truth labelling rubrics use strict JSON schema version 1 and enter only through
`RubricImporter`. A rubric describes how independent reviewers interpret defined evidence; it is
not an executable label engine.

## Top-level shape

```json
{
  "schema_version": 1,
  "rubric": {}
}
```

## Rubric definition

`RubricDefinition` records:

- stable rubric identity and positive version;
- name, purpose, and timezone-aware creation time;
- exact evidence-pack definition identity/version/digest;
- ordered qualitative criteria and their evidence item references;
- exactly the four protocol label states in protocol order;
- closed reason-code definitions and their permitted labels;
- exactly one ordered human-readable decision rule per label; and
- canonical SHA-256 digest.

Criteria and rules preserve supplied order. IDs are unique. Decision rules may reference only
known reason codes that permit the rule's label.

The only decision states are `positive`, `negative`, `borderline`, and `unknown`. Rules contain
guidance text only. No expression, threshold, score, weight, ranking, code callback, automatic
result, or Product policy is supported.

## Canonicalization and integrity

The rubric digest covers the schema wrapper and complete rubric except its own digest. Canonical
JSON uses UTF-8, sorted object keys, explicit array order, retained Unicode, no insignificant
whitespace, and no non-finite numbers.

`RubricCanonicalizer` calculates/verifies the digest and serializes a validated import to stable
bytes.

## Label binding

`GroundTruthLabelBindingValidator` can verify that an existing label artifact references the exact
evidence definition, concrete pack, rubric, dataset, observation, channel, and digests. It also
checks criterion evidence IDs and label-compatible reason codes. It does not choose, adjudicate,
or mutate a label.

## Strict validation

Import rejects unsupported schemas, missing or unknown fields, coercive primitives, naive times,
duplicate identities, incomplete/reordered label states or rules, unknown/incompatible reason
codes, and digest mismatch. No partial result is returned. Typed failures distinguish reads,
syntax, schema, structure, and integrity.

Import performs no labelling, reviewer workflow, statistics, study execution, Product decision, or
runtime behavior. See ADR-023.
