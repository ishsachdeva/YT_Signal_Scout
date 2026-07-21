"""Deterministic channel age calculator."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ChannelAgeCalculator:
    """Calculate whole elapsed days since a channel was published."""

    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock

    @property
    def metric(self) -> MetricType:
        return MetricType.CHANNEL_AGE

    def calculate(self, source_dataset: ChannelAnalytics) -> MetricResult[int]:
        """Return the channel age in whole elapsed days."""
        published_at = source_dataset.channel.published_at
        calculated_at = self._clock()
        self._validate_inputs(published_at, calculated_at)
        return MetricResult[int](
            metric=self.metric,
            value=(calculated_at - cast(datetime, published_at)).days,
        )

    @staticmethod
    def _validate_inputs(
        published_at: datetime | None, calculated_at: datetime
    ) -> None:
        if published_at is None:
            raise AnalyticsValidationError("channel publication date is required")
        if published_at.tzinfo is None or published_at.utcoffset() is None:
            raise AnalyticsValidationError("channel publication date must be timezone-aware")
        if calculated_at.tzinfo is None or calculated_at.utcoffset() is None:
            raise AnalyticsValidationError("calculator clock must be timezone-aware")
        if published_at > calculated_at:
            raise AnalyticsValidationError("channel publication date cannot be in the future")
