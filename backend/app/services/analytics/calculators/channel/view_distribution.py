"""Deterministic view distribution calculator."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import cast

from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import (
    validate_source_dataset,
    validate_video_collection,
    validate_view_counts,
)


class ViewDistributionCalculator:
    """Calculate population variation in lifetime views across all videos."""

    @property
    def metric(self) -> MetricType:
        return MetricType.VIEW_DISTRIBUTION

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[float]:
        """Return the population coefficient of variation of video view counts."""
        validate_source_dataset(source_dataset)
        validate_video_collection(source_dataset)
        validate_view_counts(source_dataset)

        view_counts = [cast(int, video.view_count) for video in source_dataset.videos]
        mean_view_count = mean(view_counts)
        if mean_view_count == 0:
            return MetricResult[float](metric=self.metric, value=0.0)
        return MetricResult[float](
            metric=self.metric,
            value=pstdev(view_counts) / mean_view_count,
        )
