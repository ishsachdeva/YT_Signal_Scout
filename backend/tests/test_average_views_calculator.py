from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.services.analytics.calculators.video.average_views import (
    AverageViewsCalculator,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricType
from app.services.youtube.models import Channel, Video


def _dataset(view_counts: list[int | None]) -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=[
            Video(
                id=f"video-{index}",
                channel_id="channel-1",
                title="Video",
                view_count=view_count,
            )
            for index, view_count in enumerate(view_counts)
        ],
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


class AverageViewsCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = AverageViewsCalculator()

    def test_metric_identity_and_protocol_conformance(self) -> None:
        result = self.calculator.calculate(_dataset([100]))

        self.assertIsInstance(self.calculator, AnalyticsCalculator)
        self.assertEqual(self.calculator.metric, MetricType.AVERAGE_VIEWS)
        self.assertEqual(result.metric, self.calculator.metric)

    def test_normal_calculation(self) -> None:
        result = self.calculator.calculate(_dataset([100, 200, 300]))
        self.assertEqual(result.value, 200.0)

    def test_one_video(self) -> None:
        result = self.calculator.calculate(_dataset([125]))
        self.assertEqual(result.value, 125.0)

    def test_zero_view_counts(self) -> None:
        result = self.calculator.calculate(_dataset([0, 0]))
        self.assertEqual(result.value, 0.0)

    def test_decimal_result_is_not_rounded(self) -> None:
        result = self.calculator.calculate(_dataset([1, 2]))
        self.assertEqual(result.value, 1.5)

    def test_empty_video_collection_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "videos must not be empty"):
            self.calculator.calculate(_dataset([]))

    def test_missing_source_dataset_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "source dataset is required"):
            self.calculator.calculate(None)  # type: ignore[arg-type]

    def test_missing_view_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "view count is required"):
            self.calculator.calculate(_dataset([None]))

    def test_negative_view_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "cannot be negative"):
            self.calculator.calculate(_dataset([-1]))

    def test_source_dataset_remains_unchanged(self) -> None:
        dataset = _dataset([300, 100, 200])
        original_videos = list(dataset.videos)

        self.calculator.calculate(dataset)

        self.assertEqual(dataset.videos, original_videos)


if __name__ == "__main__":
    unittest.main()
