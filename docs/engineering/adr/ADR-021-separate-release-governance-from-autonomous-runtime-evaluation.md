# ADR-021: Separate Release Governance from Autonomous Runtime Evaluation

**Status:** Accepted

**Date:** 2026-07-24

**Owner:** Product & Architecture

## Supersedes and amends

- Supersedes ADR-018's mandatory human-evaluation and manual-production-approval prerequisites.
- Supersedes ADR-019's rule that manual approval is unsatisfiable and every eligibility assessment
  must therefore remain ineligible.
- Amends ADR-016's research recommendation names to remove ambiguous human-review terminology.
- Preserves ADR-015 through ADR-017 as research-governance history and optional evidence artifacts.

---

# 1. Decision Summary

Production policy adoption is one-time, versioned repository and release governance. Immutable
evidence is generated, Product approves a versioned policy decision after required Analytics and
Architecture review, Engineering implements that approved policy, and the implementation is
released. After release, runtime signal evaluation is deterministic and autonomous. No user,
analyst, reviewer, administrator, or Product Owner authorizes an individual runtime signal,
dataset, threshold evaluation, execution, or emission.

# 2. Context

ADR-018 required human evaluation count/completion, a research recommendation, and mandatory
manual production approval for every promotion policy. ADR-019 then prohibited satisfying the
manual requirement without a future approval artifact, forcing all valid assessments to remain
ineligible. Although these contracts were offline, their structure incorrectly implied recurring
human authorization as part of the path to production and made eligibility impossible.

Product direction requires autonomous operation after an approved policy and implementation are
released. Development-time accountability remains necessary, but it must not become an operational
review queue or per-execution approval mechanism.

# 3. Development-Time Governance

The Product Owner may make one versioned Product Decision Record after reviewing governed evidence.
The decision may approve a threshold, comparator, equality behavior, evidence requirements, rule
version, and effective release. Required Analytics and Architecture review dispositions are
recorded before Product approval under Decision Governance.

Research labels, study reviews, and `BacktestStudyEvaluation` artifacts may inform that decision.
They remain research evidence and interpretation. No particular count, completion state, or
research recommendation is a universal structural prerequisite for Product policy adoption.

# 4. Promotion Policy Contract

`ProductionPromotionPolicy` is a release-governance contract, not a runtime policy lookup. Every
valid version contains exactly one of these typed requirements:

- approved research study status;
- exact evaluation-methodology identity and version;
- approved Product Decision Record identity/version and effective semantic release; and
- recorded Analytics Owner and Architecture Owner release-governance reviews.

`ManualApprovalRequirement`, `MinimumEvaluationsRequirement`,
`EvaluationCompletionRequirement`, and `ResearchRecommendationRequirement` are removed from the
promotion union and public exports. Human evaluations remain available through ADR-017 but are not
production prerequisites.

# 5. Eligibility Assessment

`ProductionEligibilityAssessment` remains an immutable release-governance snapshot. Its ordered
results may all be satisfied, in which case `eligible=true` is structurally valid. It does not
approve Product policy, implement code, publish configuration, deploy a release, or authorize any
runtime invocation.

Eligibility means only that supplied release-governance facts satisfy the declared policy. An
approved PDR and reviews must exist independently; a caller cannot originate those decisions by
setting an assessment result to true.

# 6. Autonomous Runtime Boundary

After an approved Product policy and conforming implementation are released:

- runtime evaluates immutable inputs against released deterministic policy;
- equal inputs and policy versions produce equal outcomes;
- no human approval, review queue, acknowledgement, or per-execution authorization is consulted;
- no research label or study review is loaded as runtime authorization; and
- changing behavior requires a new governed policy/rule version and release, not an operational
  override masquerading as approval.

Policy kill switches and operational safety controls may disable functionality as already
governed; they do not approve individual positive results.

# 7. Research Terminology

Research recommendation vocabulary changes as follows:

- `candidate_worth_reviewing` becomes `candidate_for_product_consideration`;
- `ready_for_human_review` becomes `ready_for_product_decision`.

These remain research-only dispositions with no production authority. Human labels and qualitative
evaluations remain permissible ground truth and interpretation artifacts.

# 8. Compatibility and Migration

This is a breaking change to offline serialized research-governance contracts:

- promotion policies using the four removed requirement kinds no longer validate;
- eligibility results using those kinds no longer validate; and
- artifacts using the two renamed recommendation values require a new methodology/evaluation
  version with the replacement values.

No persisted policy, eligibility assessment, methodology, evaluation, dataset, or production
threshold exists, so no repository data migration is required. Historical ADR text remains
available. Future artifacts must use the corrected contracts and increment their own versions.

# 9. Consequences

Release governance now represents the approved Product decision and required expert review without
creating runtime human authorization. Eligibility is no longer structurally impossible. Research
review remains auditable but optional as a production prerequisite. No threshold is approved and
SIG-002 remains blocked.

# 10. Implementation Impact

Updates promotion and eligibility models, research recommendation values, exports, tests,
architecture documentation, and research-governance navigation. It adds no production rule,
runtime service, API, persistence, dataset, study execution, or threshold.

# 11. Related Decisions

Decision Governance, PDR-001, ADR-007, ADR-015 through ADR-020, and the SIG-002 Research Protocol.
