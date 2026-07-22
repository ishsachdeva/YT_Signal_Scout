"""Tests for declarative production threshold promotion policy contracts."""

from __future__ import annotations

from unittest import TestCase

from pydantic import ValidationError

from app.services.backtesting import (
    ApprovedStudyRequirement,
    BacktestStudyStatus,
    EvaluationCompletionRequirement,
    ManualApprovalRequirement,
    MethodologyVersionRequirement,
    MinimumEvaluationsRequirement,
    ProductionPromotionPolicy,
    ResearchRecommendation,
    ResearchRecommendationRequirement,
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
        MinimumEvaluationsRequirement(
            requirement_id="minimum-evaluations",
            kind="minimum_evaluations",
            minimum_count=1,
        ),
        EvaluationCompletionRequirement(
            requirement_id="evaluation-completion",
            kind="evaluation_completion",
            allow_required_needs_clarification=False,
            require_optional_criteria_reviewed=False,
        ),
        ResearchRecommendationRequirement(
            requirement_id="research-recommendation",
            kind="research_recommendation",
            permitted_recommendations=(
                ResearchRecommendation.READY_FOR_HUMAN_REVIEW,
            ),
        ),
        ManualApprovalRequirement(
            requirement_id="manual-approval",
            kind="manual_approval",
            required=True,
        ),
    )


def _policy() -> ProductionPromotionPolicy:
    return ProductionPromotionPolicy(
        policy_id="production-promotion-v1",
        version=1,
        requirements=_requirements(),
    )


class ProductionPromotionPolicyTests(TestCase):
    def test_complete_six_kind_policy_is_valid_and_preserves_supplied_order(self) -> None:
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

        self.assertEqual(len(values["requirements"]), 6)
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
        first = MinimumEvaluationsRequirement(
            requirement_id="minimum-one",
            kind="minimum_evaluations",
            minimum_count=1,
        )
        second = MinimumEvaluationsRequirement(
            requirement_id="minimum-two",
            kind="minimum_evaluations",
            minimum_count=2,
        )

        with self.assertRaisesRegex(ValidationError, "kinds must be unique"):
            ProductionPromotionPolicy(
                policy_id="production-promotion-v1",
                version=1,
                requirements=(first, second),
            )

    def test_boundary_validation_rejects_nonapproved_study_and_optional_manual_approval(self) -> None:
        invalid_study = _requirements()[0].model_dump()
        invalid_study["required_status"] = BacktestStudyStatus.EXECUTED
        with self.assertRaises(ValidationError):
            ApprovedStudyRequirement.model_validate(invalid_study)

        invalid_approval = _requirements()[-1].model_dump()
        invalid_approval["required"] = False
        with self.assertRaises(ValidationError):
            ManualApprovalRequirement.model_validate(invalid_approval)

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
            MinimumEvaluationsRequirement(
                requirement_id="minimum-evaluations",
                kind="minimum_evaluations",
                minimum_count=0,
            )

        values = _policy().model_dump()
        values["published_threshold"] = 1.5
        with self.assertRaises(ValidationError):
            ProductionPromotionPolicy.model_validate(values)

    def test_research_recommendations_remain_the_existing_closed_enum(self) -> None:
        values = _requirements()[4].model_dump()
        values["permitted_recommendations"] = ("production_approved",)
        with self.assertRaises(ValidationError):
            ResearchRecommendationRequirement.model_validate(values)

        values = _requirements()[4].model_dump()
        values["permitted_recommendations"] = (
            ResearchRecommendation.READY_FOR_HUMAN_REVIEW,
            ResearchRecommendation.READY_FOR_HUMAN_REVIEW,
        )
        with self.assertRaisesRegex(ValidationError, "must be unique"):
            ResearchRecommendationRequirement.model_validate(values)
