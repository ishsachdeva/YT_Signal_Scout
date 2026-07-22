# Decision Governance

**Status:** Active

**Version:** 1.0

**Effective date:** 2026-07-22

**Accountable owner:** Repository Governance Owner

## 1. Purpose

This document is the authoritative repository-wide governance model for durable decisions. It
defines accountability, required review, approval, lifecycle, blocking, and traceability. It does
not make product, analytics, architecture, or implementation decisions.

## 2. Scope

This governance applies to product specifications, the Signal Catalog, signal specifications,
analytics definitions, ADRs, implementation, and release-readiness decisions. Existing accepted
documents retain their subject authority: Product owns product behavior, Analytics owns factual
methodology, accepted ADRs own architecture, and implementation must conform to all three.

If documents conflict, implementation stops. The accountable owner of the disputed decision
category must resolve the conflict in that category's governing record; reviewers cannot resolve
it by changing another category's document.

## 3. Roles

Roles are accountabilities, not necessarily distinct people. A decision has exactly one
accountable owner even when one person performs several roles.

| Role | Accountability |
|---|---|
| Product Owner | User-visible behavior, business policy, and Product Decision Records |
| Analytics Owner | Metric definitions, mathematical semantics, analytical validity, and research interpretation boundaries |
| Architecture Owner | System boundaries, typed contracts, compatibility, dependency direction, and ADRs |
| Engineering Owner | Implementation choices within approved Product, Analytics, and Architecture constraints |
| Repository Governance Owner | Decision process, approval authority assignments, record lifecycle, and governance amendments |

Reviewers advise and verify within their expertise. Review does not transfer accountability or
permit a reviewer to approve the decision on the owner's behalf.

## 4. Decision categories and authority

| Category | Accountable owner | Required reviewers | Governing record |
|---|---|---|---|
| Product | Product Owner | Analytics Owner when metrics, thresholds, samples, or statistical claims are involved; Architecture Owner when contracts or runtime boundaries are affected | Product specification, approved Signal Catalog entry, signal specification, or Product Decision Record |
| Analytics | Analytics Owner | Product Owner when interpretation affects user-visible meaning; Architecture Owner when a public contract or execution boundary is affected | Approved analytics documentation or a referenced Product Decision Record; ADR when architecture also changes |
| Architecture | Architecture Owner | Product Owner when behavior or product contracts are affected; Analytics Owner when factual semantics or analytical inputs are affected; Engineering Owner for implementability | Accepted ADR |
| Engineering | Engineering Owner | Architecture Owner for conformance; Product or Analytics Owner when verification exposes ambiguity in their approved decision | Source, tests, and implementation documentation linked to governing decisions |
| Governance | Repository Governance Owner | Every role whose authority or workflow would change | A versioned amendment to this document |

Required reviewers must record a disposition of approved or changes requested. A decision cannot
advance to Approved while any required review is absent or records changes requested. Consensus
does not replace the accountable owner's approval.

## 5. Signal approval authority

Signal lifecycle terms have distinct accountability:

- The Product Owner approves the signal's observable behavior and changes its Signal Catalog
  lifecycle status to **Approved** after all required reviews are complete.
- The Analytics Owner approves the validity of referenced metrics, units, inputs, analytical
  claims, and threshold-support evidence; this is required review, not ownership of product policy.
- The Architecture Owner approves required contract evolution through an ADR and is accountable
  for changing catalog readiness to **Implementable Now** only after every required runtime
  contract exists and the approved specification is implementable without inference.
- The Engineering Owner may implement or compose a production rule only when the catalog entry is
  both Approved and Implementable Now and every referenced decision is approved.

Approved means product policy is authorized. Implementable Now means architecture and inputs are
ready. Neither status means the rule has been implemented, composed, released, or verified.

## 6. Decision lifecycle

```text
Draft
  |
  v
Review
  |
  v
Approved
  |
  v
Implemented
  |
  v
Verified
  |
  v
Archived (when no longer current)
```

- **Draft:** The accountable owner records the question, proposal, and consequences. Drafts have
  no implementation authority.
- **Review:** Every required reviewer records a disposition. Open requested changes block
  approval.
- **Approved:** The accountable owner records approval after required reviews. Only approved
  decisions may govern implementation.
- **Implemented:** Engineering links the implementation and tests to the approved record. This
  state does not prove correctness.
- **Verified:** The accountable owner or an explicitly named verifier confirms implementation
  conformity and required quality gates.
- **Archived:** A superseding or retirement record identifies why the decision is no longer
  current. Historical records remain available and are not rewritten.

Rejected proposals remain recorded as rejected or are archived with their rationale. Material
semantic changes create a new version or superseding record rather than silently editing approved
history.

## 7. Decision traceability

Every durable decision uses a stable decision reference.

- Product specifications and Signal Catalog entries cite applicable Product Decision Records.
- Signal specifications cite their catalog entry, Product Decision Records, analytics definitions,
  and ADRs.
- Analytics documentation cites the product question it supports and any ADR governing its
  contract or execution boundary.
- ADRs cite the Product and Analytics decisions that constrain the architecture.
- Implementation and tests cite or name the governing specification identity, rule or policy
  version, and ADR where repository conventions permit.
- Release documentation cites the implemented and verified decision versions.

References do not transfer authority. If a downstream document contradicts an upstream approved
decision, the downstream work stops until the accountable owner resolves the conflict.

## 8. Blocking rules

Implementation must stop when:

- required behavior is missing, Draft, in Review, rejected, or marked pending;
- a required reviewer has not approved or has requested changes;
- governing documents conflict;
- an accepted ADR does not support the required contract or boundary;
- a signal is not both Approved and Implementable Now in the Signal Catalog;
- implementation would require guessing a value, operator, boundary, unit, provenance, identity,
  failure behavior, or version.

Architecture must stop when Product has not approved the behavior or factual evidence meaning that
the architecture would represent. Product must obtain Analytics review for metric definitions,
threshold evidence, units, samples, statistical validity, or analytical claims. Analytics must
stop before converting research findings into product policy. Engineering must not use code or
configuration to originate a missing decision.

Markers are category-specific:

- `PENDING PRODUCT DECISION` blocks Product behavior and every dependent decision.
- `PENDING ANALYTICS DECISION` blocks factual or methodological definition and its dependents.
- `PENDING ARCHITECTURE DECISION` blocks contract or boundary implementation after upstream
  Product and Analytics decisions are complete.
- `PENDING GOVERNANCE DECISION` blocks approval or lifecycle action whose authority is unresolved.

## 9. Product Decision Record metadata

Every Product Decision Record must include:

- stable decision ID and title;
- status and version;
- accountable Product Owner;
- decision date and effective date;
- exact question and scope;
- decision and rationale;
- alternatives considered;
- affected specifications, catalog entries, rule or policy versions, and releases;
- factual inputs, units, boundaries, missing-data behavior, and evidence provenance where relevant;
- required reviewers and each review disposition with date;
- validation or research references;
- implementation blockers and dependencies;
- superseded decision references, if any;
- approval record and change history.

A Product Decision Record is required when durable product behavior is unresolved across existing
documents, when a policy choice changes observable behavior, or when the Signal Catalog cannot
record sufficient rationale and review traceability by itself. Document presence, research
recommendation, or implementation does not imply approval.

## 10. Changes to this governance

Only the Repository Governance Owner may approve a change to decision categories, accountable
roles, approval authority, required-review rules, or lifecycle semantics. Every affected role is a
required reviewer. Governance changes are versioned, record their rationale, and never silently
reassign ownership of an already approved decision.
