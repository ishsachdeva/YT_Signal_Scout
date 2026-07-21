"""Shared stateless validation for deterministic analytics calculators."""

from __future__ import annotations

from datetime import datetime

from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import ChannelAnalytics


def validate_source_dataset(source_dataset: ChannelAnalytics) -> None:
    """Validate that a calculator received a channel analytics dataset."""
    if source_dataset is None:
        raise AnalyticsValidationError("source dataset is required")
    if not isinstance(source_dataset, ChannelAnalytics):
        raise AnalyticsValidationError("source dataset must be ChannelAnalytics")


def validate_video_collection(source_dataset: ChannelAnalytics) -> None:
    """Validate that a source dataset contains at least one video."""
    if not source_dataset.videos:
        raise AnalyticsValidationError("videos must not be empty")


def validate_view_counts(source_dataset: ChannelAnalytics) -> None:
    """Validate that every video has a non-negative view count."""
    for video in source_dataset.videos:
        if video.view_count is None:
            raise AnalyticsValidationError("video view count is required")
        if video.view_count < 0:
            raise AnalyticsValidationError("video view count cannot be negative")


def validate_channel_publication_date(published_at: datetime | None) -> None:
    """Validate that a channel has a timezone-aware publication date."""
    if published_at is None:
        raise AnalyticsValidationError("channel publication date is required")
    if published_at.tzinfo is None or published_at.utcoffset() is None:
        raise AnalyticsValidationError("channel publication date must be timezone-aware")


def validate_video_publication_dates(source_dataset: ChannelAnalytics) -> None:
    """Validate that every video has a timezone-aware publication date."""
    for video in source_dataset.videos:
        if video.published_at is None:
            raise AnalyticsValidationError("video publication date is required")
        if video.published_at.tzinfo is None or video.published_at.utcoffset() is None:
            raise AnalyticsValidationError(
                "video publication date must be timezone-aware"
            )


def validate_clock(calculated_at: datetime) -> None:
    """Validate that a calculator clock returned a timezone-aware timestamp."""
    if calculated_at.tzinfo is None or calculated_at.utcoffset() is None:
        raise AnalyticsValidationError("calculator clock must be timezone-aware")
