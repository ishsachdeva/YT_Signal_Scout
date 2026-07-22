"""Deterministic eligible standard-video count calculator."""

from __future__ import annotations

from app.services.analytics.eligibility import EligibleVideoClassification
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import MetricResult, MetricType
from app.services.youtube.models import Video


class EligibleStandardVideoCountCalculator:
    """Count the standard-video basis from a completed classification."""

    @property
    def metric(self) -> MetricType:
        return MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT

    def calculate(
        self,
        classification: EligibleVideoClassification,
    ) -> MetricResult[int]:
        """Return the number of eligible standard videos."""
        self._validate_classification(classification)
        return MetricResult[int](
            metric=self.metric,
            value=len(classification.eligible_standard_videos),
        )

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
