"""Deterministic upload frequency calculator."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import (
    validate_source_dataset,
    validate_video_collection,
    validate_video_publication_dates,
)

_SECONDS_PER_DAY = 86_400
_DAYS_PER_WEEK = 7


class UploadFrequencyCalculator:
    """Calculate uploads per seven elapsed days in the observed publication window.

    A one-video dataset returns 1.0 because it provides no interval from which to
    infer a cadence.
    """

    @property
    def metric(self) -> MetricType:
        return MetricType.UPLOAD_FREQUENCY

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[float]:
        """Return uploads per seven elapsed days without rounding."""
        validate_source_dataset(source_dataset)
        validate_video_collection(source_dataset)
        validate_video_publication_dates(source_dataset)
        if len(source_dataset.videos) == 1:
            return MetricResult[float](metric=self.metric, value=1.0)

        published_dates = [
            cast(datetime, video.published_at) for video in source_dataset.videos
        ]
        observation_days = max(
            (max(published_dates) - min(published_dates)).total_seconds()
            / _SECONDS_PER_DAY,
            1.0,
        )
        return MetricResult[float](
            metric=self.metric,
            value=len(published_dates) / observation_days * _DAYS_PER_WEEK,
        )
