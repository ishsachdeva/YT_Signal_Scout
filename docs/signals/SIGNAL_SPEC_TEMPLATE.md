# SIG-XXX — Signal Name

## Specification metadata

| Field | Value |
|---|---|
| Signal identifier | `SIG-XXX` |
| Specification version | 1 |
| Approval status | Draft |
| Implementation status | Not implemented |
| Catalog alignment | Pending |
| Decision owner | Pending |
| Decision date | Pending |
| Decision reference | Pending |

## Name

Provide the stable user-facing signal name.

## Purpose

State the single observation this signal communicates without implying causality or prediction.

## Business value

Explain why this observation helps the intended user make a decision.

## User problem solved

Describe the concrete user question answered by this signal.

## Category

Record an approved category or `PENDING PRODUCT DECISION`. Do not invent taxonomy in engineering.

## Dependencies

List approved product policies, canonical facts, analytics, qualification, evidence, and runtime
contracts required before evaluation.

## Analytics required

List existing factual metrics by exact identity, type, availability semantics, and time basis. Do
not duplicate formulas owned by analytics except as normative references.

## Qualification requirements

State every dataset- and channel-level precondition. Define whether failed qualification emits no
signal, emits another approved signal, or is invalid input.

## Formula

Define the deterministic business condition symbolically. Mark every unresolved term
`PENDING PRODUCT DECISION`.

## Variables

| Variable | Meaning | Source | Type | Availability |
|---|---|---|---|---|
| `x` | Define | Define | Define | Define |

## Units

Define semantic units for observed values, thresholds, samples, and time values.

## Comparator

Specify the approved operator or `PENDING PRODUCT DECISION`.

## Threshold

Specify value, provenance, owner, and version or `PENDING PRODUCT DECISION`.

## Boundary conditions

Define null, zero, non-finite, minimum-sample, qualification, timestamp, and precision behavior.

## Equality behavior

State whether equality triggers or `PENDING PRODUCT DECISION`.

## Expected inputs

Describe the exact immutable input contract and prohibited substitutes.

## Expected outputs

Define zero/one/many cardinality, stable identities, polarity, rule version, and coexistence rules.
Do not add severity, confidence, score, narrative, or presentation fields without approved policy
and architecture.

## Evidence required

List only facts used by the condition or required to explain its validity and limitations.

## Evidence structure

Map each evidence fact to its identity, type, unit, provenance, and containing contract. Mark
unsupported emitted-evidence fields as blockers rather than generic payloads.

## False positives

List known conditions that can make the signal appear stronger than the underlying opportunity.

## False negatives

List known conditions that can suppress a legitimate opportunity.

## Known limitations

State data-source, denominator, sampling, time-basis, eligibility, and interpretation constraints.

## Examples that SHOULD trigger

Provide boundary-focused factual examples only after comparator and threshold approval.

## Examples that MUST NOT trigger

Include failed qualification, unavailable metrics, equality boundary, and immediately adjacent
non-trigger examples after policy approval.

## Future improvements

Record non-blocking ideas separately from version-1 behavior.

## Performance considerations

State expected complexity and prohibit unnecessary I/O, caching, or recomputation.

## Version history

| Version | Date | Change | Approval reference |
|---|---|---|---|
| 1 | YYYY-MM-DD | Initial draft | Pending |

## Open questions

List every unresolved product, analytics, and architecture decision with an owner.

## Approval status

Record Product, Analytics, and Architecture disposition with decision owner, decision date,
decision reference, scope, and catalog status. Approval is version-controlled documentation
metadata, not a separate approval artifact or runtime workflow. Never infer approval from document
presence alone.

## Implementation status

Record Not implemented, Blocked, Implementable Now, Implemented, or Deprecated and cite evidence.

## Related ADRs

List accepted architecture decisions governing the signal.

## Related analytics

List exact metric identities and calculators or services that own them.

## Related qualification rules

List exact qualification policy version, failure semantics, and required evidence.
