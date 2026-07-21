"""Structural assembly of deterministic analytics results."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from app.services.analytics.exceptions import AnalyticsAssemblyError
from app.services.analytics.models import (
    CalculatedChannelAnalytics,
    ChannelAnalytics,
    MetricResult,
    MetricType,
    OutlierResult,
)

_SUPPORTED_METRICS = frozenset(
    {
        MetricType.CHANNEL_AGE,
        MetricType.UPLOAD_FREQUENCY,
        MetricType.AVERAGE_VIEWS,
        MetricType.MEDIAN_VIEWS,
        MetricType.VIEWS_PER_DAY,
        MetricType.VIEW_DISTRIBUTION,
        MetricType.UPLOAD_CONSISTENCY,
        MetricType.VIEW_OUTLIER,
        MetricType.VIEW_GROWTH_RATE,
        MetricType.VIEW_ENGAGEMENT_RATE,
    }
)


class AnalyticsAssembler:
    """Map a complete metric-result collection into a typed aggregate."""

    def assemble(
        self,
        source_dataset: ChannelAnalytics,
        metric_results: Iterable[MetricResult[object]],
    ) -> CalculatedChannelAnalytics:
        """Validate and assemble one complete deterministic analytics snapshot."""
        results_by_metric = self._index_results(metric_results)
        self._validate_completeness(results_by_metric)
        return CalculatedChannelAnalytics(
            source_dataset=source_dataset,
            channel_age=cast(int, results_by_metric[MetricType.CHANNEL_AGE].value),
            upload_frequency=cast(
                float,
                results_by_metric[MetricType.UPLOAD_FREQUENCY].value,
            ),
            average_views=cast(
                float,
                results_by_metric[MetricType.AVERAGE_VIEWS].value,
            ),
            median_views=cast(
                float,
                results_by_metric[MetricType.MEDIAN_VIEWS].value,
            ),
            views_per_day=cast(
                float,
                results_by_metric[MetricType.VIEWS_PER_DAY].value,
            ),
            view_distribution=cast(
                float,
                results_by_metric[MetricType.VIEW_DISTRIBUTION].value,
            ),
            upload_consistency=cast(
                float,
                results_by_metric[MetricType.UPLOAD_CONSISTENCY].value,
            ),
            view_outlier=cast(
                OutlierResult,
                results_by_metric[MetricType.VIEW_OUTLIER].value,
            ),
            view_growth_rate=cast(
                float,
                results_by_metric[MetricType.VIEW_GROWTH_RATE].value,
            ),
            view_engagement_rate=cast(
                float | None,
                results_by_metric[MetricType.VIEW_ENGAGEMENT_RATE].value,
            ),
        )

    @staticmethod
    def _index_results(
        metric_results: Iterable[MetricResult[object]],
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
