from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta, timezone

from app.services.analytics.calculators.channel.upload_frequency import (
    UploadFrequencyCalculator,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricType
from app.services.youtube.models import Channel, Video


def _dataset(publication_dates: list[datetime | None]) -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=[
            Video(
                id=f"video-{index}",
                channel_id="channel-1",
                title="Video",
                published_at=published_at,
            )
            for index, published_at in enumerate(publication_dates)
        ],
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


class UploadFrequencyCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = UploadFrequencyCalculator()
        self.start = datetime(2026, 7, 1, tzinfo=UTC)

    def test_metric_identity_and_protocol_conformance(self) -> None:
        result = self.calculator.calculate(_dataset([self.start]))

        self.assertIsInstance(self.calculator, AnalyticsCalculator)
        self.assertEqual(self.calculator.metric, MetricType.UPLOAD_FREQUENCY)
        self.assertEqual(result.metric, self.calculator.metric)

    def test_normal_multi_video_cadence(self) -> None:
        result = self.calculator.calculate(
            _dataset([self.start, self.start + timedelta(days=7)])
        )
        self.assertEqual(result.value, 2.0)

    def test_unsorted_publication_timestamps(self) -> None:
        dates = [
            self.start + timedelta(days=14),
            self.start,
            self.start + timedelta(days=7),
        ]
        result = self.calculator.calculate(_dataset(dates))
        self.assertEqual(result.value, 1.5)

    def test_exact_seven_day_observation_period(self) -> None:
        dates = [self.start, self.start + timedelta(days=3), self.start + timedelta(days=7)]
        result = self.calculator.calculate(_dataset(dates))
        self.assertEqual(result.value, 3.0)

    def test_fractional_day_observation_period(self) -> None:
        dates = [self.start, self.start + timedelta(hours=36)]
        result = self.calculator.calculate(_dataset(dates))
        self.assertAlmostEqual(result.value, 2 / 1.5 * 7)

    def test_one_video_returns_one(self) -> None:
        result = self.calculator.calculate(_dataset([self.start]))
        self.assertEqual(result.value, 1.0)

    def test_identical_timestamps_use_one_day_minimum(self) -> None:
        result = self.calculator.calculate(_dataset([self.start, self.start]))
        self.assertEqual(result.value, 14.0)

    def test_empty_video_collection_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "videos must not be empty"):
            self.calculator.calculate(_dataset([]))

    def test_missing_source_dataset_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "source dataset is required"):
            self.calculator.calculate(None)  # type: ignore[arg-type]

    def test_missing_publication_timestamp_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "date is required"):
            self.calculator.calculate(_dataset([None]))

    def test_naive_publication_timestamp_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "must be timezone-aware"):
            self.calculator.calculate(_dataset([datetime(2026, 7, 1)]))

    def test_equivalent_timezone_instants_produce_zero_length_window(self) -> None:
        india = timezone(timedelta(hours=5, minutes=30))
        result = self.calculator.calculate(_dataset([self.start, self.start.astimezone(india)]))
        self.assertEqual(result.value, 14.0)

    def test_source_video_order_remains_unchanged(self) -> None:
        dataset = _dataset(
            [self.start + timedelta(days=7), self.start, self.start + timedelta(days=3)]
        )
        original_ids = [video.id for video in dataset.videos]

        self.calculator.calculate(dataset)

        self.assertEqual([video.id for video in dataset.videos], original_ids)


if __name__ == "__main__":
    unittest.main()
