"""Tests for immutable production-promotion eligibility assessments."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest import TestCase

from pydantic import ValidationError

from app.services.backtesting import (
    EligibilityRequirementResult,
    ProductionEligibilityAssessment,
)
from tests.test_backtest_study_evaluation import _evaluation
from tests.test_production_promotion_policy import _policy

_ASSESSED_AT = datetime(2026, 7, 22, 15, tzinfo=UTC)


def _results(*, failed_ids: tuple[str, ...] = ("approved-product-policy",)):
    return tuple(
        EligibilityRequirementResult(
            requirement_id=requirement.requirement_id,
            requirement_kind=requirement.kind,
            satisfied=requirement.requirement_id not in failed_ids,
            failure_reason=(
                "The supplied governance facts did not satisfy this requirement."
                if requirement.requirement_id in failed_ids
                else None
            ),
        )
        for requirement in _policy().requirements
    )


def _assessment(
    *, failed_ids: tuple[str, ...] = ("approved-product-policy",)
) -> ProductionEligibilityAssessment:
    evaluation = _evaluation()
    return ProductionEligibilityAssessment(
        assessment_id="assessment-1",
        version=1,
        assessed_at=_ASSESSED_AT,
        policy=_policy(),
        study=evaluation.study,
        evaluations=(evaluation,),
        requirement_results=_results(failed_ids=failed_ids),
        eligible=not failed_ids,
        failed_requirement_ids=tuple(
            requirement.requirement_id
            for requirement in _policy().requirements
            if requirement.requirement_id in failed_ids
        ),
    )


class ProductionEligibilityAssessmentTests(TestCase):
    def test_current_state_assessment_is_immutable_serializable_and_deterministic(self) -> None:
        first = _assessment()
        second = _assessment()

        self.assertEqual(first, second)
        self.assertFalse(first.eligible)
        self.assertEqual(first.failed_requirement_ids, ("approved-product-policy",))
        self.assertEqual(
            ProductionEligibilityAssessment.model_validate_json(
                first.model_dump_json()
            ),
            first,
        )
        with self.assertRaises(ValidationError):
            first.eligible = False

    def test_ineligible_assessment_records_failures_in_policy_order(self) -> None:
        assessment = _assessment(
            failed_ids=("release-governance-reviews", "approved-product-policy")
        )

        self.assertFalse(assessment.eligible)
        self.assertEqual(
            assessment.failed_requirement_ids,
            ("approved-product-policy", "release-governance-reviews"),
        )

    def test_release_governance_requirements_can_produce_eligible_assessment(self) -> None:
        assessment = _assessment(failed_ids=())

        self.assertTrue(assessment.eligible)
        self.assertEqual(assessment.failed_requirement_ids, ())

    def test_results_must_match_policy_identity_kind_and_order(self) -> None:
        assessment = _assessment()
        invalid = (
            assessment.requirement_results[:-1],
            tuple(reversed(assessment.requirement_results)),
            (
                assessment.requirement_results[0].model_copy(
                    update={"requirement_id": "different"}
                ),
                *assessment.requirement_results[1:],
            ),
        )
        for results in invalid:
            with self.subTest(results=results):
                with self.assertRaisesRegex(ValidationError, "match promotion"):
                    ProductionEligibilityAssessment(
                        **{**assessment.model_dump(), "requirement_results": results}
                    )

    def test_eligible_and_failed_ids_must_match_requirement_results(self) -> None:
        assessment = _assessment()
        for updates in (
            {"eligible": True},
            {"failed_requirement_ids": ()},
            {"failed_requirement_ids": ("approved-study",)},
        ):
            with self.subTest(updates=updates):
                with self.assertRaises(ValidationError):
                    ProductionEligibilityAssessment(
                        **{**assessment.model_dump(), **updates}
                    )

    def test_requirement_failure_recording_is_structurally_consistent(self) -> None:
        with self.assertRaisesRegex(ValidationError, "cannot have"):
            EligibilityRequirementResult(
                requirement_id="approved-study",
                requirement_kind="approved_study",
                satisfied=True,
                failure_reason="Contradictory failure.",
            )
        with self.assertRaisesRegex(ValidationError, "require a failure"):
            EligibilityRequirementResult(
                requirement_id="approved-study",
                requirement_kind="approved_study",
                satisfied=False,
                failure_reason=None,
            )

    def test_evaluations_must_be_unique_and_bound_to_assessed_study(self) -> None:
        assessment = _assessment()
        duplicate = (assessment.evaluations[0], assessment.evaluations[0])
        with self.assertRaisesRegex(ValidationError, "IDs must be unique"):
            ProductionEligibilityAssessment(
                **{**assessment.model_dump(), "evaluations": duplicate}
            )

        mismatched = assessment.evaluations[0].model_copy(
            update={"study": _evaluation().study.model_copy(update={"artifact_version": 2})}
        )
        with self.assertRaisesRegex(ValidationError, "match the assessed study"):
            ProductionEligibilityAssessment(
                **{**assessment.model_dump(), "evaluations": (mismatched,)}
            )

    def test_assessment_time_and_typed_boundaries_are_validated(self) -> None:
        assessment = _assessment()
        with self.assertRaisesRegex(ValidationError, "precede an evaluation"):
            ProductionEligibilityAssessment(
                **{
                    **assessment.model_dump(),
                    "assessed_at": assessment.evaluations[0].evaluated_at
                    - timedelta(seconds=1),
                }
            )

        values = assessment.model_dump()
        values["assessed_at"] = datetime(2026, 7, 22)
        with self.assertRaisesRegex(ValidationError, "timezone-aware"):
            ProductionEligibilityAssessment.model_validate(values)

        values = assessment.model_dump()
        values["approved"] = True
        with self.assertRaises(ValidationError):
            ProductionEligibilityAssessment.model_validate(values)
