# Production Signal Specifications

This directory contains the long-lived product-behavior specification for each prospective YT
Signal Scout production signal. Specifications define what a signal means and what must be approved
before implementation. They do not authorize runtime composition by themselves.

## Governance

The [Signal Catalog](../product/SIGNAL_CATALOG.md) remains the authoritative approval registry and
identity inventory. A specification in this directory elaborates one catalog entry. If the two
documents disagree, implementation stops until Product, Analytics, and Architecture reconcile and
version the governing documents.

A production rule may be implemented only when:

1. its specification has no blocking product or architecture decisions;
2. Product and Analytics approve its observable behavior;
3. Architecture approves any required contract evolution;
4. the matching catalog entry is Approved and Implementable Now; and
5. identities, threshold provenance, comparator, equality behavior, qualification, evidence,
   limitations, and rule version are explicit.

Approval is recorded through version-controlled changes to the specification and Signal Catalog.
No separate production-promotion or manual-approval artifact is required.

Specifications use `PENDING PRODUCT DECISION` for unresolved business behavior. That marker is a
hard implementation blocker, never a default or invitation for engineering inference.

## Structure

- [`SIGNAL_SPEC_TEMPLATE.md`](SIGNAL_SPEC_TEMPLATE.md) is copied for every new signal.
- [`SIG-002.md`](SIG-002.md) specifies high median subscriber-relative reach.
- [`SIG-002_GAP_ANALYSIS.md`](SIG-002_GAP_ANALYSIS.md) is the implementation-blocker backlog.

Future specifications use stable catalog identifiers and filenames such as `SIG-001.md` and
`SIG-003.md`. Adding signals requires new specification files, not changes to the framework.

## Status vocabulary

- **Draft:** incomplete specification; implementation prohibited.
- **Blocked:** structurally complete enough to expose unresolved decisions; implementation
  prohibited.
- **Approved:** Product, Analytics, and Architecture approvals are recorded and catalog-aligned.
- **Implementable Now:** approved with all required runtime contracts available.
- **Deprecated:** unavailable for new production emission; historical meaning remains reserved.

Approval and implementation readiness are separate. Research approval, eligibility, or a catalog
proposal does not constitute production authorization; the completed specification and matching
Approved and Implementable Now catalog disposition do.
