"""Typed models produced by the analytics framework."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from app.services.youtube.models import Channel, Video

MetricValueT = TypeVar("MetricValueT")


class MetricType(str, Enum):
    """Stable identifiers for deterministic analytics metrics."""

    CHANNEL_AGE = "channel_age"
    UPLOAD_FREQUENCY = "upload_frequency"
    AVERAGE_VIEWS = "average_views"
    MEDIAN_VIEWS = "median_views"
    VIEWS_PER_DAY = "views_per_day"
    VIEW_DISTRIBUTION = "view_distribution"
    CONSISTENCY = "consistency"
    OUTLIER = "outlier"
    ENGAGEMENT = "engagement"


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


class CalculatedChannelAnalytics(BaseModel):
    """Deterministic analytics derived from a raw channel dataset."""

    model_config = ConfigDict(frozen=True)

    source_dataset: ChannelAnalytics
