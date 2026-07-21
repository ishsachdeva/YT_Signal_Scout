"""Deterministic upload consistency calculator."""

from __future__ import annotations

from datetime import datetime
from statistics import mean, pstdev
from typing import cast

from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import (
    validate_source_dataset,
    validate_video_collection,
    validate_video_publication_dates,
)

_SECONDS_PER_DAY = 86_400


class UploadConsistencyCalculator:
    """Calculate variation in elapsed days between consecutive uploads."""

    @property
    def metric(self) -> MetricType:
        return MetricType.UPLOAD_CONSISTENCY

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[float]:
        """Return the population coefficient of variation of upload intervals."""
        validate_source_dataset(source_dataset)
        validate_video_collection(source_dataset)
        validate_video_publication_dates(source_dataset)

        if len(source_dataset.videos) == 1:
            return MetricResult[float](metric=self.metric, value=0.0)

        publication_dates = sorted(
            cast(datetime, video.published_at) for video in source_dataset.videos
        )
        intervals = self._compute_intervals(publication_dates)
        mean_interval = mean(intervals)
        if mean_interval == 0:
            return MetricResult[float](metric=self.metric, value=0.0)
        return MetricResult[float](
            metric=self.metric,
            value=pstdev(intervals) / mean_interval,
        )

    @staticmethod
    def _compute_intervals(publication_dates: list[datetime]) -> list[float]:
        return [
            (current - previous).total_seconds() / _SECONDS_PER_DAY
            for previous, current in zip(publication_dates, publication_dates[1:])
        ]
