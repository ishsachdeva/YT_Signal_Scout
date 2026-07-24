# PDR-001: SIG-002 Product Policy

## Decision metadata

| Field | Value |
|---|---|
| Decision ID | `PDR-001` |
| Title | SIG-002 Product Policy |
| Version | 1 |
| Status | Draft |
| Decision date | Not decided |
| Effective date | Not effective |
| Accountable owner | Product Owner |
| Required reviewers | Analytics Owner; Architecture Owner |
| Analytics review disposition | Pending; no review recorded |
| Analytics review date | Not recorded |
| Architecture review disposition | Pending; no review recorded |
| Architecture review date | Not recorded |
| Affected signal | `SIG-002` |
| Affected rule version | 1 |
| Documentation target | v0.9.0 |
| Effective runtime release | Unassigned; this Draft authorizes no runtime behavior |
| Supersedes | None |

## Decision scope

This record governs the Product-owned behavior required for SIG-002: production threshold,
comparator, equality behavior, required business evidence, evidence cardinality, boundary examples,
and coexistence meaning. It does not own metric calculation, analytical validity, typed contract
design, rule-input boundaries, implementation, composition, or release execution.

Every decision remains `PENDING PRODUCT DECISION`. This Draft records the questions and evidence
requirements; it does not approve a value, operator, boundary, evidence set, or coexistence policy.

## Decision inventory

### 1. Production threshold

**Current status:** Undecided.

**Blocking marker:** `PENDING PRODUCT DECISION`.

**Decision required:** Select and version production threshold `T`, including whether it is fixed,
subscriber-band-specific, or cohort-relative.

**Evidence available:** The repository defines `median_standard_video_vsr`, its ratio unit and null
semantics, deterministic threshold-candidate backtesting, governed dataset import, controlled
execution, study artifacts, evaluation methodology, and human evaluation contracts.

**Evidence missing:** No governed historical dataset, executed report, study artifact, completed
evaluation, sensitivity findings, labelled-channel review, false-positive/false-negative review,
or approved research recommendation is committed.

**Alternatives recorded, not selected:** Fixed VSR, subscriber-band threshold, or cohort percentile,
as documented by the Signal Catalog.

**Decision rationale:** Insufficient governed evidence exists to select a defensible production
threshold without inventing policy.

**Downstream dependencies:** Comparator and equality review, boundary examples, required evidence,
Architecture evidence representation, rule-input boundary, catalog approval, and implementation.

**Approval state:** Not approved. Product Owner decision and Analytics Owner plus Architecture Owner
review are pending.

### 2. Comparator

**Current status:** Undecided. `>=` is a proposal only.

**Blocking marker:** `PENDING PRODUCT DECISION`.

**Decision required:** Select the production comparator for observed median VSR and `T`.

**Evidence available:** The backtesting contracts can evaluate supplied `>` and `>=` candidates;
the catalog records both as candidate behavior.

**Evidence missing:** No executed comparison, boundary sensitivity result, or reviewed impact on
false positives and false negatives exists.

**Alternatives recorded, not selected:** `>` or `>=`.

**Decision rationale:** Candidate support is not evidence that either comparator is appropriate for
production.

**Downstream dependencies:** Equality behavior, boundary examples, business evidence, typed
comparison evidence, catalog approval, and rule tests.

**Approval state:** Not approved. Product Owner decision and required reviews are pending.

### 3. Equality behavior

**Current status:** Undecided. Equality triggering is proposed only.

**Blocking marker:** `PENDING PRODUCT DECISION`.

**Decision required:** State explicitly whether an observed median VSR equal to `T` emits SIG-002.

**Evidence available:** Full-precision comparison and no pre-comparison rounding are already
documented constraints.

**Evidence missing:** No approved comparator, threshold, equality-boundary sensitivity result, or
reviewed adjacent-value examples exists.

**Alternatives recorded, not selected:** Equality triggers or equality does not trigger.

**Decision rationale:** Equality cannot be inferred from the catalog's proposed `>=` notation.

**Downstream dependencies:** Boundary examples, typed comparator evidence, and deterministic rule
tests.

**Approval state:** Not approved. Product Owner decision and required reviews are pending.

### 4. Required business evidence

**Current status:** Undecided. Existing evidence lists are proposed.

**Blocking marker:** `PENDING PRODUCT DECISION`.

**Decision required:** Approve the minimum factual evidence that must explain why SIG-002 exists
and its limitations, without selecting its Python representation.

**Evidence available:** ADR-011 provides policy-free qualification, sample, subscriber state,
resolution, median VSR, unit, evaluation time, and provenance facts. The Signal Catalog and SIG-002
specification list candidate emitted facts.

**Evidence missing:** No approved threshold or comparator, reviewed explanation sufficiency,
consumer requirement, or Product disposition identifying which candidate facts are mandatory.

**Alternatives recorded, not selected:** A minimal set limited to comparison facts, or a broader set
that also includes qualification and acquisition context. Generic untyped payloads remain
prohibited by existing architecture.

**Decision rationale:** Product must define what the evidence communicates before Architecture can
choose its typed representation.

**Downstream dependencies:** Evidence cardinality, Architecture representation and provenance
composition, implementation mapping, and catalog readiness.

**Approval state:** Not approved. Product Owner decision and required reviews are pending.

### 5. Evidence cardinality

**Current status:** Undecided.

**Blocking marker:** `PENDING PRODUCT DECISION`.

**Decision required:** Approve which evidence facts are mandatory, optional, or prohibited for one
emitted SIG-002 signal. This decision concerns business sufficiency, not collection or model shape.

**Evidence available:** Current `Signal` requires at least one emitted `SignalEvidence`; ADR-011
provides a fixed upstream factual bundle. Neither contract decides SIG-002's emitted evidence set.

**Evidence missing:** An approved business evidence inventory and reviewed explanation contract.

**Alternatives recorded, not selected:** Exactly the approved minimum facts, or approved mandatory
facts plus explicitly optional factual context.

**Decision rationale:** Cardinality cannot be approved before the evidence meaning is approved.

**Downstream dependencies:** Architecture contract design, validation, mapping, serialization, and
rule tests.

**Approval state:** Not approved. Product Owner decision and required reviews are pending.

### 6. Boundary examples

**Current status:** Undecided and not constructible authoritatively.

**Blocking marker:** `PENDING PRODUCT DECISION`.

**Decision required:** Record exact below-threshold, equality, and above-threshold examples using
the approved threshold, comparator, full precision, and qualification behavior.

**Evidence available:** Qualification failures, unavailable median behavior, and the prohibition on
pre-comparison rounding are already documented.

**Evidence missing:** Approved `T`, comparator, equality behavior, and reviewed adjacent numeric
values.

**Alternatives recorded, not selected:** Examples will cover immediately below, exactly equal, and
immediately above the approved boundary; their values cannot yet be supplied.

**Decision rationale:** Numeric examples created before boundary approval would silently define
policy.

**Downstream dependencies:** Acceptance tests, rule implementation, and catalog Implementable Now
review.

**Approval state:** Not approved. Product Owner decision and Analytics Owner review are pending.

### 7. Coexistence

**Current status:** Undecided. Coexistence with SIG-001 and SIG-003 is proposed only.

**Blocking marker:** `PENDING PRODUCT DECISION`.

**Decision required:** Define whether SIG-002 may coexist with other approved signals for the same
channel and snapshot, and whether any Product-level suppression rule applies.

**Evidence available:** ADR-006 preserves ordered signals from distinct rules and does not merge
duplicate signal types. No production rules currently exist.

**Evidence missing:** Approved SIG-001 or SIG-003 behavior, user-facing coexistence requirements,
and evidence that suppression would be useful or safe.

**Alternatives recorded, not selected:** Independent coexistence, explicit mutual exclusion, or a
future policy scoped to a versioned production composition. Ranking and scoring are outside scope.

**Decision rationale:** Coexistence does not block isolated SIG-002 rule design, but must be decided
before multi-rule production composition.

**Downstream dependencies:** Future multi-rule composition and downstream presentation. It does not
close or replace any P0 SIG-002 blocker.

**Approval state:** Not approved. Product Owner decision and Architecture Owner review are pending.

## Research references

The repository contains research capabilities and contracts, not completed SIG-002 research
evidence:

- The [SIG-002 Research Protocol](../../research/SIG-002_RESEARCH_PROTOCOL.md) defines the
  mandatory dataset, labelling, evaluation, boundary-testing, study-acceptance, and Product
  evidence methodology for future studies without selecting a threshold.
- ADR-012 defines deterministic subscriber-band threshold backtesting.
- ADR-013 defines governed historical dataset import.
- ADR-014 defines controlled deterministic execution.
- ADR-015 defines immutable study artifacts.
- ADR-016 defines factual evaluation methodology.
- ADR-017 defines immutable human evaluation artifacts.
- ADR-021 supersedes the manual-approval portions of ADR-018 and ADR-019 and defines one-time
  Product/release governance followed by autonomous runtime evaluation.
- ADR-022 defines immutable dataset-bound ground-truth labels without making a Product decision.

No governed dataset instance, execution result, study artifact, completed human evaluation, or
research recommendation is committed. Test fixtures prove contract behavior only and are not
Product evidence.

## Traceability

- [Decision Governance](../../governance/DECISION_GOVERNANCE.md)
- [Signal Catalog](../SIGNAL_CATALOG.md), SIG-002 and threshold-governance sections
- [SIG-002 specification](../../signals/SIG-002.md)
- [SIG-002 gap analysis](../../signals/SIG-002_GAP_ANALYSIS.md)
- [SIG-002 Research Protocol](../../research/SIG-002_RESEARCH_PROTOCOL.md)
- ADR-006: deterministic analytics and signal evaluation boundary
- ADR-007: Signal Catalog governance
- ADR-010: acquisition provenance and subscriber-relative qualification
- ADR-011: policy-free subscriber-relative evidence
- ADR-012 through ADR-020: governed research, dataset, and eligibility contracts
- ADR-021: release governance separated from autonomous runtime evaluation
- ADR-022: ground-truth label artifacts and canonical integrity

## Implementation blockers and dependencies

This Draft does not close `GAP-002-01`, `GAP-002-02`, `GAP-002-03P`, `GAP-002-07`, or
`GAP-002-08`. Architecture must not begin `GAP-002-03A` or `GAP-002-04` until their upstream
Product decisions are Approved. SIG-002 must remain Blocked and not Implementable Now.

## Approval record

No Product approval or required-review disposition is recorded. Status remains Draft.

## Change history

| Version | Date | Change | Approval reference |
|---|---|---|---|
| 1 | 2026-07-22 | Initial Draft recording unresolved SIG-002 Product decisions | None |
