"""Explicit orchestration for subscriber-relative analytics calculators."""

from __future__ import annotations

from app.services.analytics.calculators.video.eligible_standard_video_count import (
    EligibleStandardVideoCountCalculator,
)
from app.services.analytics.calculators.video.median_standard_video_vsr import (
    MedianStandardVideoVsrCalculator,
)
from app.services.analytics.eligibility import EligibleVideoClassification
from app.services.analytics.exceptions import DuplicateCalculatorError
from app.services.analytics.models import MetricResult


class SubscriberRelativeAnalyticsOrchestrator:
    """Sequence subscriber-relative calculators with explicit typed inputs."""

    def __init__(
        self,
        eligible_standard_video_count_calculator: EligibleStandardVideoCountCalculator,
        median_standard_video_vsr_calculator: MedianStandardVideoVsrCalculator,
    ) -> None:
        self._eligible_standard_video_count_calculator = (
            eligible_standard_video_count_calculator
        )
        self._median_standard_video_vsr_calculator = (
            median_standard_video_vsr_calculator
        )
        self._validate_unique_metrics()

    def calculate_all(
        self,
        classification: EligibleVideoClassification,
        subscriber_count: int | None,
    ) -> tuple[MetricResult[object], ...]:
        """Execute both calculators once in the approved deterministic order."""
        eligible_count = self._eligible_standard_video_count_calculator.calculate(
            classification
        )
        median_vsr = self._median_standard_video_vsr_calculator.calculate(
            classification,
            subscriber_count,
        )
        return (eligible_count, median_vsr)

    def _validate_unique_metrics(self) -> None:
        count_metric = self._eligible_standard_video_count_calculator.metric
        median_metric = self._median_standard_video_vsr_calculator.metric
        if count_metric == median_metric:
            raise DuplicateCalculatorError(
                f"duplicate calculator registered for metric '{count_metric.value}'"
            )
