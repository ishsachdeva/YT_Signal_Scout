"""Explicit orchestration for deterministic analytics calculators."""

from __future__ import annotations

from collections.abc import Sequence

from app.services.analytics.exceptions import DuplicateCalculatorError
from app.services.analytics.interfaces import AnalyticsCalculator
from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType


class CalculatorRegistry:
    """Execute an explicitly ordered collection of deterministic calculators."""

    def __init__(self, calculators: Sequence[AnalyticsCalculator[object]]) -> None:
        self._calculators = tuple(calculators)
        self._validate_unique_metrics()

    def calculate_all(
        self, source_dataset: ChannelAnalytics
    ) -> tuple[MetricResult[object], ...]:
        """Execute every calculator once in registration order."""
        return tuple(
            calculator.calculate(source_dataset)
            for calculator in self._calculators
        )

    def _validate_unique_metrics(self) -> None:
        registered_metrics: set[MetricType] = set()
        for calculator in self._calculators:
            if calculator.metric in registered_metrics:
                raise DuplicateCalculatorError(
                    f"duplicate calculator registered for metric "
                    f"'{calculator.metric.value}'"
                )
            registered_metrics.add(calculator.metric)
