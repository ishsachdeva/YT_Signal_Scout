"""Tests for immutable human threshold-study evaluation artifacts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest import TestCase

from pydantic import ValidationError

from app.services.backtesting import (
    BacktestStudyArtifact,
    BacktestStudyEvaluation,
    BacktestStudyStatus,
    CriterionObservation,
    CriterionObservationStatus,
    ResearchRecommendation,
    ThresholdEvaluationMetric,
)
from tests.test_backtest_study_models import _definition, _execution
from tests.test_threshold_evaluation_methodology import _methodology

_EVALUATED_AT = datetime(2026, 7, 22, 14, tzinfo=UTC)


def _study() -> BacktestStudyArtifact:
    return BacktestStudyArtifact(
        artifact_version=1,
        status=BacktestStudyStatus.EXECUTED,
        definition=_definition(),
        execution=_execution(),
    )


def _observations() -> tuple[CriterionObservation, ...]:
    return (
        CriterionObservation(
            criterion_id="coverage",
            metric=ThresholdEvaluationMetric.QUALIFICATION_COVERAGE,
            status=CriterionObservationStatus.REVIEWED,
            notes="Qualification coverage was inspected in the report.",
        ),
        CriterionObservation(
            criterion_id="candidate-hit-rate",
            metric=ThresholdEvaluationMetric.CANDIDATE_HIT_RATE,
            status=CriterionObservationStatus.NEEDS_CLARIFICATION,
            notes="Human clarification is required before another review.",
        ),
    )


def _evaluation() -> BacktestStudyEvaluation:
    return BacktestStudyEvaluation(
        evaluation_id="evaluation-1",
        version=1,
        evaluated_at=_EVALUATED_AT,
        reviewer="analytics-reviewer",
        study=_study(),
        methodology=_methodology(),
        observations=_observations(),
        recommendation=ResearchRecommendation.FURTHER_INVESTIGATION,
    )


class BacktestStudyEvaluationTests(TestCase):
    def test_evaluation_binds_one_study_methodology_reviewer_and_recommendation(self) -> None:
        evaluation = _evaluation()

        self.assertEqual(evaluation.study.definition.study_id, "median-vsr-study-v1")
        self.assertEqual(
            evaluation.methodology.methodology_id, "median-vsr-evaluation-v1"
        )
        self.assertEqual(evaluation.reviewer, "analytics-reviewer")
        self.assertEqual(
            evaluation.recommendation,
            ResearchRecommendation.FURTHER_INVESTIGATION,
        )

    def test_evaluation_is_immutable_serializable_and_deterministic(self) -> None:
        first = _evaluation()
        second = _evaluation()

        self.assertEqual(first, second)
        self.assertEqual(
            BacktestStudyEvaluation.model_validate_json(first.model_dump_json()), first
        )
        with self.assertRaises(ValidationError):
            first.reviewer = "another-reviewer"

    def test_observations_must_match_methodology_identity_metric_and_order(self) -> None:
        observations = _observations()
        invalid = (
            observations[:1],
            tuple(reversed(observations)),
            (
                observations[0].model_copy(update={"criterion_id": "different"}),
                observations[1],
            ),
            (
                observations[0].model_copy(
                    update={"metric": ThresholdEvaluationMetric.EXCLUSION_PROFILE}
                ),
                observations[1],
            ),
        )
        for values in invalid:
            with self.subTest(observations=values):
                with self.assertRaisesRegex(ValidationError, "match methodology"):
                    BacktestStudyEvaluation(
                        **{
                            **_evaluation().model_dump(),
                            "observations": values,
                        }
                    )

    def test_duplicate_criterion_observation_is_rejected(self) -> None:
        duplicate = (_observations()[0], _observations()[0])

        with self.assertRaisesRegex(ValidationError, "match methodology"):
            BacktestStudyEvaluation(
                **{
                    **_evaluation().model_dump(),
                    "observations": duplicate,
                }
            )

    def test_required_criterion_cannot_be_not_reviewed(self) -> None:
        observations = (
            _observations()[0].model_copy(
                update={"status": CriterionObservationStatus.NOT_REVIEWED}
            ),
            _observations()[1],
        )

        with self.assertRaisesRegex(ValidationError, "required criteria"):
            BacktestStudyEvaluation(
                **{
                    **_evaluation().model_dump(),
                    "observations": observations,
                }
            )

    def test_required_criterion_may_need_clarification(self) -> None:
        evaluation = _evaluation()

        self.assertEqual(
            evaluation.observations[1].status,
            CriterionObservationStatus.NEEDS_CLARIFICATION,
        )

    def test_optional_criterion_may_be_not_reviewed(self) -> None:
        methodology = _methodology()
        optional_criterion = methodology.criteria[1].model_copy(
            update={"required": False}
        )
        methodology = methodology.model_copy(
            update={
                "criteria": (methodology.criteria[0], optional_criterion),
            }
        )
        observations = (
            _observations()[0],
            _observations()[1].model_copy(
                update={"status": CriterionObservationStatus.NOT_REVIEWED}
            ),
        )

        evaluation = BacktestStudyEvaluation(
            **{
                **_evaluation().model_dump(),
                "methodology": methodology,
                "observations": observations,
            }
        )

        self.assertEqual(
            evaluation.observations[1].status,
            CriterionObservationStatus.NOT_REVIEWED,
        )

    def test_study_must_be_executed_and_evaluation_cannot_precede_execution(self) -> None:
        draft = BacktestStudyArtifact(
            artifact_version=1,
            status=BacktestStudyStatus.DRAFT,
            definition=_definition(),
        )
        with self.assertRaisesRegex(ValidationError, "executed study"):
            BacktestStudyEvaluation(
                **{**_evaluation().model_dump(), "study": draft}
            )

        executed_at = _study().execution.metadata.executed_at
        with self.assertRaisesRegex(ValidationError, "precede study execution"):
            BacktestStudyEvaluation(
                **{
                    **_evaluation().model_dump(),
                    "evaluated_at": executed_at - timedelta(seconds=1),
                }
            )

    def test_recommendation_must_be_permitted_by_methodology(self) -> None:
        methodology = _methodology().model_copy(
            update={
                "permitted_recommendations": (
                    ResearchRecommendation.INSUFFICIENT_EVIDENCE,
                )
            }
        )

        with self.assertRaisesRegex(ValidationError, "not permitted"):
            BacktestStudyEvaluation(
                **{
                    **_evaluation().model_dump(),
                    "methodology": methodology,
                }
            )

    def test_typed_validation_rejects_unknown_status_fields_and_naive_time(self) -> None:
        observation = _observations()[0].model_dump()
        observation["status"] = "scored"
        with self.assertRaises(ValidationError):
            CriterionObservation.model_validate(observation)

        values = _evaluation().model_dump()
        values["score"] = 0.9
        with self.assertRaises(ValidationError):
            BacktestStudyEvaluation.model_validate(values)

        values = _evaluation().model_dump()
        values["evaluated_at"] = datetime(2026, 7, 22)
        with self.assertRaisesRegex(ValidationError, "timezone-aware"):
            BacktestStudyEvaluation.model_validate(values)
