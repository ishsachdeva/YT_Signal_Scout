from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.services.analytics.calculators.channel.view_engagement_rate import (
    ViewEngagementRateCalculator,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricType
from app.services.youtube.models import Channel, Video


def _dataset(
    entries: list[tuple[int | None, int | None, int | None]],
) -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=[
            Video(
                id=f"video-{index}",
                channel_id="channel-1",
                title="Video",
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
            )
            for index, (view_count, like_count, comment_count) in enumerate(entries)
        ],
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


class ViewEngagementRateCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = ViewEngagementRateCalculator()

    def test_metric_identity_and_protocol_conformance(self) -> None:
        result = self.calculator.calculate(_dataset([(100, 10, 5)]))

        self.assertIsInstance(self.calculator, AnalyticsCalculator)
        self.assertEqual(self.calculator.metric, MetricType.VIEW_ENGAGEMENT_RATE)
        self.assertEqual(result.metric, self.calculator.metric)

    def test_multiple_valid_videos_use_mean_of_individual_rates(self) -> None:
        result = self.calculator.calculate(
            _dataset([(100, 10, 10), (1000, 50, 50)])
        )

        self.assertAlmostEqual(result.value, 0.15)

    def test_single_video(self) -> None:
        result = self.calculator.calculate(_dataset([(200, 20, 10)]))

        self.assertAlmostEqual(result.value, 0.15)

    def test_decimal_engagement_rate(self) -> None:
        result = self.calculator.calculate(_dataset([(3, 1, 0)]))

        self.assertAlmostEqual(result.value, 1 / 3)

    def test_zero_views_are_excluded(self) -> None:
        result = self.calculator.calculate(_dataset([(0, 10, 5), (100, 5, 5)]))

        self.assertAlmostEqual(result.value, 0.1)

    def test_missing_likes_are_excluded(self) -> None:
        result = self.calculator.calculate(
            _dataset([(100, None, 5), (100, 10, 5)])
        )

        self.assertAlmostEqual(result.value, 0.15)

    def test_missing_comments_are_excluded(self) -> None:
        result = self.calculator.calculate(
            _dataset([(100, 10, None), (100, 10, 5)])
        )

        self.assertAlmostEqual(result.value, 0.15)

    def test_no_eligible_videos_returns_none(self) -> None:
        result = self.calculator.calculate(
            _dataset([(0, 10, 5), (100, None, 5), (100, 10, None)])
        )

        self.assertIsNone(result.value)

    def test_empty_collection_returns_none(self) -> None:
        result = self.calculator.calculate(_dataset([]))

        self.assertIsNone(result.value)

    def test_engagement_greater_than_views_is_not_clamped(self) -> None:
        result = self.calculator.calculate(_dataset([(10, 12, 8)]))

        self.assertEqual(result.value, 2.0)

    def test_very_large_numbers(self) -> None:
        result = self.calculator.calculate(
            _dataset([(10**18, 2 * 10**17, 3 * 10**17)])
        )

        self.assertAlmostEqual(result.value, 0.5)

    def test_mixed_valid_and_invalid_videos(self) -> None:
        result = self.calculator.calculate(
            _dataset(
                [
                    (100, 10, 0),
                    (0, 100, 100),
                    (200, None, 20),
                    (400, 40, 40),
                ]
            )
        )

        self.assertAlmostEqual(result.value, 0.15)

    def test_missing_source_dataset_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "required"):
            self.calculator.calculate(None)  # type: ignore[arg-type]

    def test_calculation_is_deterministic(self) -> None:
        dataset = _dataset([(100, 10, 5), (200, 20, 10)])

        first_result = self.calculator.calculate(dataset)
        second_result = self.calculator.calculate(dataset)

        self.assertEqual(first_result, second_result)

    def test_source_dataset_remains_unchanged(self) -> None:
        dataset = _dataset([(100, 10, 5), (0, 20, 10)])
        original_videos = list(dataset.videos)

        self.calculator.calculate(dataset)

        self.assertEqual(dataset.videos, original_videos)


if __name__ == "__main__":
    unittest.main()
