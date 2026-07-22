"""Tests for immutable governed threshold study artifacts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest import TestCase

from pydantic import ValidationError

from app.services.backtesting import (
    BacktestExecutionService,
    BacktestStudyArtifact,
    BacktestStudyDecision,
    BacktestStudyDefinition,
    BacktestStudyReview,
    BacktestStudyStatus,
)
from tests.test_backtest_execution import _configuration, _request

_CREATED_AT = datetime(2026, 7, 22, 10, tzinfo=UTC)
_REVIEWED_AT = datetime(2026, 7, 22, 13, tzinfo=UTC)


def _definition() -> BacktestStudyDefinition:
    return BacktestStudyDefinition(
        study_id="median-vsr-study-v1",
        version=1,
        title="Median VSR candidate study",
        objective="Measure factual outcomes for the configured threshold candidates.",
        created_at=_CREATED_AT,
        configuration=_configuration(),
    )


def _execution():
    return BacktestExecutionService().execute(_request())


def _review(
    decision: BacktestStudyDecision = BacktestStudyDecision.APPROVE_STUDY,
    *,
    review_id: str = "review-1",
    reviewed_at: datetime = _REVIEWED_AT,
) -> BacktestStudyReview:
    return BacktestStudyReview(
        review_id=review_id,
        study_id="median-vsr-study-v1",
        study_version=1,
        execution_id="execution-1",
        reviewed_at=reviewed_at,
        reviewer="analytics-reviewer",
        decision=decision,
        rationale="The study artifact is complete and suitable for research use.",
    )


class BacktestStudyModelTests(TestCase):
    def test_draft_study_contains_definition_only(self) -> None:
        artifact = BacktestStudyArtifact(
            artifact_version=1,
            status=BacktestStudyStatus.DRAFT,
            definition=_definition(),
        )

        self.assertIsNone(artifact.execution)
        self.assertEqual(artifact.reviews, ())

    def test_executed_study_reuses_complete_factual_report(self) -> None:
        execution = _execution()
        artifact = BacktestStudyArtifact(
            artifact_version=1,
            status=BacktestStudyStatus.EXECUTED,
            definition=_definition(),
            execution=execution,
        )

        self.assertIs(artifact.execution, execution)
        self.assertEqual(artifact.execution.report, execution.report)

    def test_approved_and_rejected_research_artifacts_are_explicit(self) -> None:
        execution = _execution()
        approved = BacktestStudyArtifact(
            artifact_version=1,
            status=BacktestStudyStatus.APPROVED,
            definition=_definition(),
            execution=execution,
            reviews=(_review(),),
        )
        rejected = BacktestStudyArtifact(
            artifact_version=1,
            status=BacktestStudyStatus.REJECTED,
            definition=_definition(),
            execution=execution,
            reviews=(_review(BacktestStudyDecision.REJECT_STUDY),),
        )

        self.assertEqual(approved.reviews[-1].decision, "approve_study")
        self.assertEqual(rejected.reviews[-1].decision, "reject_study")

    def test_archived_artifact_retains_execution_and_review_history(self) -> None:
        artifact = BacktestStudyArtifact(
            artifact_version=1,
            status=BacktestStudyStatus.ARCHIVED,
            definition=_definition(),
            execution=_execution(),
            reviews=(_review(BacktestStudyDecision.REJECT_STUDY),),
        )

        self.assertEqual(artifact.status, BacktestStudyStatus.ARCHIVED)
        self.assertEqual(len(artifact.reviews), 1)

    def test_artifact_is_immutable_serializable_and_deterministic(self) -> None:
        values = {
            "artifact_version": 1,
            "status": BacktestStudyStatus.APPROVED,
            "definition": _definition(),
            "execution": _execution(),
            "reviews": (_review(),),
        }
        first = BacktestStudyArtifact(**values)
        second = BacktestStudyArtifact(**values)

        self.assertEqual(first, second)
        self.assertEqual(
            BacktestStudyArtifact.model_validate_json(first.model_dump_json()), first
        )
        with self.assertRaises(ValidationError):
            first.status = BacktestStudyStatus.ARCHIVED

    def test_invalid_lifecycle_combinations_are_rejected(self) -> None:
        execution = _execution()
        invalid_values = (
            {
                "status": BacktestStudyStatus.DRAFT,
                "execution": execution,
                "reviews": (),
            },
            {
                "status": BacktestStudyStatus.EXECUTED,
                "execution": None,
                "reviews": (),
            },
            {
                "status": BacktestStudyStatus.EXECUTED,
                "execution": execution,
                "reviews": (_review(),),
            },
            {
                "status": BacktestStudyStatus.APPROVED,
                "execution": execution,
                "reviews": (_review(BacktestStudyDecision.REJECT_STUDY),),
            },
            {
                "status": BacktestStudyStatus.REJECTED,
                "execution": execution,
                "reviews": (_review(),),
            },
        )
        for values in invalid_values:
            with self.subTest(status=values["status"]):
                with self.assertRaises(ValidationError):
                    BacktestStudyArtifact(
                        artifact_version=1,
                        definition=_definition(),
                        **values,
                    )

    def test_reviews_require_unique_ids_deterministic_order_and_matching_identity(self) -> None:
        execution = _execution()
        cases = (
            (
                _review(reviewed_at=_REVIEWED_AT),
                _review(reviewed_at=_REVIEWED_AT - timedelta(minutes=1), review_id="review-2"),
            ),
            (_review(), _review()),
            (_review().model_copy(update={"study_id": "another-study"}),),
            (
                _review(
                    reviewed_at=_CREATED_AT - timedelta(minutes=1),
                ),
            ),
        )
        for reviews in cases:
            with self.subTest(reviews=reviews):
                with self.assertRaises(ValidationError):
                    BacktestStudyArtifact(
                        artifact_version=1,
                        status=BacktestStudyStatus.APPROVED,
                        definition=_definition(),
                        execution=execution,
                        reviews=reviews,
                    )

    def test_equal_review_timestamps_are_rejected(self) -> None:
        reviews = (
            _review(review_id="review-1"),
            _review(review_id="review-2"),
        )

        with self.assertRaisesRegex(ValidationError, "strictly increasing"):
            BacktestStudyArtifact(
                artifact_version=1,
                status=BacktestStudyStatus.APPROVED,
                definition=_definition(),
                execution=_execution(),
                reviews=reviews,
            )

    def test_definition_review_and_artifact_reject_invalid_typed_values(self) -> None:
        with self.assertRaisesRegex(ValidationError, "timezone-aware"):
            BacktestStudyDefinition(
                study_id="median-vsr-study-v1",
                version=1,
                title="Study",
                objective="Research objective",
                created_at=datetime(2026, 7, 22),
                configuration=_configuration(),
            )
        with self.assertRaisesRegex(ValidationError, "timezone-aware"):
            _review().model_validate(
                {**_review().model_dump(), "reviewed_at": datetime(2026, 7, 22)}
            )
        with self.assertRaises(ValidationError):
            BacktestStudyArtifact(
                artifact_version=1,
                status="published",
                definition=_definition(),
            )

    def test_execution_must_match_definition_configuration(self) -> None:
        definition = _definition().model_copy(
            update={"configuration": _configuration(dataset_id="another-dataset")}
        )

        with self.assertRaisesRegex(ValidationError, "match the definition"):
            BacktestStudyArtifact(
                artifact_version=1,
                status=BacktestStudyStatus.EXECUTED,
                definition=definition,
                execution=_execution(),
            )

    def test_execution_band_set_identity_must_match_definition(self) -> None:
        execution = _execution()
        for updates in (
            {"band_set_id": "different-bands"},
            {"band_set_version": 2},
        ):
            with self.subTest(updates=updates):
                mismatched = execution.model_copy(
                    update={"metadata": execution.metadata.model_copy(update=updates)}
                )
                with self.assertRaisesRegex(ValidationError, "match the definition"):
                    BacktestStudyArtifact(
                        artifact_version=1,
                        status=BacktestStudyStatus.EXECUTED,
                        definition=_definition(),
                        execution=mismatched,
                    )

    def test_execution_threshold_set_identity_must_match_definition(self) -> None:
        execution = _execution()
        for updates in (
            {"threshold_set_id": "different-thresholds"},
            {"threshold_set_version": 2},
        ):
            with self.subTest(updates=updates):
                mismatched = execution.model_copy(
                    update={"metadata": execution.metadata.model_copy(update=updates)}
                )
                with self.assertRaisesRegex(ValidationError, "match the definition"):
                    BacktestStudyArtifact(
                        artifact_version=1,
                        status=BacktestStudyStatus.EXECUTED,
                        definition=_definition(),
                        execution=mismatched,
                    )
