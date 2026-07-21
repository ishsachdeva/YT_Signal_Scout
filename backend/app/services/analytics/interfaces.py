"""Contract for building typed analytics datasets."""

from __future__ import annotations

from typing import Protocol

from app.services.analytics.models import ChannelAnalytics
from app.services.youtube.models import Channel, Video


class AnalyticsBuilder(Protocol):
    """Contract implemented by analytics dataset builders."""

    def build_channel_analytics(
        self, channel: Channel, videos: list[Video]
    ) -> ChannelAnalytics: ...
