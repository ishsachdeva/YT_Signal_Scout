"""Deterministic average video views calculator."""

from __future__ import annotations

from typing import cast

from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import (
    validate_source_dataset,
    validate_video_collection,
    validate_view_counts,
)


class AverageViewsCalculator:
    """Calculate the arithmetic mean lifetime view count across all videos."""

    @property
    def metric(self) -> MetricType:
        return MetricType.AVERAGE_VIEWS

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[float]:
        """Return mean lifetime views as an unrounded float."""
        validate_source_dataset(source_dataset)
        validate_video_collection(source_dataset)
        validate_view_counts(source_dataset)
        view_counts = [cast(int, video.view_count) for video in source_dataset.videos]
        return MetricResult[float](
            metric=self.metric,
            value=sum(view_counts) / len(view_counts),
        )
