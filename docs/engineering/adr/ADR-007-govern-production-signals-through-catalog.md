# ADR-007: Govern Production Signals Through a Versioned Signal Catalog

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None

---

# 1. Decision Summary

Production `SignalRule` implementations must trace to an approved, versioned entry in the
documentation-first Signal Catalog. The catalog owns business meaning, deterministic conditions,
threshold provenance, evidence requirements, limitations, and approval state. Application code
implements approved policy but does not originate it.

# 2. Context

ADR-006 separates factual analytics from signal evaluation. The first production-rule review
correctly stopped because existing metrics did not have an approved, complete business condition.
A durable policy-governance boundary is needed to prevent thresholds and semantics from emerging
implicitly inside rule classes.

# 3. Problem Statement

Where should signal meaning and approval live so Product, Analytics, and Engineering can review
policy before deterministic code is released and can reproduce historical semantics later?

# 4. Decision Drivers

- Product-policy ownership
- Traceability and explainability
- Deterministic implementation
- Threshold governance
- Historical reproducibility
- Separation of concerns
- Simplicity before automation

# 5. Goals

- Establish one discoverable source for signal definitions and readiness.
- Require explicit threshold provenance and approval.
- Keep analytics factual, rules deterministic, and AI explanatory.
- Version material semantic changes without overwriting history.
- Identify missing analytics before implementation begins.

# 6. Alternatives Considered

## Option A — Define policy directly in each SignalRule

### Pros

- Minimal documentation overhead

### Cons

- Business decisions hide in code
- Product approval and source traceability are unclear
- Threshold changes can silently alter historical meaning

Rejected.

## Option B — Documentation-first versioned catalog

### Pros

- Human-reviewable and close to current requirements
- No runtime parser or configuration risk
- Explicit readiness, limitations, approvals, and missing dependencies
- Rules remain ordinary typed code

### Cons

- Documentation and implementation require disciplined synchronization
- Approval remains a manual workflow initially

Selected.

## Option C — Machine-readable YAML/JSON catalog driving execution

### Pros

- Potential automated validation and administration

### Cons

- No immediate runtime consumer
- Premature schema and loader design
- Encourages a generic rule DSL before real rules establish requirements
- Adds validation, security, and operational complexity

Rejected for v1.

## Option D — Allow AI to select or interpret signal conditions

### Pros

- Flexible natural-language policy

### Cons

- Non-deterministic and difficult to audit
- Violates ADR-002 and ADR-006
- Cannot guarantee threshold or historical reproducibility

Rejected.

# 7. Decision

Create `docs/product/SIGNAL_CATALOG.md` as the authoritative signal-policy artifact.

Every production rule must reference exactly one approved catalog entry whose machine identities,
version, condition, boundaries, missing-data behavior, evidence, and limitations match the code.
Proposed or blocked entries must not be composed into production.

Material threshold, formula, evidence, polarity, sample, null, or interpretation changes create a
new rule version. AI and ranking remain downstream consumers and cannot originate signal state.

# 8. Decision Rationale

Documentation-first governance solves the immediate policy gap with the lowest complexity. It
makes decisions reviewable by non-code owners while retaining strongly typed Python rules as the
execution mechanism. Automation can follow only when multiple approved rules demonstrate a real
consumer and stable schema.

# 9. Related Engineering Principles

- EP-001 Build for Maintainability Before Optimization
- EP-002 Separation of Concerns
- EP-003 Single Responsibility Principle
- EP-004 Deterministic Business Logic
- EP-006 Immutable Models

# 10. Consequences

## Positive

- Product policy cannot be silently invented in code.
- Threshold provenance and open decisions are visible.
- Missing analytics are discovered before rule implementation.
- Historical rule meaning can be reproduced.
- AI and ranking boundaries remain explicit.

## Negative

- Catalog maintenance becomes part of rule delivery.
- Approval is manual until workflow needs justify automation.
- Documentation/code drift remains possible without review discipline.

## Risks

- Contributors may mistake Proposed entries for production authorization.
- Catalog entries may become verbose or duplicate requirements.
- Premature machine-readable conversion could create a de facto rule DSL.

# 11. Implementation Impact

### Affected folders

- `docs/product/`
- `docs/engineering/`

### Affected modules

- Future `SignalRule` implementations and composition
- Future analytics required by approved catalog entries
- Future AI narrative and ranking consumers

### Migration required?

No.

### Breaking changes?

No production rules exist.

# 12. Security Impact

Documentation does not execute. Rejecting runtime expressions avoids code-injection, unsafe
parsing, and untrusted configuration risks. Future automation requires an independent security
review.

# 13. Performance Impact

None. The catalog is not loaded at runtime.

# 14. Cost Impact

No infrastructure cost. Product and Analytics review adds intentional governance effort.

# 15. Operational Impact

Release review must verify catalog approval and rule-version alignment. Historical signals must
retain their original rule identity/version. No deployment component is added.

# 16. Future Revisit Criteria

Revisit documentation-only storage when multiple approved rules create a demonstrated need for
automated schema validation, catalog publication, administration, or policy-set composition.
Do not adopt runtime-driven rules without a separate ADR and security review.

# 17. References

- Product Requirements Document §§5, 8, and 9
- Technical Requirements Document scoring and reproducibility requirements
- Feature Catalogue E04 and E05
- Engineering Principles
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation
- ADR-006: Separate Deterministic Analytics from Business Signal Evaluation
- Signal Catalog v1
