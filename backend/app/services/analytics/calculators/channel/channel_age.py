"""Deterministic channel age calculator."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.analytics.validation import (
    validate_channel_publication_date,
    validate_clock,
)


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
        validate_channel_publication_date(published_at)
        validate_clock(calculated_at)
        self._validate_not_future(cast(datetime, published_at), calculated_at)
        return MetricResult[int](
            metric=self.metric,
            value=(calculated_at - cast(datetime, published_at)).days,
        )

    @staticmethod
    def _validate_not_future(published_at: datetime, calculated_at: datetime) -> None:
        if published_at > calculated_at:
            raise AnalyticsValidationError("channel publication date cannot be in the future")
