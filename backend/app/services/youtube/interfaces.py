"""Provider-neutral contract for public video-platform acquisition."""

from __future__ import annotations

from typing import Protocol

from app.services.youtube.models import Channel, ChannelStatistics, SearchResult, Video


class VideoPlatformService(Protocol):
    """Contract implemented by public video-platform data providers."""

    def search_channels(
        self, query: str, *, page_token: str | None = None, page_size: int | None = None
    ) -> SearchResult: ...

    def search_videos(
        self, query: str, *, page_token: str | None = None, page_size: int | None = None
    ) -> SearchResult: ...

    def get_channel(self, channel_id: str) -> Channel: ...

    def get_video(self, video_id: str) -> Video: ...

    def get_channel_statistics(self, channel_id: str) -> ChannelStatistics: ...

    def list_channel_videos(
        self, channel_id: str, *, max_pages: int = 1, page_size: int | None = None
    ) -> SearchResult: ...
