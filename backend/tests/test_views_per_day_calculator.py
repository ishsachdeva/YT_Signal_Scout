from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import Mock

from app.services.analytics.calculators.video.views_per_day import (
    ViewsPerDayCalculator,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricType
from app.services.youtube.models import Channel, Video


def _dataset(videos: list[Video]) -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=videos,
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


def _video(
    *, view_count: int | None, published_at: datetime | None, index: int = 1
) -> Video:
    return Video(
        id=f"video-{index}",
        channel_id="channel-1",
        title="Video",
        view_count=view_count,
        published_at=published_at,
    )


class ViewsPerDayCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculated_at = datetime(2026, 7, 21, 12, tzinfo=UTC)
        self.calculator = ViewsPerDayCalculator(clock=lambda: self.calculated_at)

    def test_metric_identity_and_protocol_conformance(self) -> None:
        dataset = _dataset(
            [_video(view_count=100, published_at=self.calculated_at - timedelta(days=1))]
        )

        result = self.calculator.calculate(dataset)

        self.assertIsInstance(self.calculator, AnalyticsCalculator)
        self.assertEqual(self.calculator.metric, MetricType.VIEWS_PER_DAY)
        self.assertEqual(result.metric, self.calculator.metric)

    def test_normal_multi_video_calculation(self) -> None:
        dataset = _dataset(
            [
                _video(
                    view_count=200,
                    published_at=self.calculated_at - timedelta(days=2),
                ),
                _video(
                    view_count=100,
                    published_at=self.calculated_at - timedelta(days=1),
                    index=2,
                ),
            ]
        )

        result = self.calculator.calculate(dataset)

        self.assertEqual(result.value, 100.0)

    def test_exactly_one_day_old_video(self) -> None:
        dataset = _dataset(
            [_video(view_count=120, published_at=self.calculated_at - timedelta(days=1))]
        )
        self.assertEqual(self.calculator.calculate(dataset).value, 120.0)

    def test_video_younger_than_one_day_uses_floor(self) -> None:
        dataset = _dataset(
            [_video(view_count=120, published_at=self.calculated_at - timedelta(hours=12))]
        )
        self.assertEqual(self.calculator.calculate(dataset).value, 120.0)

    def test_fractional_elapsed_days(self) -> None:
        dataset = _dataset(
            [_video(view_count=150, published_at=self.calculated_at - timedelta(hours=36))]
        )
        self.assertAlmostEqual(self.calculator.calculate(dataset).value, 100.0)

    def test_zero_views(self) -> None:
        dataset = _dataset(
            [_video(view_count=0, published_at=self.calculated_at - timedelta(days=2))]
        )
        self.assertEqual(self.calculator.calculate(dataset).value, 0.0)

    def test_injected_clock_is_deterministic(self) -> None:
        dataset = _dataset(
            [_video(view_count=100, published_at=self.calculated_at - timedelta(days=2))]
        )
        self.assertEqual(
            self.calculator.calculate(dataset), self.calculator.calculate(dataset)
        )

    def test_injected_clock_is_called_once(self) -> None:
        clock = Mock(return_value=self.calculated_at)
        calculator = ViewsPerDayCalculator(clock=clock)
        dataset = _dataset(
            [
                _video(
                    view_count=100,
                    published_at=self.calculated_at - timedelta(days=1),
                ),
                _video(
                    view_count=200,
                    published_at=self.calculated_at - timedelta(days=2),
                    index=2,
                ),
            ]
        )

        calculator.calculate(dataset)

        clock.assert_called_once_with()

    def test_equivalent_timezone_aware_instants(self) -> None:
        india = timezone(timedelta(hours=5, minutes=30))
        published_at = (self.calculated_at - timedelta(days=2)).astimezone(india)
        dataset = _dataset([_video(view_count=200, published_at=published_at)])

        self.assertAlmostEqual(self.calculator.calculate(dataset).value, 100.0)

    def test_future_publication_timestamp_is_rejected(self) -> None:
        dataset = _dataset(
            [_video(view_count=100, published_at=self.calculated_at + timedelta(seconds=1))]
        )
        with self.assertRaisesRegex(AnalyticsValidationError, "cannot be in the future"):
            self.calculator.calculate(dataset)

    def test_naive_publication_timestamp_is_rejected(self) -> None:
        dataset = _dataset(
            [_video(view_count=100, published_at=datetime(2026, 7, 20))]
        )
        with self.assertRaisesRegex(AnalyticsValidationError, "must be timezone-aware"):
            self.calculator.calculate(dataset)

    def test_naive_clock_is_rejected(self) -> None:
        calculator = ViewsPerDayCalculator(clock=lambda: datetime(2026, 7, 21))
        dataset = _dataset(
            [_video(view_count=100, published_at=self.calculated_at - timedelta(days=1))]
        )
        with self.assertRaisesRegex(AnalyticsValidationError, "clock must be timezone-aware"):
            calculator.calculate(dataset)

    def test_missing_publication_timestamp_is_rejected(self) -> None:
        dataset = _dataset([_video(view_count=100, published_at=None)])
        with self.assertRaisesRegex(AnalyticsValidationError, "date is required"):
            self.calculator.calculate(dataset)

    def test_missing_view_count_is_rejected(self) -> None:
        dataset = _dataset(
            [_video(view_count=None, published_at=self.calculated_at - timedelta(days=1))]
        )
        with self.assertRaisesRegex(AnalyticsValidationError, "view count is required"):
            self.calculator.calculate(dataset)

    def test_negative_view_count_is_rejected(self) -> None:
        dataset = _dataset(
            [_video(view_count=-1, published_at=self.calculated_at - timedelta(days=1))]
        )
        with self.assertRaisesRegex(AnalyticsValidationError, "cannot be negative"):
            self.calculator.calculate(dataset)

    def test_empty_video_collection_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "videos must not be empty"):
            self.calculator.calculate(_dataset([]))

    def test_missing_source_dataset_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "source dataset is required"):
            self.calculator.calculate(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
