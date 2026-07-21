from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta, timezone
from math import sqrt

from app.services.analytics.calculators.channel.upload_consistency import (
    UploadConsistencyCalculator,
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


class UploadConsistencyCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = UploadConsistencyCalculator()
        self.start = datetime(2026, 7, 1, tzinfo=UTC)

    def test_metric_identity_and_protocol_conformance(self) -> None:
        result = self.calculator.calculate(_dataset([self.start]))

        self.assertIsInstance(self.calculator, AnalyticsCalculator)
        self.assertEqual(self.calculator.metric, MetricType.UPLOAD_CONSISTENCY)
        self.assertEqual(result.metric, self.calculator.metric)

    def test_perfectly_regular_uploads(self) -> None:
        dates = [self.start + timedelta(days=days) for days in (0, 7, 14, 21)]
        result = self.calculator.calculate(_dataset(dates))
        self.assertEqual(result.value, 0.0)

    def test_irregular_uploads(self) -> None:
        dates = [self.start + timedelta(days=days) for days in (0, 2, 19, 44)]
        result = self.calculator.calculate(_dataset(dates))
        self.assertAlmostEqual(result.value, sqrt(818) / 44)

    def test_one_video(self) -> None:
        result = self.calculator.calculate(_dataset([self.start]))
        self.assertEqual(result.value, 0.0)

    def test_two_videos(self) -> None:
        result = self.calculator.calculate(
            _dataset([self.start, self.start + timedelta(days=10)])
        )
        self.assertEqual(result.value, 0.0)

    def test_identical_timestamps(self) -> None:
        result = self.calculator.calculate(
            _dataset([self.start, self.start, self.start])
        )
        self.assertEqual(result.value, 0.0)

    def test_unsorted_input(self) -> None:
        dates = [
            self.start + timedelta(days=14),
            self.start,
            self.start + timedelta(days=7),
        ]
        result = self.calculator.calculate(_dataset(dates))
        self.assertEqual(result.value, 0.0)

    def test_timezone_aware_timestamps_use_elapsed_instants(self) -> None:
        india = timezone(timedelta(hours=5, minutes=30))
        dates = [
            self.start,
            (self.start + timedelta(days=7)).astimezone(india),
            self.start + timedelta(days=14),
        ]
        result = self.calculator.calculate(_dataset(dates))
        self.assertEqual(result.value, 0.0)

    def test_empty_collection_is_rejected(self) -> None:
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

    def test_source_dataset_remains_unchanged(self) -> None:
        dataset = _dataset(
            [self.start + timedelta(days=14), self.start, self.start + timedelta(days=3)]
        )
        original_videos = list(dataset.videos)

        self.calculator.calculate(dataset)

        self.assertEqual(dataset.videos, original_videos)


if __name__ == "__main__":
    unittest.main()
