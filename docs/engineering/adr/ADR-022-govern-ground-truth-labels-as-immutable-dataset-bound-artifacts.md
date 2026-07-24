# ADR-022: Govern Ground-Truth Labels as Immutable Dataset-Bound Artifacts

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## Supersedes

None. This decision implements the label boundary required by the SIG-002 Research Protocol and
remains separate from ADR-017 methodology-based study evaluation.

---

# 1. Decision Summary

Represent channel ground truth as immutable, versioned label artifacts bound to one exact
historical dataset observation and one exact evidence/rubric definition. Every artifact contains
exactly two independent reviews. Matching reviews establish the final label directly; disagreement
requires a third independent adjudicator. Versioned label sets enter through strict JSON import,
are canonically ordered, and carry a SHA-256 digest over complete metadata and label content.

# 2. Context

The Research Protocol permits only Positive, Negative, Borderline, and Unknown labels and requires
two blinded independent reviewers, adjudication of disagreements, immutable evidence references,
version history, and deterministic artifacts. Existing `BacktestStudyEvaluation` records a human
interpretation of aggregate study evidence. It does not label an individual channel observation
and must not be reused as ground truth.

# 3. Alternatives Considered

## Add labels to historical observations

Rejected because factual datasets and later human annotations have independent custody, version,
and correction lifecycles.

## Reuse study evaluation artifacts

Rejected because methodology criteria and research recommendations concern an executed aggregate
study, not blinded observation-level classification.

## Mutable label history or persistence

Rejected because no database, workflow, permissions, or operational service is approved. Immutable
replacement artifacts preserve history without mutable state.

## Dataset-bound immutable label artifacts

Selected. This keeps facts, labels, study evaluation, and Product policy in separate contracts.

# 4. Label Contract

`GroundTruthLabel` is a closed enum containing only `positive`, `negative`, `borderline`, and
`unknown`. `GroundTruthLabelArtifact` binds label-set, dataset, observation, and channel identities;
one evidence-pack definition, concrete pack, and rubric reference; exactly two independent
reviews; optional disagreement adjudication; one final label; and optional supersession history.

Reviewer identifiers are stable supplied research identities, not authentication claims. Review
and adjudication timestamps are timezone-aware. Reason codes are bounded machine identifiers and
notes are bounded human text.

# 5. Independence and Adjudication

Independent review IDs and reviewer IDs must be unique. Matching reviews prohibit adjudication and
must equal the final label. Disagreement requires an adjudicator distinct from both reviewers, an
adjudication at or after both reviews, and a final label equal to the adjudicated decision.

The framework validates supplied decisions; it does not assign reviewers, hide evidence, calculate
agreement, or perform workflow execution.

# 6. Versioning and History

Initial artifacts use version 1 and have no supersession fields. A replacement increments the
artifact version by exactly one, binds an earlier label-set version and the same artifact identity,
and records a non-empty change reason. Previous artifacts remain immutable and external; no
in-place update occurs.

One label-set manifest binds a positive label-set version to one exact dataset ID/version, creator,
creation time, schema version, and content digest. Artifact identity, dataset, and label-set
bindings must agree with the manifest.

# 7. Canonical Import and Integrity

Ground Truth Label JSON schema version 1 is strict and all-or-nothing. Import rejects unknown or
missing fields, primitive coercion, invalid labels or timestamps, duplicate artifact/observation/
channel identities, inconsistent evidence/rubric definitions, binding mismatches, and digest
mismatch.

Canonical UTF-8 JSON sorts object keys, label artifacts by observation/artifact identity, and
independent reviews by review ID. The SHA-256 digest covers the complete manifest except its digest
and every canonical artifact. Equivalent input ordering produces equal label sets and bytes.

# 8. Boundary

This framework creates no real labels, assigns no reviewer, imports no repository dataset, calls no
API, executes no study, calculates no agreement or classification metric, and adds no persistence,
database, UI, AI, Product policy, threshold, ranking, signal, or runtime behavior.

Labels and study evaluations may inform development-time Product decisions under ADR-021. Neither
authorizes individual production outcomes or participates in autonomous runtime execution.

# 9. Consequences

Future studies gain reproducible ground-truth inputs independently versioned from historical facts.
The additional label schema and models increase contract surface, but prevent labels from mutating
datasets or leaking into production authorization.

# 10. Implementation Impact

Adds label models, strict importer, canonicalizer, typed failures, package exports, focused tests,
format documentation, and architecture/navigation references inside the existing offline
backtesting package. No existing serialized artifact or production contract changes.

# 11. Future Revisit Criteria

Revisit if authenticated reviewer identity, blind-review assignment, signatures, persisted label
custody, rubric registries, evidence-pack storage, or an explicitly approved label workflow service
is required.

# 12. Related Decisions

ADR-013, ADR-017, ADR-020, ADR-021, and the SIG-002 Research Protocol.
