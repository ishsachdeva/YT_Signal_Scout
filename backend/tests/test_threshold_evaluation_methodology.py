"""Tests for immutable threshold evaluation methodology contracts."""

from __future__ import annotations

from unittest import TestCase

from pydantic import ValidationError

from app.services.backtesting import (
    ResearchRecommendation,
    ThresholdEvaluationCriterion,
    ThresholdEvaluationMethodology,
    ThresholdEvaluationMetric,
)


def _criterion(
    criterion_id: str = "coverage",
    metric: ThresholdEvaluationMetric = (
        ThresholdEvaluationMetric.QUALIFICATION_COVERAGE
    ),
) -> ThresholdEvaluationCriterion:
    return ThresholdEvaluationCriterion(
        criterion_id=criterion_id,
        metric=metric,
        description="Inspect the factual report value without scoring candidates.",
        required=True,
    )


def _methodology() -> ThresholdEvaluationMethodology:
    return ThresholdEvaluationMethodology(
        methodology_id="median-vsr-evaluation-v1",
        version=1,
        name="Median VSR threshold evaluation",
        objective="Define factual evidence that research evaluators may inspect.",
        criteria=(
            _criterion(),
            _criterion(
                "candidate-hit-rate",
                ThresholdEvaluationMetric.CANDIDATE_HIT_RATE,
            ),
        ),
        permitted_recommendations=(
            ResearchRecommendation.FURTHER_INVESTIGATION,
            ResearchRecommendation.INSUFFICIENT_EVIDENCE,
            ResearchRecommendation.CANDIDATE_FOR_PRODUCT_CONSIDERATION,
            ResearchRecommendation.READY_FOR_PRODUCT_DECISION,
        ),
    )


class ThresholdEvaluationMethodologyTests(TestCase):
    def test_methodology_is_immutable_serializable_and_deterministic(self) -> None:
        first = _methodology()
        second = _methodology()

        self.assertEqual(first, second)
        self.assertEqual(
            ThresholdEvaluationMethodology.model_validate_json(
                first.model_dump_json()
            ),
            first,
        )
        with self.assertRaises(ValidationError):
            first.version = 2

    def test_metrics_are_limited_to_existing_factual_report_concepts(self) -> None:
        self.assertEqual(
            tuple(ThresholdEvaluationMetric),
            (
                ThresholdEvaluationMetric.QUALIFICATION_COVERAGE,
                ThresholdEvaluationMetric.MEDIAN_VSR_AVAILABILITY,
                ThresholdEvaluationMetric.THRESHOLD_ELIGIBLE_SUPPORT,
                ThresholdEvaluationMetric.MEDIAN_VSR_DISTRIBUTION,
                ThresholdEvaluationMetric.CANDIDATE_HIT_RATE,
                ThresholdEvaluationMetric.EXCLUSION_PROFILE,
                ThresholdEvaluationMetric.QUALIFICATION_FAILURE_PROFILE,
            ),
        )

    def test_recommendations_are_research_only(self) -> None:
        self.assertEqual(
            tuple(ResearchRecommendation),
            (
                ResearchRecommendation.FURTHER_INVESTIGATION,
                ResearchRecommendation.INSUFFICIENT_EVIDENCE,
                ResearchRecommendation.CANDIDATE_FOR_PRODUCT_CONSIDERATION,
                ResearchRecommendation.READY_FOR_PRODUCT_DECISION,
            ),
        )
        prohibited_terms = ("production", "publish", "enable", "deploy", "release")
        for recommendation in ResearchRecommendation:
            self.assertFalse(
                any(term in recommendation.value for term in prohibited_terms)
            )

    def test_empty_methodology_is_rejected(self) -> None:
        values = _methodology().model_dump()
        values["criteria"] = ()
        with self.assertRaises(ValidationError):
            ThresholdEvaluationMethodology.model_validate(values)

        values = _methodology().model_dump()
        values["permitted_recommendations"] = ()
        with self.assertRaises(ValidationError):
            ThresholdEvaluationMethodology.model_validate(values)

    def test_duplicate_criterion_ids_metrics_and_recommendations_are_rejected(self) -> None:
        duplicate_cases = (
            {
                "criteria": (
                    _criterion(),
                    _criterion(
                        "coverage",
                        ThresholdEvaluationMetric.CANDIDATE_HIT_RATE,
                    ),
                )
            },
            {
                "criteria": (
                    _criterion(),
                    _criterion(
                        "other-coverage",
                        ThresholdEvaluationMetric.QUALIFICATION_COVERAGE,
                    ),
                )
            },
            {
                "permitted_recommendations": (
                    ResearchRecommendation.FURTHER_INVESTIGATION,
                    ResearchRecommendation.FURTHER_INVESTIGATION,
                )
            },
        )
        for updates in duplicate_cases:
            with self.subTest(updates=updates):
                values = _methodology().model_dump()
                values.update(updates)
                with self.assertRaises(ValidationError):
                    ThresholdEvaluationMethodology.model_validate(values)

    def test_unknown_metric_recommendation_and_fields_are_rejected(self) -> None:
        criterion = _criterion().model_dump()
        criterion["metric"] = "precision"
        with self.assertRaises(ValidationError):
            ThresholdEvaluationCriterion.model_validate(criterion)

        values = _methodology().model_dump()
        values["permitted_recommendations"] = ("production_approved",)
        with self.assertRaises(ValidationError):
            ThresholdEvaluationMethodology.model_validate(values)

        values = _methodology().model_dump()
        values["weights"] = {"coverage": 1.0}
        with self.assertRaises(ValidationError):
            ThresholdEvaluationMethodology.model_validate(values)
