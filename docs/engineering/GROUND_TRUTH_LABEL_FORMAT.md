# Ground Truth Label JSON Format

Ground-truth channel labels use strict JSON schema version 1 and enter only through
`GroundTruthLabelImporter`. The schema represents supplied research annotations; importing it does
not label channels or execute research.

## Document shape

```json
{
  "manifest": {
    "schema_version": 1,
    "label_set_id": "sig-002-labels-v1",
    "label_set_version": 1,
    "dataset_id": "research-dataset-v1",
    "dataset_version": 1,
    "created_at": "2026-07-24T12:00:00Z",
    "creator_identity": "analytics-owner",
    "digest": {
      "algorithm": "sha256",
      "value": "<64 lowercase hexadecimal characters>"
    }
  },
  "artifacts": []
}
```

The actual `artifacts` array must be non-empty. The empty example only illustrates top-level
shape; this repository contains no ground-truth label instance.

## Label artifact

Each artifact requires:

- stable artifact identity and positive version;
- matching label-set ID/version;
- exact historical dataset ID/version;
- observation ID and canonical channel ID;
- evidence-pack definition identity/version, concrete channel-pack identity/version/digest, and
  rubric identity/version/digest;
- exactly two independent review records;
- an adjudication only when independent labels disagree;
- one final protocol-defined label; and
- supersession reference and change reason for replacement versions.

The only label values are:

- `positive`
- `negative`
- `borderline`
- `unknown`

## Independent reviews

Every review records a unique review ID, unique reviewer ID, timezone-aware review timestamp, one
closed label, a reason code, and optional reasoning notes. Reviewer IDs are supplied research
identities and do not prove authentication.

When both reviews match, adjudication is prohibited and their label is final. When they disagree,
an adjudicator distinct from both reviewers records a timezone-aware later decision, reason code,
required reasoning notes, and the final label.

The framework validates these facts but does not assign reviewers, enforce blinding operationally,
or calculate agreement.

## Evidence binding

Every artifact records the exact concrete evidence-pack identity/version/content digest and exact
rubric identity/version/digest used for the decision. All artifacts in one label set use the same
evidence-pack definition identity/version and rubric version; concrete channel evidence-pack IDs
and content digests may differ.

The label-set manifest and every artifact bind the same historical dataset identity/version. Labels
never modify or become fields on the historical dataset.

## Version history

Version 1 artifacts have no supersession reference. A replacement artifact:

- increments its artifact version by exactly one;
- retains the same artifact and label-set identities;
- references an earlier label-set version and immediately previous artifact version; and
- records a non-empty change reason.

Historical versions remain immutable and are not embedded automatically in the current label set.

## Canonicalization and integrity

Digest input is canonical UTF-8 JSON containing the complete manifest except `digest` plus every
artifact. Object keys are lexicographically sorted, artifacts are ordered by observation ID then
artifact ID, reviews are ordered by review ID, Unicode is retained, insignificant whitespace is
removed, and non-finite JSON numbers are prohibited.

`GroundTruthLabelCanonicalizer.calculate_digest(...)` computes the digest.
`serialize_import_result(...)` emits stable canonical bytes for a validated import result.

## Strict validation and typed failures

Import rejects:

- unsupported schema versions;
- missing or unknown fields and coercive primitives;
- labels outside the four protocol states;
- naive timestamps;
- review or adjudication timestamps after label-set creation;
- duplicate review, reviewer, artifact, observation, or channel identities;
- missing, unnecessary, non-independent, or early adjudication;
- invalid supersession history;
- label-set, dataset, evidence, or rubric binding mismatches; and
- canonical digest mismatch.

Typed failures distinguish file reads, JSON syntax, unsupported schemas, structural validation,
duplicates, and digest mismatches. No partial label set is returned.

## Programmatic use

```python
from app.services.backtesting import (
    GroundTruthLabelCanonicalizer,
    GroundTruthLabelImporter,
)

result = GroundTruthLabelImporter().import_file("ground-truth-labels.json")
canonical_bytes = GroundTruthLabelCanonicalizer.serialize_import_result(result)
label_set = result.label_set
```

Import and serialization perform no statistics, threshold evaluation, study execution, Product
decision, or runtime signal behavior. See ADR-022 and the SIG-002 Research Protocol.
