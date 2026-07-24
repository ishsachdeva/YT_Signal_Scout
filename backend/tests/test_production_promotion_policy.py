"""Tests for declarative production threshold promotion policy contracts."""

from __future__ import annotations

from unittest import TestCase

from pydantic import ValidationError

from app.services.backtesting import (
    ApprovedProductPolicyRequirement,
    ApprovedStudyRequirement,
    BacktestStudyStatus,
    MethodologyVersionRequirement,
    ProductionPromotionPolicy,
    ReleaseGovernanceReviewsRequirement,
)


def _requirements():
    return (
        ApprovedStudyRequirement(
            requirement_id="approved-study",
            kind="approved_study",
            required_status=BacktestStudyStatus.APPROVED,
        ),
        MethodologyVersionRequirement(
            requirement_id="methodology-version",
            kind="methodology_version",
            methodology_id="median-vsr-evaluation-v1",
            methodology_version=1,
        ),
        ApprovedProductPolicyRequirement(
            requirement_id="approved-product-policy",
            kind="approved_product_policy",
            decision_id="PDR-001",
            decision_version=1,
            effective_release="v1.0.0",
        ),
        ReleaseGovernanceReviewsRequirement(
            requirement_id="release-governance-reviews",
            kind="release_governance_reviews",
            required_reviewers=(
                "analytics_owner",
                "architecture_owner",
            ),
        ),
    )


def _policy() -> ProductionPromotionPolicy:
    return ProductionPromotionPolicy(
        policy_id="production-promotion-v1",
        version=1,
        requirements=_requirements(),
    )


class ProductionPromotionPolicyTests(TestCase):
    def test_complete_release_governance_policy_preserves_supplied_order(self) -> None:
        requirements = tuple(reversed(_requirements()))

        policy = ProductionPromotionPolicy(
            policy_id="production-promotion-v1",
            version=1,
            requirements=requirements,
        )

        self.assertEqual(policy.requirements, requirements)

    def test_policy_is_immutable_serializable_and_deterministic(self) -> None:
        first = _policy()
        second = _policy()

        self.assertEqual(first, second)
        self.assertEqual(
            ProductionPromotionPolicy.model_validate_json(first.model_dump_json()),
            first,
        )
        with self.assertRaises(ValidationError):
            first.version = 2

    def test_policy_represents_requirements_without_threshold_or_decision(self) -> None:
        values = _policy().model_dump()

        self.assertEqual(len(values["requirements"]), 4)
        self.assertNotIn("threshold", values)
        self.assertNotIn("decision", values)
        self.assertNotIn("eligible", values)

    def test_duplicate_requirement_ids_are_rejected(self) -> None:
        requirements = _requirements()
        duplicate = requirements[1].model_copy(
            update={"requirement_id": requirements[0].requirement_id}
        )

        with self.assertRaisesRegex(ValidationError, "IDs must be unique"):
            ProductionPromotionPolicy(
                policy_id="production-promotion-v1",
                version=1,
                requirements=(requirements[0], duplicate),
            )

    def test_duplicate_requirement_kinds_are_rejected(self) -> None:
        first = ApprovedProductPolicyRequirement(
            requirement_id="product-policy-one",
            kind="approved_product_policy",
            decision_id="PDR-001",
            decision_version=1,
            effective_release="v1.0.0",
        )
        second = ApprovedProductPolicyRequirement(
            requirement_id="product-policy-two",
            kind="approved_product_policy",
            decision_id="PDR-002",
            decision_version=1,
            effective_release="v1.0.0",
        )

        with self.assertRaisesRegex(ValidationError, "kinds must be unique"):
            ProductionPromotionPolicy(
                policy_id="production-promotion-v1",
                version=1,
                requirements=(first, second),
            )

    def test_boundary_validation_rejects_nonapproved_study_and_invalid_release_governance(self) -> None:
        invalid_study = _requirements()[0].model_dump()
        invalid_study["required_status"] = BacktestStudyStatus.EXECUTED
        with self.assertRaises(ValidationError):
            ApprovedStudyRequirement.model_validate(invalid_study)

        invalid_reviews = _requirements()[-1].model_dump()
        invalid_reviews["required_reviewers"] = ("analytics_owner",)
        with self.assertRaises(ValidationError):
            ReleaseGovernanceReviewsRequirement.model_validate(invalid_reviews)

    def test_omitting_each_required_kind_is_rejected(self) -> None:
        requirements = _requirements()
        for omitted in requirements:
            with self.subTest(kind=omitted.kind):
                incomplete = tuple(
                    requirement
                    for requirement in requirements
                    if requirement.kind != omitted.kind
                )
                with self.assertRaisesRegex(ValidationError, "exactly one of each"):
                    ProductionPromotionPolicy(
                        policy_id="production-promotion-v1",
                        version=1,
                        requirements=incomplete,
                    )

    def test_typed_validation_rejects_empty_invalid_and_unknown_policy(self) -> None:
        with self.assertRaises(ValidationError):
            ProductionPromotionPolicy(
                policy_id="production-promotion-v1",
                version=1,
                requirements=(),
            )
        with self.assertRaises(ValidationError):
            ApprovedProductPolicyRequirement(
                requirement_id="approved-product-policy",
                kind="approved_product_policy",
                decision_id="PDR-001",
                decision_version=0,
                effective_release="v1.0.0",
            )

        values = _policy().model_dump()
        values["published_threshold"] = 1.5
        with self.assertRaises(ValidationError):
            ProductionPromotionPolicy.model_validate(values)

    def test_product_policy_requires_pdr_identity_and_semantic_release(self) -> None:
        values = _requirements()[2].model_dump()
        for field, value in (("decision_id", "pdr-001"), ("effective_release", "main")):
            with self.subTest(field=field):
                invalid = {**values, field: value}
                with self.assertRaises(ValidationError):
                    ApprovedProductPolicyRequirement.model_validate(invalid)

    def test_legacy_manual_and_human_evaluation_requirements_are_rejected(self) -> None:
        for kind in (
            "manual_approval",
            "minimum_evaluations",
            "evaluation_completion",
            "research_recommendation",
        ):
            with self.subTest(kind=kind):
                values = _policy().model_dump()
                requirements = list(values["requirements"])
                requirements[0] = {
                    "requirement_id": "legacy-requirement",
                    "kind": kind,
                }
                values["requirements"] = requirements
                with self.assertRaises(ValidationError):
                    ProductionPromotionPolicy.model_validate(values)
