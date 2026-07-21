from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from app.services.analytics.calculators.channel.channel_age import (
    ChannelAgeCalculator,
)
from app.services.analytics.calculators.channel.upload_consistency import (
    UploadConsistencyCalculator,
)
from app.services.analytics.calculators.channel.upload_frequency import (
    UploadFrequencyCalculator,
)
from app.services.analytics.calculators.channel.view_distribution import (
    ViewDistributionCalculator,
)
from app.services.analytics.calculators.channel.view_engagement_rate import (
    ViewEngagementRateCalculator,
)
from app.services.analytics.calculators.channel.view_growth_rate import (
    ViewGrowthRateCalculator,
)
from app.services.analytics.calculators.channel.view_outlier import (
    ViewOutlierCalculator,
)
from app.services.analytics.calculators.video.average_views import (
    AverageViewsCalculator,
)
from app.services.analytics.calculators.video.median_views import (
    MedianViewsCalculator,
)
from app.services.analytics.calculators.video.views_per_day import (
    ViewsPerDayCalculator,
)
from app.services.analytics.exceptions import DuplicateCalculatorError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.registry import CalculatorRegistry
from app.services.youtube.models import Channel, Video


class RecordingCalculator:
    def __init__(
        self,
        metric: MetricType,
        value: object,
        execution_log: list[MetricType],
    ) -> None:
        self._metric = metric
        self._value = value
        self._execution_log = execution_log
        self.received_datasets: list[ChannelAnalytics] = []

    @property
    def metric(self) -> MetricType:
        return self._metric

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[object]:
        self._execution_log.append(self.metric)
        self.received_datasets.append(source_dataset)
        return MetricResult[object](metric=self.metric, value=self._value)


class FailingCalculator(RecordingCalculator):
    def __init__(
        self,
        metric: MetricType,
        error: Exception,
        execution_log: list[MetricType],
    ) -> None:
        super().__init__(metric, None, execution_log)
        self._error = error

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[object]:
        self._execution_log.append(self.metric)
        self.received_datasets.append(source_dataset)
        raise self._error


def _dataset() -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=[Video(id="video-1", channel_id="channel-1", title="Video")],
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )


class CalculatorRegistryTests(unittest.TestCase):
    def test_empty_registry_returns_empty_results(self) -> None:
        registry = CalculatorRegistry(())

        self.assertEqual(registry.calculate_all(_dataset()), ())

    def test_registered_calculators_execute_once_in_registration_order(self) -> None:
        execution_log: list[MetricType] = []
        first = RecordingCalculator(MetricType.CHANNEL_AGE, 10, execution_log)
        second = RecordingCalculator(MetricType.AVERAGE_VIEWS, 20.0, execution_log)
        registry = CalculatorRegistry((first, second))

        results = registry.calculate_all(_dataset())

        self.assertEqual(
            execution_log,
            [MetricType.CHANNEL_AGE, MetricType.AVERAGE_VIEWS],
        )
        self.assertEqual([result.metric for result in results], execution_log)
        self.assertEqual([result.value for result in results], [10, 20.0])
        self.assertIsInstance(results, tuple)
        self.assertEqual(len(first.received_datasets), 1)
        self.assertEqual(len(second.received_datasets), 1)

    def test_registry_owns_a_snapshot_of_the_registered_sequence(self) -> None:
        execution_log: list[MetricType] = []
        first = RecordingCalculator(MetricType.CHANNEL_AGE, 10, execution_log)
        second = RecordingCalculator(MetricType.AVERAGE_VIEWS, 20.0, execution_log)
        calculators = [first]
        registry = CalculatorRegistry(calculators)

        calculators.append(second)
        results = registry.calculate_all(_dataset())

        self.assertEqual(
            [result.metric for result in results],
            [MetricType.CHANNEL_AGE],
        )

    def test_calculators_receive_same_dataset_instance(self) -> None:
        execution_log: list[MetricType] = []
        first = RecordingCalculator(MetricType.CHANNEL_AGE, 10, execution_log)
        second = RecordingCalculator(MetricType.AVERAGE_VIEWS, 20.0, execution_log)
        registry = CalculatorRegistry((first, second))
        dataset = _dataset()

        registry.calculate_all(dataset)

        self.assertIs(first.received_datasets[0], dataset)
        self.assertIs(second.received_datasets[0], dataset)

    def test_duplicate_metric_is_rejected_at_construction(self) -> None:
        execution_log: list[MetricType] = []
        first = RecordingCalculator(MetricType.CHANNEL_AGE, 10, execution_log)
        duplicate = RecordingCalculator(MetricType.CHANNEL_AGE, 20, execution_log)

        with self.assertRaisesRegex(
            DuplicateCalculatorError,
            "duplicate calculator registered for metric 'channel_age'",
        ):
            CalculatorRegistry((first, duplicate))

        self.assertEqual(execution_log, [])

    def test_failure_propagates_and_stops_execution(self) -> None:
        execution_log: list[MetricType] = []
        expected_error = RuntimeError("calculation failed")
        first = RecordingCalculator(MetricType.CHANNEL_AGE, 10, execution_log)
        failing = FailingCalculator(
            MetricType.AVERAGE_VIEWS,
            expected_error,
            execution_log,
        )
        last = RecordingCalculator(MetricType.MEDIAN_VIEWS, 30.0, execution_log)
        registry = CalculatorRegistry((first, failing, last))

        with self.assertRaises(RuntimeError) as raised:
            registry.calculate_all(_dataset())

        self.assertIs(raised.exception, expected_error)
        self.assertEqual(
            execution_log,
            [MetricType.CHANNEL_AGE, MetricType.AVERAGE_VIEWS],
        )

    def test_registry_is_stateless_across_executions(self) -> None:
        execution_log: list[MetricType] = []
        calculator = RecordingCalculator(MetricType.CHANNEL_AGE, 10, execution_log)
        registry = CalculatorRegistry((calculator,))
        dataset = _dataset()

        first_results = registry.calculate_all(dataset)
        second_results = registry.calculate_all(dataset)

        self.assertEqual(first_results, second_results)
        self.assertEqual(
            execution_log,
            [MetricType.CHANNEL_AGE, MetricType.CHANNEL_AGE],
        )

    def test_additional_calculator_requires_only_constructor_registration(self) -> None:
        execution_log: list[MetricType] = []
        calculators = (
            RecordingCalculator(MetricType.CHANNEL_AGE, 10, execution_log),
            RecordingCalculator(MetricType.AVERAGE_VIEWS, 20.0, execution_log),
            RecordingCalculator(MetricType.MEDIAN_VIEWS, 15.0, execution_log),
        )

        results = CalculatorRegistry(calculators).calculate_all(_dataset())

        self.assertEqual(
            [result.metric for result in results],
            [calculator.metric for calculator in calculators],
        )

    def test_registry_accepts_all_production_calculator_result_types(self) -> None:
        calculated_at = datetime(2026, 7, 21, tzinfo=UTC)
        calculators: tuple[AnalyticsCalculator[object], ...] = (
            ChannelAgeCalculator(clock=lambda: calculated_at),
            UploadFrequencyCalculator(),
            AverageViewsCalculator(),
            MedianViewsCalculator(),
            ViewsPerDayCalculator(clock=lambda: calculated_at),
            ViewDistributionCalculator(),
            UploadConsistencyCalculator(),
            ViewOutlierCalculator(),
            ViewGrowthRateCalculator(),
            ViewEngagementRateCalculator(),
        )
        dataset = ChannelAnalytics(
            channel=Channel(
                id="channel-1",
                title="Channel",
                published_at=calculated_at - timedelta(days=365),
            ),
            videos=[
                Video(
                    id=f"video-{index}",
                    channel_id="channel-1",
                    title="Video",
                    published_at=calculated_at - timedelta(days=index + 1),
                    view_count=(index + 1) * 100,
                    like_count=(index + 1) * 10,
                    comment_count=index + 1,
                )
                for index in range(3)
            ],
            generated_at=calculated_at,
        )

        results = CalculatorRegistry(calculators).calculate_all(dataset)

        self.assertEqual(
            tuple(result.metric for result in results),
            tuple(calculator.metric for calculator in calculators),
        )


if __name__ == "__main__":
    unittest.main()
