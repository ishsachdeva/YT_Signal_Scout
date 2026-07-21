"""Deterministic historical view growth-rate calculator."""

from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import cast

from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import (
    validate_source_dataset,
    validate_video_collection,
    validate_video_publication_dates,
    validate_view_counts,
)


class ViewGrowthRateCalculator:
    """Compare average views of newer uploads with older uploads."""

    @property
    def metric(self) -> MetricType:
        return MetricType.VIEW_GROWTH_RATE

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[float]:
        """Return the newer-half average divided by the older-half average."""
        validate_source_dataset(source_dataset)
        validate_video_collection(source_dataset)
        validate_video_publication_dates(source_dataset)
        validate_view_counts(source_dataset)

        if len(source_dataset.videos) == 1:
            return MetricResult[float](metric=self.metric, value=1.0)

        ordered_videos = sorted(
            source_dataset.videos,
            key=lambda video: cast(datetime, video.published_at),
        )
        split_index = len(ordered_videos) // 2
        old_average_views = mean(
            cast(int, video.view_count) for video in ordered_videos[:split_index]
        )
        new_average_views = mean(
            cast(int, video.view_count) for video in ordered_videos[split_index:]
        )
        if old_average_views == 0:
            value = 1.0 if new_average_views == 0 else float("inf")
        else:
            value = new_average_views / old_average_views
        return MetricResult[float](metric=self.metric, value=value)
