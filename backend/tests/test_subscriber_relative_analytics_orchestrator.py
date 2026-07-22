"""Tests for subscriber-relative analytics orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from unittest import TestCase

from app.services.analytics.calculators.video.eligible_standard_video_count import (
    EligibleStandardVideoCountCalculator,
)
from app.services.analytics.calculators.video.median_standard_video_vsr import (
    MedianStandardVideoVsrCalculator,
)
from app.services.analytics.eligibility import EligibleVideoClassification
from app.services.analytics.exceptions import DuplicateCalculatorError
from app.services.analytics.models import MetricResult, MetricType
from app.services.analytics.subscriber_relative_orchestrator import (
    SubscriberRelativeAnalyticsOrchestrator,
)

_EVALUATED_AT = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _classification() -> EligibleVideoClassification:
    return EligibleVideoClassification(
        eligible_standard_videos=(),
        eligible_shorts=(),
        eligible_livestream_replays=(),
        exclusions=(),
        evaluated_at=_EVALUATED_AT,
    )


class _CountCalculatorSpy:
    metric = MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT

    def __init__(
        self,
        result: MetricResult[int],
        execution_log: list[MetricType],
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.execution_log = execution_log
        self.error = error
        self.calls: list[EligibleVideoClassification] = []

    def calculate(
        self,
        classification: EligibleVideoClassification,
    ) -> MetricResult[int]:
        self.calls.append(classification)
        self.execution_log.append(self.metric)
        if self.error is not None:
            raise self.error
        return self.result


class _MedianCalculatorSpy:
    metric = MetricType.MEDIAN_STANDARD_VIDEO_VSR

    def __init__(
        self,
        result: MetricResult[float | None],
        execution_log: list[MetricType],
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.execution_log = execution_log
        self.error = error
        self.calls: list[tuple[EligibleVideoClassification, int | None]] = []

    def calculate(
        self,
        classification: EligibleVideoClassification,
        subscriber_count: int | None,
    ) -> MetricResult[float | None]:
        self.calls.append((classification, subscriber_count))
        self.execution_log.append(self.metric)
        if self.error is not None:
            raise self.error
        return self.result


class SubscriberRelativeAnalyticsOrchestratorTests(TestCase):
    """Verify sequencing and input delivery without retesting calculations."""

    def setUp(self) -> None:
        self.execution_log: list[MetricType] = []
        self.count_result = MetricResult[int](
            metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
            value=3,
        )
        self.median_result = MetricResult[float | None](
            metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR,
            value=1.5,
        )
        self.count_calculator = _CountCalculatorSpy(
            self.count_result,
            self.execution_log,
        )
        self.median_calculator = _MedianCalculatorSpy(
            self.median_result,
            self.execution_log,
        )
        self.orchestrator = self._orchestrator(
            self.count_calculator,
            self.median_calculator,
        )

    @staticmethod
    def _orchestrator(
        count_calculator: _CountCalculatorSpy,
        median_calculator: _MedianCalculatorSpy,
    ) -> SubscriberRelativeAnalyticsOrchestrator:
        return SubscriberRelativeAnalyticsOrchestrator(
            cast(EligibleStandardVideoCountCalculator, count_calculator),
            cast(MedianStandardVideoVsrCalculator, median_calculator),
        )

    def test_successful_orchestration_preserves_order_and_inputs(self) -> None:
        classification = _classification()

        results = self.orchestrator.calculate_all(classification, 1_000)

        self.assertEqual(results, (self.count_result, self.median_result))
        self.assertEqual(
            self.execution_log,
            [
                MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                MetricType.MEDIAN_STANDARD_VIDEO_VSR,
            ],
        )
        self.assertEqual(self.count_calculator.calls, [classification])
        self.assertEqual(self.median_calculator.calls, [(classification, 1_000)])
        self.assertIs(self.count_calculator.calls[0], classification)
        self.assertIs(self.median_calculator.calls[0][0], classification)

    def test_each_calculator_is_called_exactly_once(self) -> None:
        self.orchestrator.calculate_all(_classification(), None)

        self.assertEqual(len(self.count_calculator.calls), 1)
        self.assertEqual(len(self.median_calculator.calls), 1)

    def test_returned_collection_is_an_immutable_tuple(self) -> None:
        results = self.orchestrator.calculate_all(_classification(), 100)

        self.assertIsInstance(results, tuple)
        with self.assertRaises(TypeError):
            results[0] = self.median_result  # type: ignore[index]

    def test_repeated_execution_is_deterministic(self) -> None:
        classification = _classification()

        first = self.orchestrator.calculate_all(classification, 100)
        second = self.orchestrator.calculate_all(classification, 100)

        self.assertEqual(first, second)
        self.assertEqual(len(self.count_calculator.calls), 2)
        self.assertEqual(len(self.median_calculator.calls), 2)

    def test_first_calculator_failure_propagates_and_stops_execution(self) -> None:
        expected_error = RuntimeError("count failed")
        count_calculator = _CountCalculatorSpy(
            self.count_result,
            self.execution_log,
            expected_error,
        )
        orchestrator = self._orchestrator(count_calculator, self.median_calculator)

        with self.assertRaises(RuntimeError) as raised:
            orchestrator.calculate_all(_classification(), 100)

        self.assertIs(raised.exception, expected_error)
        self.assertEqual(len(count_calculator.calls), 1)
        self.assertEqual(self.median_calculator.calls, [])
        self.assertEqual(
            self.execution_log,
            [MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT],
        )

    def test_second_calculator_failure_propagates_without_partial_result(self) -> None:
        expected_error = RuntimeError("median failed")
        median_calculator = _MedianCalculatorSpy(
            self.median_result,
            self.execution_log,
            expected_error,
        )
        orchestrator = self._orchestrator(self.count_calculator, median_calculator)

        with self.assertRaises(RuntimeError) as raised:
            orchestrator.calculate_all(_classification(), 100)

        self.assertIs(raised.exception, expected_error)
        self.assertEqual(len(self.count_calculator.calls), 1)
        self.assertEqual(len(median_calculator.calls), 1)
        self.assertEqual(
            self.execution_log,
            [
                MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                MetricType.MEDIAN_STANDARD_VIDEO_VSR,
            ],
        )

    def test_duplicate_configured_metric_identities_are_rejected(self) -> None:
        self.median_calculator.metric = MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT

        with self.assertRaisesRegex(
            DuplicateCalculatorError,
            "duplicate calculator registered",
        ):
            self._orchestrator(self.count_calculator, self.median_calculator)


if __name__ == "__main__":
    import unittest

    unittest.main()
