# ADR-023: Govern Reviewer Evidence Packs and Labelling Rubrics

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Analytics & Engineering

## Supersedes

None. This decision completes the definition and rubric references introduced by ADR-022.

---

# 1. Decision Summary

Represent reviewer evidence as one immutable, versioned `EvidencePackDefinition` plus one concrete,
dataset/observation-bound `EvidencePack`. Represent labelling guidance as one immutable, versioned
`RubricDefinition` containing ordered criteria, all four protocol label states, closed reason codes,
and one non-executing decision rule per state. Strict importers verify schemas, bindings, content,
canonical serialization, and SHA-256 digests. A pure validator binds an existing label artifact to
the exact evidence and rubric without evaluating or changing its decision.

# 2. Context

ADR-022 label artifacts already reference evidence-pack definition, concrete pack, and rubric
identities, versions, and digests. Those references had no corresponding engineering contracts.
The Research Protocol requires every reviewer to inspect the same immutable evidence under the same
rubric while candidate threshold outcomes and other reviewers' decisions remain outside the pack.

The existing policy-free `SignalEvidenceBundle` is not reused. It is a production-facing factual
analytics projection, not a versioned reviewer presentation contract bound to historical dataset
and observation identities.

# 3. Alternatives Considered

## Store free-form JSON or rendered documents

Rejected because hidden fields, untyped values, unstable ordering, and manual edits would weaken
reproducibility. Images, screenshots, thumbnails, OCR, and generated narratives remain prohibited.

## Embed evidence and rubric inside every label artifact

Rejected because shared definitions would be duplicated and could diverge between reviewers.
Content-addressed references preserve exact binding without copying complete contracts.

## Executable rubric rules

Rejected because rubric guidance belongs to independent human research annotation. Executable
rules would become a label engine and blur ground truth with deterministic signal evaluation.

## Separate immutable contracts

Selected. Evidence facts, presentation definition, concrete snapshot, rubric, and label remain
independently versioned and cryptographically bound.

# 4. Evidence Pack Contract

`EvidencePackDefinition` supplies stable identity/version, purpose, creation time, ordered item
definitions, typed fact definitions, and digest. Fact definitions declare a closed primitive type,
required/repeatable semantics, optional unit, and description.

`EvidencePack` binds the exact definition digest to one immutable `EvidenceSnapshot` containing
dataset, observation, channel, snapshot identity/version, and observation time. Ordered items carry
strict facts with exact primitive types, optional repeated subject identities, and semantic units.
Pack creation cannot precede its observation.

Supported fact types are Boolean, integer, finite float, text, and timezone-aware timestamp. No
dictionary payload or executable calculation is accepted.

# 5. Rubric Contract

`RubricDefinition` binds one evidence-pack definition identity/version/digest and contains ordered
criteria, reason codes, and decision rules. Criteria reference evidence item IDs. Allowed decision
states must be exactly Positive, Negative, Borderline, and Unknown in protocol order. Exactly one
rule exists per state in the same order.

Reason codes declare which states they may support. Decision rules reference only known compatible
reason codes and contain human-readable guidance only. No score, weight, expression, threshold,
ranking, or automatic result exists.

# 6. Binding Validation

`GroundTruthLabelBindingValidator` verifies exact definition, pack, rubric, dataset, observation,
and channel identities/versions/digests. It also verifies criterion evidence references and that
each review/adjudication reason code permits its supplied label state.

The validator returns no decision and mutates nothing. It does not authenticate reviewers, enforce
blinding, generate evidence, execute a rubric, or approve research or Product policy.

# 7. Canonical Import and Integrity

Evidence Pack and Labelling Rubric JSON each use strict schema version 1. Unknown/missing fields,
coercive primitives, unsupported schema versions, invalid times/types/order, definition/content
mismatch, and digest mismatch fail the entire import with typed errors.

Canonical UTF-8 JSON retains explicit array order, sorts object keys, removes insignificant
whitespace, retains Unicode, and rejects non-finite numbers. Definition, pack, and rubric digests
exclude only their own digest field. Equal typed inputs produce identical bytes.

# 8. Versioning

Definition, concrete pack, snapshot, and rubric versions are independent positive integers. Any
semantic or content change requires a new version and digest. Label artifacts bind exact versions
and digests; they cannot silently resolve to a later contract.

# 9. Boundary

This framework creates no evidence or rubric instance, acquires no data, calls no API, renders no
media, labels no channel, executes no reviewer workflow or study, calculates no statistics, and
adds no AI, persistence, database, Product policy, threshold, ranking, signal, or runtime behavior.

# 10. Consequences

Ground-truth references now resolve to complete typed contracts, enabling later reproducible label
recording without hidden evidence or rubric drift. The public offline contract surface grows, but
each responsibility remains isolated and testable.

# 11. Implementation Impact

Adds evidence/rubric models, importers, canonicalizers, typed failures, label binding validation,
package exports, focused tests, format specifications, and architecture/navigation updates inside
the existing offline backtesting package.

# 12. Future Revisit Criteria

Revisit if governed evidence generation, authenticated custody, digital signatures, blinded
reviewer delivery, persisted artifact resolution, rendered presentation, or a separately approved
review workflow is required.

# 13. Related Decisions

ADR-011, ADR-013, ADR-020 through ADR-022, and the SIG-002 Research Protocol.
