# SIG-002 Implementation Gap Analysis

This backlog lists every known blocker preventing implementation of SIG-002. Resolving a row
requires updating the authoritative Signal Catalog and SIG-002 specification where applicable.
Engineering must not infer missing policy from research results or proposed catalog language.

| ID | Description | Owner | Impact | Suggested resolution | Priority |
|---|---|---|---|---|---|
| GAP-002-01 | Production threshold `T` is undefined. | Product + Analytics | No deterministic emission condition exists. | Review governed study artifacts and validation evidence; approve one threshold with provenance and rule-version impact. | P0 |
| GAP-002-02 | Comparator and equality behavior are proposed as `>=` but not approved. | Product + Analytics | Boundary results cannot be implemented or tested. | Approve `>` or `>=` and explicitly record equality behavior and adjacent examples. | P0 |
| GAP-002-03 | Current emitted `SignalEvidence` cannot carry threshold, comparator, unit, sample size, eligibility basis, or subscriber-relative provenance. | Architecture | A conforming signal would be under-explained and non-reproducible. | Approve the smallest typed SIG-002 evidence extension; prohibit generic JSON. | P0 |
| GAP-002-04 | Existing `SignalRule` consumes `CalculatedChannelAnalytics`, which does not contain subscriber-relative qualification or median standard-video VSR. | Architecture | A rule would either lack inputs or bypass qualification. | Approve a qualified subscriber-relative rule boundary or a compatible separate protocol/composition path without weakening ADR-006/ADR-010. | P0 |
| GAP-002-05 | Signal Catalog entry is Blocked and no production rule is Approved or Implementable Now. | Product + Analytics + Architecture | ADR-007 prohibits implementation and composition. | Record approvals, decision evidence, limitations, exact identities, and status change in the catalog after all P0 gaps close. | P0 |
| GAP-002-07 | Trigger and non-trigger numeric examples cannot be finalized before threshold and equality approval. | Product + Analytics | Boundary tests cannot be authoritative. | Add exact below/equal/above examples using full precision after GAP-002-01 and GAP-002-02. | P1 |
| GAP-002-08 | Final coexistence policy with SIG-001/SIG-003 is not production-approved. | Product | Multi-signal behavior remains underspecified, though it does not block isolated zero-or-one rule design. | Approve coexistence before composing multiple production rules; keep the first rule isolated. | P2 |

## Exit criteria

SIG-002 becomes implementation-ready only when:

- every P0 gap is resolved with recorded approval evidence;
- `SIG-002.md` contains no blocking `PENDING PRODUCT DECISION` marker;
- the Signal Catalog marks SIG-002 Approved and Implementable Now;
- exact boundary examples and required evidence are complete;
- implementation can reuse qualification and analytics without recomputation.

Research findings or human recommendations alone do not close these gaps.
