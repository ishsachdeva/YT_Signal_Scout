"""Typed service layer for public YouTube data acquisition."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from app.services.youtube.client import JsonObject, YouTubeClient
from app.services.youtube.exceptions import (
    ChannelNotFoundError,
    VideoNotFoundError,
    YouTubeAPIError,
)
from app.services.youtube.models import (
    Channel,
    ChannelStatistics,
    LiveState,
    PageInfo,
    PrivacyStatus,
    SearchResult,
    Thumbnail,
    Video,
    VideoAvailability,
    VideoFormat,
)

_DURATION_PATTERN = re.compile(
    r"^P(?:(?P<days>\d+)D)?"
    r"(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$"
)
_STANDARD_VIDEO_MINIMUM_DURATION = timedelta(minutes=3)


class YouTubeService:
    """Convert YouTube API payloads into stable application models."""

    def __init__(self, client: YouTubeClient) -> None:
        self._client = client

    def search_channels(
        self,
        query: str,
        *,
        page_token: str | None = None,
        page_size: int | None = None,
        region_code: str | None = None,
        relevance_language: str | None = None,
    ) -> SearchResult:
        """Search for public channels matching a query."""
        payload = self._client.search(
            query=query,
            resource_type="channel",
            max_results=self._page_size(page_size),
            page_token=page_token,
            region_code=region_code,
            relevance_language=relevance_language,
        )
        return self._parse_result(payload, self._parse_channel)

    def search_videos(
        self,
        query: str,
        *,
        page_token: str | None = None,
        page_size: int | None = None,
        region_code: str | None = None,
        relevance_language: str | None = None,
    ) -> SearchResult:
        """Search for public videos matching a query."""
        payload = self._client.search(
            query=query,
            resource_type="video",
            max_results=self._page_size(page_size),
            page_token=page_token,
            region_code=region_code,
            relevance_language=relevance_language,
        )
        return self._parse_result(payload, self._parse_video)

    def get_channel(self, channel_id: str) -> Channel:
        """Retrieve public metadata, statistics, and uploads ID for one channel."""
        payload = self._client.get_channels(
            [channel_id], parts=("snippet", "statistics", "contentDetails")
        )
        items = self._items(payload)
        if not items:
            raise ChannelNotFoundError(f"YouTube channel '{channel_id}' was not found")
        return self._parse_channel(items[0])

    def get_video(self, video_id: str) -> Video:
        """Retrieve public metadata, statistics, and content details for one video."""
        payload = self._client.get_videos(
            [video_id],
            parts=(
                "snippet",
                "statistics",
                "contentDetails",
                "status",
                "liveStreamingDetails",
            ),
        )
        items = self._items(payload)
        if not items:
            raise VideoNotFoundError(f"YouTube video '{video_id}' was not found")
        return self._parse_video_resource(items[0])

    def get_channel_statistics(self, channel_id: str) -> ChannelStatistics:
        """Retrieve the current public statistics for one channel."""
        payload = self._client.get_channels([channel_id], parts=("statistics",))
        items = self._items(payload)
        if not items:
            raise ChannelNotFoundError(f"YouTube channel '{channel_id}' was not found")
        return self._parse_statistics(self._mapping(items[0].get("statistics")))

    def list_channel_videos(
        self,
        channel_id: str,
        *,
        max_pages: int = 1,
        page_size: int | None = None,
    ) -> SearchResult:
        """List a bounded number of pages from a channel's uploads playlist."""
        if max_pages < 1:
            raise ValueError("max_pages must be one or greater")
        channel = self.get_channel(channel_id)
        if channel.uploads_playlist_id is None:
            raise YouTubeAPIError("YouTube response did not include an uploads playlist")

        size = self._page_size(page_size)
        collected: list[Channel | Video] = []
        page_token: str | None = None
        previous_page_token: str | None = None
        total_results = 0
        for _ in range(max_pages):
            payload = self._client.list_playlist_items(
                playlist_id=channel.uploads_playlist_id,
                max_results=size,
                page_token=page_token,
            )
            collected.extend(self._parse_video(item) for item in self._items(payload))
            total_results = self._page_info(payload).total_results
            previous_page_token = self._optional_string(payload.get("prevPageToken"))
            page_token = self._optional_string(payload.get("nextPageToken"))
            if page_token is None:
                break

        return SearchResult(
            items=tuple(collected),
            page_info=PageInfo(total_results=total_results, results_per_page=len(collected)),
            next_page_token=page_token,
            previous_page_token=previous_page_token,
        )

    def _page_size(self, requested: int | None) -> int:
        return self._client.page_size if requested is None else requested

    def _parse_result(
        self,
        payload: JsonObject,
        parser: Callable[[JsonObject], Channel | Video],
    ) -> SearchResult:
        return SearchResult(
            items=tuple(parser(item) for item in self._items(payload)),
            page_info=self._page_info(payload),
            next_page_token=self._optional_string(payload.get("nextPageToken")),
            previous_page_token=self._optional_string(payload.get("prevPageToken")),
        )

    @classmethod
    def _parse_channel(cls, item: JsonObject) -> Channel:
        snippet = cls._mapping(item.get("snippet"))
        identifier = item.get("id")
        if isinstance(identifier, Mapping):
            identifier = identifier.get("channelId")
        content_details = cls._mapping(item.get("contentDetails"))
        playlists = cls._mapping(content_details.get("relatedPlaylists"))
        statistics_value = item.get("statistics")
        return Channel(
            id=cls._required_string(identifier, "channel id"),
            title=cls._required_string(snippet.get("title"), "channel title"),
            description=cls._optional_string(snippet.get("description")) or "",
            custom_url=cls._optional_string(snippet.get("customUrl")),
            country=cls._optional_string(snippet.get("country")),
            published_at=cls._datetime(snippet.get("publishedAt")),
            thumbnails=cls._thumbnails(snippet.get("thumbnails")),
            uploads_playlist_id=cls._optional_string(playlists.get("uploads")),
            statistics=(
                cls._parse_statistics(cls._mapping(statistics_value))
                if statistics_value is not None
                else None
            ),
        )

    @classmethod
    def _parse_video(cls, item: JsonObject) -> Video:
        return cls._build_video(item)

    @classmethod
    def _parse_video_resource(cls, item: JsonObject) -> Video:
        """Parse one complete videos.list resource into canonical facts."""
        snippet = cls._mapping(item.get("snippet"))
        statistics = cls._mapping(item.get("statistics"))
        content_details = cls._mapping(item.get("contentDetails"))
        status = cls._mapping(item.get("status"))
        live_details = cls._mapping(item.get("liveStreamingDetails"))

        duration = cls._duration(content_details.get("duration"))
        live_state = cls._live_state(snippet, live_details)
        return cls._build_video(
            item,
            tags=cls._string_tuple(snippet.get("tags"), "video tags"),
            category_id=cls._optional_string(snippet.get("categoryId")),
            default_language=cls._optional_string(snippet.get("defaultLanguage")),
            like_count=cls._optional_integer(statistics.get("likeCount")),
            comment_count=cls._optional_integer(statistics.get("commentCount")),
            duration=duration,
            privacy_status=cls._privacy_status(status.get("privacyStatus")),
            availability=cls._availability(status.get("uploadStatus")),
            live_state=live_state,
            video_format=cls._video_format(live_state, duration),
        )

    @classmethod
    def _build_video(
        cls,
        item: JsonObject,
        *,
        tags: tuple[str, ...] = (),
        category_id: str | None = None,
        default_language: str | None = None,
        like_count: int | None = None,
        comment_count: int | None = None,
        duration: timedelta | None = None,
        privacy_status: PrivacyStatus | None = None,
        availability: VideoAvailability = VideoAvailability.UNKNOWN,
        live_state: LiveState = LiveState.UNKNOWN,
        video_format: VideoFormat = VideoFormat.UNKNOWN,
    ) -> Video:
        snippet = cls._mapping(item.get("snippet"))
        identifier = item.get("id")
        if isinstance(identifier, Mapping):
            identifier = identifier.get("videoId")
        if not identifier:
            identifier = cls._mapping(item.get("contentDetails")).get("videoId")
        if not identifier:
            identifier = cls._mapping(snippet.get("resourceId")).get("videoId")
        return Video(
            id=cls._required_string(identifier, "video id"),
            channel_id=cls._required_string(snippet.get("channelId"), "video channel id"),
            channel_title=cls._optional_string(snippet.get("channelTitle")),
            title=cls._required_string(snippet.get("title"), "video title"),
            description=cls._optional_string(snippet.get("description")) or "",
            tags=tags,
            category_id=category_id,
            default_language=default_language,
            published_at=cls._datetime(snippet.get("publishedAt")),
            view_count=cls._optional_integer(
                cls._mapping(item.get("statistics")).get("viewCount")
            ),
            like_count=like_count,
            comment_count=comment_count,
            duration=duration,
            privacy_status=privacy_status,
            availability=availability,
            live_state=live_state,
            format=video_format,
            thumbnails=cls._thumbnails(snippet.get("thumbnails")),
        )

    @staticmethod
    def _duration(value: object) -> timedelta | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise YouTubeAPIError("YouTube response contained an invalid video duration")
        match = _DURATION_PATTERN.fullmatch(value)
        if match is None or not any(match.groupdict().values()):
            raise YouTubeAPIError("YouTube response contained an invalid video duration")

        seconds = Decimal(match.group("seconds") or "0")
        microseconds = seconds * 1_000_000
        if microseconds != microseconds.to_integral_value():
            raise YouTubeAPIError("YouTube response contained an invalid video duration")
        try:
            return timedelta(
                days=int(match.group("days") or 0),
                hours=int(match.group("hours") or 0),
                minutes=int(match.group("minutes") or 0),
                microseconds=int(microseconds),
            )
        except OverflowError as exception:
            raise YouTubeAPIError(
                "YouTube response contained an invalid video duration"
            ) from exception

    @staticmethod
    def _privacy_status(value: object) -> PrivacyStatus | None:
        try:
            return PrivacyStatus(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _availability(value: object) -> VideoAvailability:
        if value == "deleted":
            return VideoAvailability.DELETED
        if value in {None, "processed"}:
            return VideoAvailability.AVAILABLE
        return VideoAvailability.UNKNOWN

    @classmethod
    def _live_state(
        cls,
        snippet: Mapping[str, Any],
        live_details: Mapping[str, Any],
    ) -> LiveState:
        broadcast_content = snippet.get("liveBroadcastContent")
        actual_start = cls._datetime(live_details.get("actualStartTime"))
        actual_end = cls._datetime(live_details.get("actualEndTime"))
        scheduled_start = cls._datetime(live_details.get("scheduledStartTime"))

        if actual_end is not None:
            if actual_start is None or broadcast_content in {"live", "upcoming"}:
                return LiveState.UNKNOWN
            return LiveState.COMPLETE
        if broadcast_content == "live":
            return LiveState.LIVE if actual_start is not None else LiveState.UNKNOWN
        if broadcast_content == "upcoming":
            if actual_start is None and scheduled_start is not None:
                return LiveState.UPCOMING
            return LiveState.UNKNOWN
        if broadcast_content == "none":
            if actual_start is None and scheduled_start is None:
                return LiveState.NOT_LIVE
            return LiveState.UNKNOWN
        return LiveState.UNKNOWN

    @staticmethod
    def _video_format(
        live_state: LiveState,
        duration: timedelta | None,
    ) -> VideoFormat:
        if live_state is LiveState.COMPLETE:
            return VideoFormat.LIVE_REPLAY
        if (
            live_state is LiveState.NOT_LIVE
            and duration is not None
            and duration > _STANDARD_VIDEO_MINIMUM_DURATION
        ):
            return VideoFormat.STANDARD
        return VideoFormat.UNKNOWN

    @staticmethod
    def _string_tuple(value: object, field: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise YouTubeAPIError(f"YouTube response contained invalid {field}")
        return tuple(value)

    @classmethod
    def _parse_statistics(cls, value: Mapping[str, Any]) -> ChannelStatistics:
        hidden = bool(value.get("hiddenSubscriberCount", False))
        subscriber_value = value.get("subscriberCount")
        return ChannelStatistics(
            view_count=cls._integer(value.get("viewCount"), "view count"),
            subscriber_count=(
                None
                if hidden or subscriber_value is None
                else cls._integer(subscriber_value, "subscriber count")
            ),
            subscriber_count_hidden=hidden,
            video_count=cls._integer(value.get("videoCount"), "video count"),
        )

    @classmethod
    def _thumbnails(cls, value: object) -> tuple[Thumbnail, ...]:
        thumbnails = cls._mapping(value)
        parsed: list[Thumbnail] = []
        for size, raw in thumbnails.items():
            data = cls._mapping(raw)
            if not isinstance(size, str) or not data:
                continue
            parsed.append(
                Thumbnail(
                    url=cls._required_string(data.get("url"), "thumbnail URL"),
                    size=size,
                    width=cls._optional_integer(data.get("width")),
                    height=cls._optional_integer(data.get("height")),
                )
            )
        return tuple(parsed)

    @classmethod
    def _page_info(cls, payload: JsonObject) -> PageInfo:
        value = cls._mapping(payload.get("pageInfo"))
        return PageInfo(
            total_results=cls._integer(value.get("totalResults", 0), "total results"),
            results_per_page=cls._integer(
                value.get("resultsPerPage", len(cls._items(payload))), "results per page"
            ),
        )

    @staticmethod
    def _items(payload: JsonObject) -> list[JsonObject]:
        items = payload.get("items", [])
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            raise YouTubeAPIError("YouTube response contained invalid items")
        return items

    @staticmethod
    def _mapping(value: object) -> Mapping[str, Any]:
        return value if isinstance(value, Mapping) else {}

    @staticmethod
    def _required_string(value: object, field: str) -> str:
        if not isinstance(value, str) or not value:
            raise YouTubeAPIError(f"YouTube response did not include {field}")
        return value

    @staticmethod
    def _optional_string(value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _integer(value: object, field: str) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exception:
            raise YouTubeAPIError(
                f"YouTube response contained an invalid {field}"
            ) from exception

    @staticmethod
    def _optional_integer(value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _datetime(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exception:
            raise YouTubeAPIError(
                "YouTube response contained an invalid timestamp"
            ) from exception
