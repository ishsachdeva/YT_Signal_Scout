"""Deterministic lifetime views-per-day calculator."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import (
    validate_clock,
    validate_source_dataset,
    validate_video_collection,
    validate_video_publication_dates,
    validate_view_counts,
)

_SECONDS_PER_DAY = 86_400


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ViewsPerDayCalculator:
    """Calculate mean per-video lifetime views per elapsed day.

    Each video's elapsed age uses a minimum denominator of one day.
    """

    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock

    @property
    def metric(self) -> MetricType:
        return MetricType.VIEWS_PER_DAY

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[float]:
        """Return mean per-video lifetime views per elapsed day."""
        validate_source_dataset(source_dataset)
        validate_video_collection(source_dataset)
        validate_view_counts(source_dataset)
        validate_video_publication_dates(source_dataset)
        calculated_at = self._clock()
        validate_clock(calculated_at)
        self._validate_not_future(source_dataset, calculated_at)

        rates = []
        for video in source_dataset.videos:
            published_at = cast(datetime, video.published_at)
            elapsed_days = max(
                (calculated_at - published_at).total_seconds() / _SECONDS_PER_DAY,
                1.0,
            )
            rates.append(cast(int, video.view_count) / elapsed_days)
        return MetricResult[float](
            metric=self.metric,
            value=sum(rates) / len(rates),
        )

    @staticmethod
    def _validate_not_future(
        source_dataset: ChannelAnalytics, calculated_at: datetime
    ) -> None:
        if any(
            cast(datetime, video.published_at) > calculated_at
            for video in source_dataset.videos
        ):
            raise AnalyticsValidationError(
                "video publication date cannot be in the future"
            )
