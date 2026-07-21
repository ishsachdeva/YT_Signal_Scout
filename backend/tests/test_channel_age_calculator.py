from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta, timezone

from app.services.analytics.calculators.channel.channel_age import ChannelAgeCalculator
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricType
from app.services.youtube.models import Channel, Video


def _dataset(published_at: datetime | None) -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(
            id="channel-1",
            title="Example Channel",
            published_at=published_at,
        ),
        videos=[Video(id="video-1", channel_id="channel-1", title="Video")],
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


class ChannelAgeCalculatorTests(unittest.TestCase):
    def test_normal_calculation(self) -> None:
        calculated_at = datetime(2026, 7, 21, 18, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        result = calculator.calculate(_dataset(datetime(2026, 7, 11, 6, tzinfo=UTC)))

        self.assertEqual(result.value, 10)

    def test_channel_created_today(self) -> None:
        calculated_at = datetime(2026, 7, 21, 18, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        result = calculator.calculate(_dataset(datetime(2026, 7, 21, 9, tzinfo=UTC)))

        self.assertEqual(result.value, 0)

    def test_one_day_old_channel(self) -> None:
        calculated_at = datetime(2026, 7, 21, 18, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        result = calculator.calculate(_dataset(datetime(2026, 7, 20, 18, tzinfo=UTC)))

        self.assertEqual(result.value, 1)

    def test_leap_year_handling(self) -> None:
        calculated_at = datetime(2024, 3, 1, 12, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        result = calculator.calculate(_dataset(datetime(2024, 2, 28, 12, tzinfo=UTC)))

        self.assertEqual(result.value, 2)

    def test_timezone_aware_calculation_uses_elapsed_time(self) -> None:
        india = timezone(timedelta(hours=5, minutes=30))
        calculated_at = datetime(2026, 7, 22, 0, tzinfo=india)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        result = calculator.calculate(_dataset(datetime(2026, 7, 20, 18, 30, tzinfo=UTC)))

        self.assertEqual(result.value, 1)

    def test_future_publication_date_is_rejected(self) -> None:
        calculated_at = datetime(2026, 7, 21, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        with self.assertRaisesRegex(AnalyticsValidationError, "cannot be in the future"):
            calculator.calculate(_dataset(datetime(2026, 7, 22, tzinfo=UTC)))

    def test_naive_publication_date_is_rejected(self) -> None:
        calculated_at = datetime(2026, 7, 21, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        with self.assertRaisesRegex(AnalyticsValidationError, "must be timezone-aware"):
            calculator.calculate(_dataset(datetime(2026, 7, 20)))

    def test_missing_publication_date_is_rejected(self) -> None:
        calculated_at = datetime(2026, 7, 21, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        with self.assertRaisesRegex(AnalyticsValidationError, "is required"):
            calculator.calculate(_dataset(None))

    def test_naive_clock_value_is_rejected(self) -> None:
        calculator = ChannelAgeCalculator(clock=lambda: datetime(2026, 7, 21))

        with self.assertRaisesRegex(AnalyticsValidationError, "clock must be timezone-aware"):
            calculator.calculate(_dataset(datetime(2026, 7, 20, tzinfo=UTC)))

    def test_metric_identity(self) -> None:
        calculated_at = datetime(2026, 7, 21, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)

        result = calculator.calculate(_dataset(datetime(2026, 7, 20, tzinfo=UTC)))

        self.assertIsInstance(calculator, AnalyticsCalculator)
        self.assertEqual(calculator.metric, MetricType.CHANNEL_AGE)
        self.assertEqual(result.metric, calculator.metric)

    def test_injected_clock_is_deterministic(self) -> None:
        calculated_at = datetime(2026, 7, 21, 12, tzinfo=UTC)
        calculator = ChannelAgeCalculator(clock=lambda: calculated_at)
        dataset = _dataset(datetime(2026, 7, 1, 12, tzinfo=UTC))

        first = calculator.calculate(dataset)
        second = calculator.calculate(dataset)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
