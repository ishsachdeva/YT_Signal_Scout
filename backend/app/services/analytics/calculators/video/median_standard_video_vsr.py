"""Deterministic median standard-video view-to-subscriber ratio calculator."""

from __future__ import annotations

from statistics import median
from typing import cast

from app.services.analytics.eligibility import EligibleVideoClassification
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import MetricResult, MetricType
from app.services.youtube.models import Video


class MedianStandardVideoVsrCalculator:
    """Calculate median VSR from a completed standard-video basis."""

    @property
    def metric(self) -> MetricType:
        return MetricType.MEDIAN_STANDARD_VIDEO_VSR

    def calculate(
        self,
        classification: EligibleVideoClassification,
        subscriber_count: int | None,
    ) -> MetricResult[float | None]:
        """Return the unrounded median VSR or unavailable value."""
        self._validate_classification(classification)
        self._validate_subscriber_count(subscriber_count)

        standard_videos = classification.eligible_standard_videos
        if not standard_videos or subscriber_count is None or subscriber_count == 0:
            value = None
        else:
            value = float(
                median(
                    cast(int, video.view_count) / subscriber_count
                    for video in standard_videos
                )
            )

        return MetricResult[float | None](metric=self.metric, value=value)

    @staticmethod
    def _validate_classification(
        classification: EligibleVideoClassification,
    ) -> None:
        if classification is None:
            raise AnalyticsValidationError("eligible video classification is required")
        if not isinstance(classification, EligibleVideoClassification):
            raise AnalyticsValidationError(
                "classification must be EligibleVideoClassification"
            )
        if not isinstance(classification.eligible_standard_videos, tuple) or not all(
            isinstance(video, Video)
            for video in classification.eligible_standard_videos
        ):
            raise AnalyticsValidationError(
                "eligible standard videos must be a tuple of Video objects"
            )
        for video in classification.eligible_standard_videos:
            if video.view_count is None:
                raise AnalyticsValidationError("eligible video view count is required")
            if isinstance(video.view_count, bool) or not isinstance(
                video.view_count,
                int,
            ):
                raise AnalyticsValidationError(
                    "eligible video view count must be an integer"
                )
            if video.view_count < 0:
                raise AnalyticsValidationError(
                    "eligible video view count cannot be negative"
                )

    @staticmethod
    def _validate_subscriber_count(subscriber_count: int | None) -> None:
        if isinstance(subscriber_count, bool) or (
            subscriber_count is not None and not isinstance(subscriber_count, int)
        ):
            raise AnalyticsValidationError(
                "subscriber count must be an integer or None"
            )
        if subscriber_count is not None and subscriber_count < 0:
            raise AnalyticsValidationError("subscriber count cannot be negative")
