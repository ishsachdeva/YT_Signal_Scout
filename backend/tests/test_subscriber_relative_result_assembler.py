"""Tests for subscriber-relative result assembly."""

from __future__ import annotations

from unittest import TestCase

from pydantic import ValidationError

from app.services.analytics.exceptions import AnalyticsAssemblyError
from app.services.analytics.models import (
    MetricResult,
    MetricType,
    SubscriberRelativeAnalytics,
)
from app.services.analytics.subscriber_relative_result_assembler import (
    SubscriberRelativeResultAssembler,
    _SUPPORTED_METRICS,
)


def _metric_results() -> tuple[MetricResult[object], ...]:
    return (
        MetricResult[int](
            metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
            value=7,
        ),
        MetricResult[float | None](
            metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR,
            value=1.25,
        ),
    )


class SubscriberRelativeResultAssemblerTests(TestCase):
    """Verify explicit mapping and deterministic structural validation."""

    def setUp(self) -> None:
        self.assembler = SubscriberRelativeResultAssembler()

    def test_successful_assembly_maps_both_metrics(self) -> None:
        analytics = self.assembler.assemble(_metric_results())

        self.assertIsInstance(analytics, SubscriberRelativeAnalytics)
        self.assertEqual(analytics.eligible_standard_video_count, 7)
        self.assertEqual(analytics.median_standard_video_vsr, 1.25)

    def test_none_median_is_mapped_as_unavailable(self) -> None:
        results = (
            _metric_results()[0],
            MetricResult[float | None](
                metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR,
                value=None,
            ),
        )

        analytics = self.assembler.assemble(results)

        self.assertIsNone(analytics.median_standard_video_vsr)

    def test_missing_eligible_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "missing required metrics: eligible_standard_video_count",
        ):
            self.assembler.assemble((_metric_results()[1],))

    def test_missing_median_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "missing required metrics: median_standard_video_vsr",
        ):
            self.assembler.assemble((_metric_results()[0],))

    def test_duplicate_metric_is_rejected(self) -> None:
        duplicate = MetricResult[int](
            metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
            value=9,
        )

        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "duplicate metric result: eligible_standard_video_count",
        ):
            self.assembler.assemble((*_metric_results(), duplicate))

    def test_unexpected_metric_is_rejected(self) -> None:
        unexpected = MetricResult[int](metric=MetricType.CHANNEL_AGE, value=365)

        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "unexpected metric: MetricType.CHANNEL_AGE",
        ):
            self.assembler.assemble((*_metric_results(), unexpected))

    def test_non_metric_result_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "metric results must contain MetricResult objects",
        ):
            self.assembler.assemble((object(),))  # type: ignore[arg-type]

    def test_mutable_metric_collection_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "metric results must be a tuple",
        ):
            self.assembler.assemble(list(_metric_results()))  # type: ignore[arg-type]

    def test_input_order_does_not_change_mapping(self) -> None:
        forward = self.assembler.assemble(_metric_results())
        reverse = self.assembler.assemble(tuple(reversed(_metric_results())))

        self.assertEqual(forward, reverse)

    def test_repeated_assembly_is_deterministic(self) -> None:
        first = self.assembler.assemble(_metric_results())
        second = self.assembler.assemble(_metric_results())

        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_aggregate_is_immutable(self) -> None:
        analytics = self.assembler.assemble(_metric_results())

        with self.assertRaises(ValidationError):
            analytics.eligible_standard_video_count = 8

    def test_aggregate_contains_exactly_the_approved_fields(self) -> None:
        self.assertEqual(
            set(SubscriberRelativeAnalytics.model_fields),
            {
                "eligible_standard_video_count",
                "median_standard_video_vsr",
            },
        )

    def test_supported_metrics_match_the_aggregate_contract(self) -> None:
        self.assertEqual(
            _SUPPORTED_METRICS,
            frozenset(
                {
                    MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                    MetricType.MEDIAN_STANDARD_VIDEO_VSR,
                }
            ),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
