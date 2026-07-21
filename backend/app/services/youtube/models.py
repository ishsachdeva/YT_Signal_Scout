"""Application-facing models for public YouTube data."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
    published_at: datetime | None = None
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
