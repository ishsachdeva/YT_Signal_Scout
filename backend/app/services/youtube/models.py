"""Application-facing models for public YouTube data."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AcquisitionSource(StrEnum):
    """Closed discovery sources represented by acquisition provenance."""

    SEARCH = "search"
    UPLOADS_PLAYLIST = "uploads_playlist"


class PaginationStatus(StrEnum):
    """Whether one bounded discovery acquisition exhausted pagination."""

    COMPLETE = "complete"
    TRUNCATED = "truncated"


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


class PaginationProvenance(BaseModel):
    """Immutable pagination facts for one video acquisition."""

    model_config = ConfigDict(frozen=True)

    status: PaginationStatus
    pages_fetched: int = Field(ge=1)
    page_size_requested: int = Field(ge=1, le=50)
    page_limit: int = Field(ge=1)
    next_page_token_present: bool
    upstream_total_results: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_status(self) -> PaginationProvenance:
        expected_status = (
            PaginationStatus.TRUNCATED
            if self.next_page_token_present
            else PaginationStatus.COMPLETE
        )
        if self.status is not expected_status:
            raise ValueError("pagination status must match next-page-token presence")
        if self.pages_fetched > self.page_limit:
            raise ValueError("pages fetched must not exceed the page limit")
        return self


class VideoAcquisitionProvenance(BaseModel):
    """Immutable population facts observed during video acquisition."""

    model_config = ConfigDict(frozen=True)

    source: AcquisitionSource
    source_channel_id: str | None = None
    discovery_request_capacity: int = Field(ge=0)
    discovered_position_count: int = Field(ge=0)
    discovered_unique_video_count: int = Field(ge=0)
    enrichment_requested_unique_count: int = Field(ge=0)
    enriched_unique_video_count: int = Field(ge=0)
    enriched_output_position_count: int = Field(ge=0)
    omitted_unique_video_count: int = Field(ge=0)
    pagination: PaginationProvenance

    @model_validator(mode="after")
    def validate_invariants(self) -> VideoAcquisitionProvenance:
        if self.source is AcquisitionSource.UPLOADS_PLAYLIST:
            if not self.source_channel_id:
                raise ValueError("uploads provenance requires a source channel id")
        elif self.source_channel_id is not None:
            raise ValueError("search provenance must not include a source channel id")

        if (
            self.enrichment_requested_unique_count
            != self.discovered_unique_video_count
        ):
            raise ValueError("every discovered unique video must be requested for enrichment")
        if self.enriched_unique_video_count > self.enrichment_requested_unique_count:
            raise ValueError("enriched unique videos must not exceed enrichment requests")
        if self.discovered_unique_video_count > self.discovered_position_count:
            raise ValueError("discovered unique videos must not exceed discovery positions")
        if self.enriched_output_position_count > self.discovered_position_count:
            raise ValueError("enriched output positions must not exceed discovery positions")
        if self.omitted_unique_video_count != (
            self.enrichment_requested_unique_count - self.enriched_unique_video_count
        ):
            raise ValueError("omitted unique videos must match unresolved enrichment requests")
        if self.discovered_position_count > self.discovery_request_capacity:
            raise ValueError("discovery positions must not exceed request capacity")
        return self


class VideoAcquisitionResult(BaseModel):
    """Canonical video acquisition output with complete immutable provenance."""

    model_config = ConfigDict(frozen=True)

    resolved_discovery_videos: tuple[Video, ...]
    unique_canonical_videos: tuple[Video, ...]
    provenance: VideoAcquisitionProvenance

    @model_validator(mode="after")
    def validate_collections(self) -> VideoAcquisitionResult:
        if (
            len(self.resolved_discovery_videos)
            != self.provenance.enriched_output_position_count
        ):
            raise ValueError("resolved discovery videos must match provenance")
        if (
            len(self.unique_canonical_videos)
            != self.provenance.enriched_unique_video_count
        ):
            raise ValueError("unique canonical videos must match provenance")

        unique_ids = tuple(video.id for video in self.unique_canonical_videos)
        if len(set(unique_ids)) != len(unique_ids):
            raise ValueError("unique canonical videos must have unique ids")

        resolved_first_seen: list[str] = []
        seen_ids: set[str] = set()
        for video in self.resolved_discovery_videos:
            if video.id not in seen_ids:
                seen_ids.add(video.id)
                resolved_first_seen.append(video.id)
        if tuple(resolved_first_seen) != unique_ids:
            raise ValueError(
                "unique canonical videos must follow first resolved discovery order"
            )
        return self
