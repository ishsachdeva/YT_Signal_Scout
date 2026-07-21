from __future__ import annotations

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import (
    ChannelAnalytics,
    MetricResult,
    MetricType,
)
from app.services.youtube.models import Channel, Video


class ExampleCalculator:
    @property
    def metric(self) -> MetricType:
        return MetricType.CHANNEL_AGE

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[int]:
        del source_dataset
        return MetricResult[int](metric=self.metric, value=1)


class AnalyticsCalculatorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_dataset = ChannelAnalytics(
            channel=Channel(id="channel-1", title="Example Channel"),
            videos=[Video(id="video-1", channel_id="channel-1", title="Video")],
            generated_at=datetime(2026, 7, 21, 12, 30, tzinfo=UTC),
        )

    def test_calculator_contract_accepts_dataset_and_returns_one_typed_result(
        self,
    ) -> None:
        calculator = ExampleCalculator()

        self.assertIsInstance(calculator, AnalyticsCalculator)
        result = calculator.calculate(self.source_dataset)
        self.assertIsInstance(result, MetricResult)
        self.assertEqual(calculator.metric, MetricType.CHANNEL_AGE)
        self.assertEqual(result.metric, calculator.metric)
        self.assertEqual(result.value, 1)

    def test_metric_result_is_immutable(self) -> None:
        result = MetricResult[int](metric=MetricType.CHANNEL_AGE, value=1)

        with self.assertRaises(ValidationError):
            result.value = 2


if __name__ == "__main__":
    unittest.main()
