"""Service for constructing validated analytics datasets."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import ChannelAnalytics
from app.services.youtube.models import Channel, Video


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AnalyticsService:
    """Validate typed source data and build channel analytics datasets."""

    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock

    def build_channel_analytics(
        self, channel: Channel, videos: list[Video]
    ) -> ChannelAnalytics:
        """Build an analytics dataset without calculating metrics or scores."""
        self._validate_channel(channel)
        self._validate_videos(videos)
        generated_at = self._clock()
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise AnalyticsValidationError("generated_at must be timezone-aware")
        return ChannelAnalytics(
            channel=channel,
            videos=list(videos),
            generated_at=generated_at,
        )

    @staticmethod
    def _validate_channel(channel: Channel) -> None:
        if not isinstance(channel, Channel):
            raise AnalyticsValidationError("channel must be a Channel")
        if not channel.id.strip():
            raise AnalyticsValidationError("channel id must not be empty")

    @staticmethod
    def _validate_videos(videos: list[Video]) -> None:
        if not isinstance(videos, list):
            raise AnalyticsValidationError("videos must be a list of Video objects")
        if not videos:
            raise AnalyticsValidationError(
                "Cannot build analytics for a channel with no videos"
            )
        if not all(isinstance(video, Video) for video in videos):
            raise AnalyticsValidationError("videos must contain only Video objects")
