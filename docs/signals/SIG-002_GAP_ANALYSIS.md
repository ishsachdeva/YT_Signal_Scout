# SIG-002 Implementation Gap Analysis

This backlog lists every known blocker preventing implementation of SIG-002. Resolving a row
requires updating the authoritative Signal Catalog and SIG-002 specification where applicable.
Engineering must not infer missing policy from research results or proposed catalog language.
Product-owned gaps are recorded without resolution in
[PDR-001](../product/decisions/PDR-001-sig-002-product-policy.md).
Future evidence offered to resolve threshold-related gaps must conform to the
[SIG-002 Research Protocol](../research/SIG-002_RESEARCH_PROTOCOL.md). Protocol conformance alone
does not resolve a gap or approve Product policy.

| ID | Description | Accountable owner | Required reviewers | Governing record | Impact | Suggested resolution | Priority |
|---|---|---|---|---|---|---|---|
| GAP-002-01 | Production threshold `T` and its provenance are undefined. | Product Owner | Analytics Owner; Architecture Owner | Product Decision Record, SIG-002 specification, and Signal Catalog | No deterministic emission condition exists. | Review governed study artifacts and validation evidence; approve one threshold with provenance and rule-version impact. | P0 |
| GAP-002-02 | Comparator and equality behavior are proposed as `>=` but not approved. | Product Owner | Analytics Owner; Architecture Owner | Product Decision Record, SIG-002 specification, and Signal Catalog | Boundary results cannot be implemented or tested. | Approve `>` or `>=` and explicitly record equality behavior and adjacent examples. | P0 |
| GAP-002-03P | Required business evidence meaning and cardinality are not approved. | Product Owner | Analytics Owner; Architecture Owner | Product Decision Record, SIG-002 specification, and Signal Catalog | Architecture cannot select a final representation without knowing what the signal must explain. | Approve the factual evidence requirements after GAP-002-01 and GAP-002-02 without designing their Python representation. | P0 |
| GAP-002-03A | Current emitted `SignalEvidence` cannot represent all proposed subscriber-relative comparison evidence. | Architecture Owner | Product Owner; Analytics Owner; Engineering Owner | Accepted ADR | A conforming signal cannot be typed until the approved evidence meaning is represented. | After GAP-002-03P, approve the smallest typed representation, provenance composition, and compatibility strategy; prohibit generic JSON. | P0 |
| GAP-002-04 | Existing `SignalRule` consumes `CalculatedChannelAnalytics`, which does not contain subscriber-relative qualification or median standard-video VSR. | Architecture Owner | Product Owner; Analytics Owner; Engineering Owner | Accepted ADR | A rule would either lack inputs or bypass qualification. | After Product evidence semantics are approved, define a qualified subscriber-relative rule boundary without weakening ADR-006 or ADR-010. | P0 |
| GAP-002-05P | Signal Catalog entry remains Blocked rather than Approved. | Product Owner | Analytics Owner; Architecture Owner | Signal Catalog approval metadata | ADR-007 prohibits implementation of unapproved product behavior. | After Product gaps and required reviews close, record the Product Owner's Approved disposition and decision references. | P0 |
| GAP-002-05A | Signal Catalog entry is not Implementable Now. | Architecture Owner | Product Owner; Analytics Owner; Engineering Owner | Signal Catalog readiness metadata | Production implementation remains prohibited while required runtime contracts are unavailable. | After Architecture gaps close, record the Architecture Owner's Implementable Now disposition and ADR references. | P0 |
| GAP-002-07 | Trigger and non-trigger numeric examples cannot be finalized before threshold and equality approval. | Product Owner | Analytics Owner | Product Decision Record and SIG-002 specification | Boundary tests cannot be authoritative. | Add exact below/equal/above examples using full precision after GAP-002-01 and GAP-002-02. | P1 |
| GAP-002-08 | Final coexistence policy with SIG-001/SIG-003 is not production-approved. | Product Owner | Architecture Owner | Signal Catalog and signal specifications | Multi-signal behavior remains underspecified, though it does not block isolated zero-or-one rule design. | Approve coexistence before composing multiple production rules; keep the first rule isolated. | P2 |

## Exit criteria

SIG-002 becomes implementation-ready only when:

- every P0 gap is resolved in dependency order under Decision Governance;
- `SIG-002.md` contains no blocking category-specific pending marker;
- the Signal Catalog marks SIG-002 Approved and Implementable Now;
- exact boundary examples and required evidence are complete;
- implementation can reuse qualification and analytics without recomputation.

Research findings or human recommendations alone do not close these gaps.
The Research Protocol defines how such evidence is produced and accepted; it does not alter the
dependency order or any accountable owner.

## P0 dependency order

`GAP-002-01` -> `GAP-002-02` -> `GAP-002-03P` -> `GAP-002-03A` -> `GAP-002-04`
-> `GAP-002-05P` -> `GAP-002-05A`.

Product evidence meaning is an upstream dependency; typed representation remains independently
accountable to Architecture. See
[Decision Governance](../governance/DECISION_GOVERNANCE.md).
