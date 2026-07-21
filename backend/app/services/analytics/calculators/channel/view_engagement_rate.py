"""Deterministic video engagement-rate calculator."""

from __future__ import annotations

from statistics import mean

from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import validate_source_dataset


class ViewEngagementRateCalculator:
    """Calculate mean engagement rate across eligible channel videos."""

    @property
    def metric(self) -> MetricType:
        return MetricType.VIEW_ENGAGEMENT_RATE

    def calculate(
        self, source_dataset: ChannelAnalytics
    ) -> MetricResult[float | None]:
        """Return the unweighted mean of eligible per-video engagement rates."""
        validate_source_dataset(source_dataset)

        engagement_rates = [
            (video.like_count + video.comment_count) / video.view_count
            for video in source_dataset.videos
            if video.view_count is not None
            and video.view_count > 0
            and video.like_count is not None
            and video.comment_count is not None
        ]
        return MetricResult[float | None](
            metric=self.metric,
            value=mean(engagement_rates) if engagement_rates else None,
        )
