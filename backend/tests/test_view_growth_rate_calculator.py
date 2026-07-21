from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from math import isinf

from app.services.analytics.calculators.channel.view_growth_rate import (
    ViewGrowthRateCalculator,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricType
from app.services.youtube.models import Channel, Video


def _dataset(entries: list[tuple[datetime | None, int | None]]) -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=[
            Video(
                id=f"video-{index}",
                channel_id="channel-1",
                title="Video",
                published_at=published_at,
                view_count=view_count,
            )
            for index, (published_at, view_count) in enumerate(entries)
        ],
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


class ViewGrowthRateCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = ViewGrowthRateCalculator()
        self.start = datetime(2026, 7, 1, tzinfo=UTC)

    def _ordered_dataset(self, view_counts: list[int]) -> ChannelAnalytics:
        return _dataset(
            [
                (self.start + timedelta(days=index), view_count)
                for index, view_count in enumerate(view_counts)
            ]
        )

    def test_metric_identity_and_protocol_conformance(self) -> None:
        result = self.calculator.calculate(self._ordered_dataset([100]))

        self.assertIsInstance(self.calculator, AnalyticsCalculator)
        self.assertEqual(self.calculator.metric, MetricType.VIEW_GROWTH_RATE)
        self.assertEqual(result.metric, self.calculator.metric)

    def test_increasing_performance(self) -> None:
        result = self.calculator.calculate(
            self._ordered_dataset([100, 200, 300, 400])
        )
        self.assertAlmostEqual(result.value, 350 / 150)

    def test_declining_performance(self) -> None:
        result = self.calculator.calculate(
            self._ordered_dataset([400, 300, 200, 100])
        )
        self.assertAlmostEqual(result.value, 150 / 350)

    def test_stable_performance(self) -> None:
        result = self.calculator.calculate(
            self._ordered_dataset([100, 100, 100, 100])
        )
        self.assertEqual(result.value, 1.0)

    def test_odd_number_assigns_extra_video_to_newer_half(self) -> None:
        result = self.calculator.calculate(
            self._ordered_dataset([100, 100, 200, 200, 200])
        )
        self.assertEqual(result.value, 2.0)

    def test_one_video(self) -> None:
        result = self.calculator.calculate(self._ordered_dataset([500]))
        self.assertEqual(result.value, 1.0)

    def test_all_zero_views(self) -> None:
        result = self.calculator.calculate(self._ordered_dataset([0, 0, 0, 0]))
        self.assertEqual(result.value, 1.0)

    def test_zero_old_average_with_positive_new_average(self) -> None:
        result = self.calculator.calculate(self._ordered_dataset([0, 0, 100, 200]))
        self.assertTrue(isinf(result.value))
        self.assertGreater(result.value, 0)

    def test_unsorted_input_is_ordered_by_publication_date(self) -> None:
        entries = [
            (self.start + timedelta(days=3), 400),
            (self.start, 100),
            (self.start + timedelta(days=2), 300),
            (self.start + timedelta(days=1), 200),
        ]
        result = self.calculator.calculate(_dataset(entries))
        self.assertAlmostEqual(result.value, 350 / 150)

    def test_validation_failures(self) -> None:
        with self.subTest("missing dataset"):
            with self.assertRaisesRegex(AnalyticsValidationError, "required"):
                self.calculator.calculate(None)  # type: ignore[arg-type]
        with self.subTest("empty collection"):
            with self.assertRaisesRegex(AnalyticsValidationError, "must not be empty"):
                self.calculator.calculate(_dataset([]))
        with self.subTest("missing publication date"):
            with self.assertRaisesRegex(AnalyticsValidationError, "date is required"):
                self.calculator.calculate(_dataset([(None, 100)]))
        with self.subTest("naive publication date"):
            with self.assertRaisesRegex(AnalyticsValidationError, "timezone-aware"):
                self.calculator.calculate(_dataset([(datetime(2026, 7, 1), 100)]))
        with self.subTest("missing view count"):
            with self.assertRaisesRegex(AnalyticsValidationError, "view count is required"):
                self.calculator.calculate(_dataset([(self.start, None)]))
        with self.subTest("negative view count"):
            with self.assertRaisesRegex(AnalyticsValidationError, "cannot be negative"):
                self.calculator.calculate(_dataset([(self.start, -1)]))

    def test_source_dataset_remains_unchanged(self) -> None:
        dataset = self._ordered_dataset([300, 100, 200])
        original_videos = list(dataset.videos)

        self.calculator.calculate(dataset)

        self.assertEqual(dataset.videos, original_videos)


if __name__ == "__main__":
    unittest.main()
