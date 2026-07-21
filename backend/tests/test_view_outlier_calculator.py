from __future__ import annotations

import unittest
from datetime import UTC, datetime
from math import sqrt

from pydantic import ValidationError

from app.services.analytics.calculators.channel.view_outlier import (
    ViewOutlierCalculator,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricType, OutlierResult
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


class ViewOutlierCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = ViewOutlierCalculator()

    def test_metric_identity_and_protocol_conformance(self) -> None:
        result = self.calculator.calculate(_dataset([100]))

        self.assertIsInstance(self.calculator, AnalyticsCalculator)
        self.assertEqual(self.calculator.metric, MetricType.VIEW_OUTLIER)
        self.assertEqual(result.metric, self.calculator.metric)
        self.assertIsInstance(result.value, OutlierResult)

    def test_single_obvious_positive_outlier(self) -> None:
        result = self.calculator.calculate(_dataset([10, 10, 100])).value

        self.assertEqual(result.highest_video_id, "video-2")
        self.assertAlmostEqual(result.highest_z_score, sqrt(2))

    def test_single_obvious_negative_outlier(self) -> None:
        result = self.calculator.calculate(_dataset([0, 100, 100])).value

        self.assertEqual(result.lowest_video_id, "video-0")
        self.assertAlmostEqual(result.lowest_z_score, -sqrt(2))

    def test_identical_view_counts_return_no_outliers(self) -> None:
        result = self.calculator.calculate(_dataset([100, 100, 100])).value

        self.assertEqual(
            result,
            OutlierResult(
                highest_video_id=None,
                highest_z_score=0.0,
                lowest_video_id=None,
                lowest_z_score=0.0,
            ),
        )

    def test_one_video_returns_no_outliers(self) -> None:
        result = self.calculator.calculate(_dataset([100])).value

        self.assertIsNone(result.highest_video_id)
        self.assertIsNone(result.lowest_video_id)
        self.assertEqual(result.highest_z_score, 0.0)
        self.assertEqual(result.lowest_z_score, 0.0)

    def test_zero_standard_deviation_returns_no_outliers(self) -> None:
        result = self.calculator.calculate(_dataset([0, 0])).value

        self.assertIsNone(result.highest_video_id)
        self.assertIsNone(result.lowest_video_id)

    def test_mixed_distribution(self) -> None:
        result = self.calculator.calculate(_dataset([0, 10, 20, 100])).value

        self.assertEqual(result.highest_video_id, "video-3")
        self.assertGreater(result.highest_z_score, 0.0)
        self.assertEqual(result.lowest_video_id, "video-0")
        self.assertLess(result.lowest_z_score, 0.0)

    def test_empty_collection_is_rejected(self) -> None:
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
        dataset = _dataset([300, 0, 100])
        original_videos = list(dataset.videos)

        self.calculator.calculate(dataset)

        self.assertEqual(dataset.videos, original_videos)

    def test_outlier_result_is_immutable(self) -> None:
        result = self.calculator.calculate(_dataset([0, 100])).value

        with self.assertRaises(ValidationError):
            result.highest_video_id = "replacement"

    def test_ties_select_first_video_in_source_order(self) -> None:
        result = self.calculator.calculate(_dataset([0, 0, 100, 100])).value

        self.assertEqual(result.highest_video_id, "video-2")
        self.assertEqual(result.lowest_video_id, "video-0")


if __name__ == "__main__":
    unittest.main()
