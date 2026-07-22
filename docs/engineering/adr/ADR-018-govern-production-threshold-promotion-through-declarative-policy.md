# ADR-018: Govern Production Threshold Promotion Through Declarative Policy

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision adds a boundary after ADR-015 through ADR-017 without authorizing promotion.

---

# 1. Decision Summary

Represent prerequisites for possible production threshold promotion as an immutable, versioned
`ProductionPromotionPolicy` containing unique typed requirements. The policy defines what a future
eligibility assessment must require but performs no assessment, decision, publication, registry
write, runtime lookup, or signal activation.

# 2. Context

The repository now represents governed studies, methodologies, and human evaluations. Research
approval and recommendation deliberately have no production authority. Without a separate policy
boundary, future code could mistakenly treat either as sufficient to publish a threshold.

# 3. Alternatives Considered

## Treat approved study status as production authorization

Rejected because ADR-015 explicitly limits approval to the research artifact.

## Add eligibility or promotion behavior now

Rejected because this milestone authorizes policy representation only. No threshold, publisher,
registry, runtime consumer, or production approval exists.

## Declarative typed prerequisites

Selected. Closed requirement contracts make policy explicit and versionable without performing
promotion or duplicating study, evaluation, methodology, or recommendation artifacts.

# 4. Policy Contract

`ProductionPromotionPolicy` has a stable ID, positive version, and ordered non-empty requirement
tuple. Every valid policy contains exactly one requirement of each supported kind, and requirement
IDs and kinds are unique. Supported requirement kinds declare:

- approved research study status;
- exact methodology identity and version;
- positive minimum governed evaluation count;
- qualitative required/optional criterion completion rules;
- permitted existing `ResearchRecommendation` values; and
- mandatory separate manual production approval.

The approved-study requirement accepts only `BacktestStudyStatus.APPROVED`. Manual approval is
always required, and the contract cannot represent it as optional.
Supplied requirement order is preserved; validation does not sort requirements or insert defaults.

# 5. Boundary

The policy contains no threshold value, candidate selection, score, ranking, eligibility result,
promotion decision, approval record, publication state, or runtime identity. It does not inspect
evaluations or mutate study status. It cannot publish policy to the Signal Catalog or unblock
SIG-002.

# 6. Determinism and Validation

Contracts are frozen and serializable. Supplied requirement order is preserved. Duplicate IDs,
duplicate kinds, empty requirements, non-positive versions/counts, unsupported discriminators,
non-approved study statuses, non-manual approval, and invented recommendation values are rejected.

# 7. Consequences

Production eligibility prerequisites become explicit without conflating research governance with
production authorization. The separate union of requirement types adds several small contracts,
but avoids optional-field ambiguity and keeps each prerequisite structurally typed.

# 8. Implementation Impact

Adds immutable policy contracts, package exports, focused tests, and architecture documentation.
No service, dependency, database, API, CLI, registry, signal, or runtime behavior changes.

# 9. Future Revisit Criteria

Revisit only when Product authorizes an eligibility assessment contract, manual production approval
artifact, or governed threshold publication boundary. Each remains a separate decision.

# 10. Related ADRs

ADR-006, ADR-007, ADR-012, ADR-015, ADR-016, and ADR-017.
