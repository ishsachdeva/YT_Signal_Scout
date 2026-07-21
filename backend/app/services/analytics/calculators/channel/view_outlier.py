"""Deterministic video view-count outlier calculator."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import cast

from app.services.analytics.models import (
    ChannelAnalytics,
    MetricResult,
    MetricType,
    OutlierResult,
)
from app.services.analytics.validation import (
    validate_source_dataset,
    validate_video_collection,
    validate_view_counts,
)


class ViewOutlierCalculator:
    """Identify the highest and lowest population z-scores by video views."""

    @property
    def metric(self) -> MetricType:
        return MetricType.VIEW_OUTLIER

    def calculate(
        self, source_dataset: ChannelAnalytics
    ) -> MetricResult[OutlierResult]:
        """Return the videos with the largest positive and negative z-scores."""
        validate_source_dataset(source_dataset)
        validate_video_collection(source_dataset)
        validate_view_counts(source_dataset)

        no_outliers = OutlierResult(
            highest_video_id=None,
            highest_z_score=0.0,
            lowest_video_id=None,
            lowest_z_score=0.0,
        )
        if len(source_dataset.videos) == 1:
            return MetricResult[OutlierResult](metric=self.metric, value=no_outliers)

        view_counts = [cast(int, video.view_count) for video in source_dataset.videos]
        mean_view_count = mean(view_counts)
        standard_deviation = pstdev(view_counts)
        if standard_deviation == 0:
            return MetricResult[OutlierResult](metric=self.metric, value=no_outliers)

        z_scores = [
            (view_count - mean_view_count) / standard_deviation
            for view_count in view_counts
        ]
        highest_index = max(range(len(z_scores)), key=z_scores.__getitem__)
        lowest_index = min(range(len(z_scores)), key=z_scores.__getitem__)
        result = OutlierResult(
            highest_video_id=source_dataset.videos[highest_index].id,
            highest_z_score=z_scores[highest_index],
            lowest_video_id=source_dataset.videos[lowest_index].id,
            lowest_z_score=z_scores[lowest_index],
        )
        return MetricResult[OutlierResult](metric=self.metric, value=result)
