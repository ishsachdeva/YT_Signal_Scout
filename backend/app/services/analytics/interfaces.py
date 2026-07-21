"""Contract for building typed analytics datasets."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from app.services.analytics.models import ChannelAnalytics, MetricResult, MetricType
from app.services.youtube.models import Channel, Video

MetricValueT_co = TypeVar("MetricValueT_co", covariant=True)


class AnalyticsBuilder(Protocol):
    """Contract implemented by analytics dataset builders."""

    def build_channel_analytics(
        self, channel: Channel, videos: list[Video]
    ) -> ChannelAnalytics: ...


@runtime_checkable
class AnalyticsCalculator(Protocol[MetricValueT_co]):
    """Contract for a deterministic calculator that produces one typed metric."""

    @property
    def metric(self) -> MetricType: ...

    def calculate(
        self, source_dataset: ChannelAnalytics
    ) -> MetricResult[MetricValueT_co]: ...
