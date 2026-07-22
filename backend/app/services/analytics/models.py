"""Typed models produced by the analytics framework."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from app.services.youtube.models import Channel, Video

MetricValueT = TypeVar("MetricValueT", covariant=True)


class MetricType(str, Enum):
    """Stable identifiers for deterministic analytics metrics."""

    CHANNEL_AGE = "channel_age"
    UPLOAD_FREQUENCY = "upload_frequency"
    AVERAGE_VIEWS = "average_views"
    MEDIAN_VIEWS = "median_views"
    VIEWS_PER_DAY = "views_per_day"
    VIEW_DISTRIBUTION = "view_distribution"
    UPLOAD_CONSISTENCY = "upload_consistency"
    VIEW_OUTLIER = "view_outlier"
    VIEW_GROWTH_RATE = "view_growth_rate"
    VIEW_ENGAGEMENT_RATE = "view_engagement_rate"
    ELIGIBLE_STANDARD_VIDEO_COUNT = "eligible_standard_video_count"
    MEDIAN_STANDARD_VIDEO_VSR = "median_standard_video_vsr"


class ChannelAnalytics(BaseModel):
    """The complete raw analytics dataset for one channel."""

    model_config = ConfigDict(frozen=True)

    channel: Channel
    videos: list[Video]
    generated_at: datetime

    @property
    def video_count(self) -> int:
        return len(self.videos)


class MetricResult(BaseModel, Generic[MetricValueT]):
    """A typed result produced by one deterministic calculator."""

    model_config = ConfigDict(frozen=True)

    metric: MetricType
    value: MetricValueT


class OutlierResult(BaseModel):
    """Most significant high-performing and low-performing video z-scores."""

    model_config = ConfigDict(frozen=True)

    highest_video_id: str | None
    highest_z_score: float
    lowest_video_id: str | None
    lowest_z_score: float


class SubscriberRelativeAnalytics(BaseModel):
    """Completed subscriber-relative analytics result."""

    model_config = ConfigDict(frozen=True)

    eligible_standard_video_count: int
    median_standard_video_vsr: float | None


class CalculatedChannelAnalytics(BaseModel):
    """Complete deterministic analytics derived from a channel dataset."""

    model_config = ConfigDict(frozen=True)

    source_dataset: ChannelAnalytics
    channel_age: int
    upload_frequency: float
    average_views: float
    median_views: float
    views_per_day: float
    view_distribution: float
    upload_consistency: float
    view_outlier: OutlierResult
    view_growth_rate: float
    view_engagement_rate: float | None
