"""Application-facing models for public YouTube data."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PrivacyStatus(StrEnum):
    """Canonical visibility states for a YouTube video."""

    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class VideoAvailability(StrEnum):
    """Canonical availability states for a YouTube video."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DELETED = "deleted"
    UNKNOWN = "unknown"


class LiveState(StrEnum):
    """Canonical live-broadcast states for a YouTube video."""

    NOT_LIVE = "not_live"
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class VideoFormat(StrEnum):
    """Canonical content formats used by format-specific analytics."""

    SHORT = "short"
    STANDARD = "standard"
    LIVE_REPLAY = "live_replay"
    UNKNOWN = "unknown"


class Thumbnail(BaseModel):
    """A public thumbnail variant for a channel or video."""

    model_config = ConfigDict(frozen=True)

    url: str
    size: str
    width: int | None = None
    height: int | None = None


class ChannelStatistics(BaseModel):
    """Public counters reported for a YouTube channel."""

    model_config = ConfigDict(frozen=True)

    view_count: int = Field(ge=0)
    subscriber_count: int | None = Field(default=None, ge=0)
    subscriber_count_hidden: bool
    video_count: int = Field(ge=0)


class Channel(BaseModel):
    """The subset of public channel metadata used by the application."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    description: str = ""
    custom_url: str | None = None
    country: str | None = None
    published_at: datetime | None = None
    thumbnails: tuple[Thumbnail, ...] = ()
    uploads_playlist_id: str | None = None
    statistics: ChannelStatistics | None = None


class Video(BaseModel):
    """The subset of public video metadata used by the application."""

    model_config = ConfigDict(frozen=True)

    id: str
    channel_id: str
    channel_title: str | None = None
    title: str
    description: str = ""
    tags: tuple[str, ...] = ()
    category_id: str | None = None
    default_language: str | None = None
    published_at: datetime | None = None
    view_count: int | None = None
    like_count: int | None = Field(default=None, ge=0)
    comment_count: int | None = Field(default=None, ge=0)
    duration: timedelta | None = None
    privacy_status: PrivacyStatus | None = None
    availability: VideoAvailability = VideoAvailability.UNKNOWN
    live_state: LiveState = LiveState.UNKNOWN
    format: VideoFormat = VideoFormat.UNKNOWN
    thumbnails: tuple[Thumbnail, ...] = ()


class PageInfo(BaseModel):
    """Pagination metadata returned by the upstream API."""

    model_config = ConfigDict(frozen=True)

    total_results: int = Field(ge=0)
    results_per_page: int = Field(ge=0)


class SearchResult(BaseModel):
    """A page or bounded collection of channel/video discovery results."""

    model_config = ConfigDict(frozen=True)

    items: tuple[Channel | Video, ...]
    page_info: PageInfo
    next_page_token: str | None = None
    previous_page_token: str | None = None
