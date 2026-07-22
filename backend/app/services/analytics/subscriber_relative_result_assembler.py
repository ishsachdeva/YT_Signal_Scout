"""Structural assembly of subscriber-relative analytics results."""

from __future__ import annotations

from typing import cast

from app.services.analytics.exceptions import AnalyticsAssemblyError
from app.services.analytics.models import (
    MetricResult,
    MetricType,
    SubscriberRelativeAnalytics,
)

_SUPPORTED_METRICS = frozenset(
    {
        MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
        MetricType.MEDIAN_STANDARD_VIDEO_VSR,
    }
)


class SubscriberRelativeResultAssembler:
    """Map a complete metric-result tuple into a typed aggregate."""

    def assemble(
        self,
        metric_results: tuple[MetricResult[object], ...],
    ) -> SubscriberRelativeAnalytics:
        """Validate and assemble one subscriber-relative analytics result."""
        if not isinstance(metric_results, tuple):
            raise AnalyticsAssemblyError("metric results must be a tuple")

        results_by_metric = self._index_results(metric_results)
        self._validate_completeness(results_by_metric)
        return SubscriberRelativeAnalytics(
            eligible_standard_video_count=cast(
                int,
                results_by_metric[
                    MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT
                ].value,
            ),
            median_standard_video_vsr=cast(
                float | None,
                results_by_metric[MetricType.MEDIAN_STANDARD_VIDEO_VSR].value,
            ),
        )

    @staticmethod
    def _index_results(
        metric_results: tuple[MetricResult[object], ...],
    ) -> dict[MetricType, MetricResult[object]]:
        results_by_metric: dict[MetricType, MetricResult[object]] = {}
        for result in metric_results:
            if not isinstance(result, MetricResult):
                raise AnalyticsAssemblyError(
                    "metric results must contain MetricResult objects"
                )
            if result.metric not in _SUPPORTED_METRICS:
                raise AnalyticsAssemblyError(f"unexpected metric: {result.metric}")
            if result.metric in results_by_metric:
                raise AnalyticsAssemblyError(
                    f"duplicate metric result: {result.metric.value}"
                )
            results_by_metric[result.metric] = result
        return results_by_metric

    @staticmethod
    def _validate_completeness(
        results_by_metric: dict[MetricType, MetricResult[object]],
    ) -> None:
        missing_metrics = _SUPPORTED_METRICS.difference(results_by_metric)
        if missing_metrics:
            names = ", ".join(sorted(metric.value for metric in missing_metrics))
            raise AnalyticsAssemblyError(f"missing required metrics: {names}")
