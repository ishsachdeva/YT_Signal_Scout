from __future__ import annotations

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from app.services.analytics.assembler import AnalyticsAssembler, _SUPPORTED_METRICS
from app.services.analytics.exceptions import AnalyticsAssemblyError
from app.services.analytics.models import (
    CalculatedChannelAnalytics,
    ChannelAnalytics,
    MetricResult,
    MetricType,
    OutlierResult,
)
from app.services.youtube.models import Channel, Video


def _dataset() -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=[Video(id="video-1", channel_id="channel-1", title="Video")],
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


def _outlier_result() -> OutlierResult:
    return OutlierResult(
        highest_video_id="video-1",
        highest_z_score=1.25,
        lowest_video_id="video-2",
        lowest_z_score=-1.25,
    )


def _metric_results() -> tuple[MetricResult[object], ...]:
    return (
        MetricResult[int](metric=MetricType.CHANNEL_AGE, value=365),
        MetricResult[float](metric=MetricType.UPLOAD_FREQUENCY, value=2.5),
        MetricResult[float](metric=MetricType.AVERAGE_VIEWS, value=1_500.0),
        MetricResult[float](metric=MetricType.MEDIAN_VIEWS, value=1_250.0),
        MetricResult[float](metric=MetricType.VIEWS_PER_DAY, value=75.5),
        MetricResult[float](metric=MetricType.VIEW_DISTRIBUTION, value=0.4),
        MetricResult[float](metric=MetricType.UPLOAD_CONSISTENCY, value=0.2),
        MetricResult[OutlierResult](
            metric=MetricType.VIEW_OUTLIER,
            value=_outlier_result(),
        ),
        MetricResult[float](metric=MetricType.VIEW_GROWTH_RATE, value=1.3),
        MetricResult[float | None](
            metric=MetricType.VIEW_ENGAGEMENT_RATE,
            value=None,
        ),
    )


class AnalyticsAssemblerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assembler = AnalyticsAssembler()
        self.dataset = _dataset()

    def test_valid_results_are_assembled_into_typed_properties(self) -> None:
        analytics = self.assembler.assemble(self.dataset, _metric_results())

        self.assertIs(analytics.source_dataset, self.dataset)
        self.assertEqual(analytics.channel_age, 365)
        self.assertEqual(analytics.upload_frequency, 2.5)
        self.assertEqual(analytics.average_views, 1_500.0)
        self.assertEqual(analytics.median_views, 1_250.0)
        self.assertEqual(analytics.views_per_day, 75.5)
        self.assertEqual(analytics.view_distribution, 0.4)
        self.assertEqual(analytics.upload_consistency, 0.2)
        self.assertEqual(analytics.view_outlier, _outlier_result())
        self.assertEqual(analytics.view_growth_rate, 1.3)
        self.assertIsNone(analytics.view_engagement_rate)

    def test_missing_metric_is_rejected(self) -> None:
        results = tuple(
            result
            for result in _metric_results()
            if result.metric is not MetricType.MEDIAN_VIEWS
        )

        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "missing required metrics: median_views",
        ):
            self.assembler.assemble(self.dataset, results)

    def test_duplicate_metric_is_rejected(self) -> None:
        duplicate = MetricResult[object](
            metric=MetricType.CHANNEL_AGE,
            value=730,
        )

        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "duplicate metric result: channel_age",
        ):
            self.assembler.assemble(
                self.dataset,
                (*_metric_results(), duplicate),
            )

    def test_unexpected_metric_is_rejected(self) -> None:
        unexpected = MetricResult[object].model_construct(
            metric="future_metric",
            value=1,
        )

        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "unexpected metric: future_metric",
        ):
            self.assembler.assemble(self.dataset, (*_metric_results(), unexpected))

    def test_ordering_does_not_affect_assembly(self) -> None:
        forward = self.assembler.assemble(self.dataset, _metric_results())
        reverse = self.assembler.assemble(
            self.dataset,
            reversed(_metric_results()),
        )

        self.assertEqual(forward, reverse)

    def test_optional_engagement_rate_accepts_a_float(self) -> None:
        results = tuple(
            MetricResult[object](metric=result.metric, value=0.075)
            if result.metric is MetricType.VIEW_ENGAGEMENT_RATE
            else result
            for result in _metric_results()
        )

        analytics = self.assembler.assemble(self.dataset, results)

        self.assertEqual(analytics.view_engagement_rate, 0.075)

    def test_assembly_is_deterministic(self) -> None:
        first = self.assembler.assemble(self.dataset, _metric_results())
        second = self.assembler.assemble(self.dataset, _metric_results())

        self.assertEqual(first, second)

    def test_non_metric_result_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsAssemblyError,
            "metric results must contain MetricResult objects",
        ):
            self.assembler.assemble(
                self.dataset,
                [object()],  # type: ignore[list-item]
            )

    def test_supported_metrics_match_current_aggregate_contract(self) -> None:
        self.assertEqual(
            _SUPPORTED_METRICS,
            frozenset(
                {
                    MetricType.CHANNEL_AGE,
                    MetricType.UPLOAD_FREQUENCY,
                    MetricType.AVERAGE_VIEWS,
                    MetricType.MEDIAN_VIEWS,
                    MetricType.VIEWS_PER_DAY,
                    MetricType.VIEW_DISTRIBUTION,
                    MetricType.UPLOAD_CONSISTENCY,
                    MetricType.VIEW_OUTLIER,
                    MetricType.VIEW_GROWTH_RATE,
                    MetricType.VIEW_ENGAGEMENT_RATE,
                }
            ),
        )
        self.assertNotIn(
            MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
            _SUPPORTED_METRICS,
        )


class CalculatedChannelAnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analytics = AnalyticsAssembler().assemble(_dataset(), _metric_results())

    def test_aggregate_is_immutable(self) -> None:
        with self.assertRaises(ValidationError):
            self.analytics.channel_age = 730

    def test_equal_values_produce_equal_aggregates(self) -> None:
        equivalent = AnalyticsAssembler().assemble(_dataset(), _metric_results())

        self.assertEqual(self.analytics, equivalent)

    def test_aggregate_is_a_typed_domain_model(self) -> None:
        self.assertIsInstance(self.analytics, CalculatedChannelAnalytics)
        self.assertIsInstance(self.analytics.channel_age, int)
        self.assertIsInstance(self.analytics.view_outlier, OutlierResult)


if __name__ == "__main__":
    unittest.main()
