"""Subscriber-relative dataset qualification under ADR-010."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.analytics.eligibility import EligibleVideoClassification
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import SubscriberRelativeAnalytics
from app.services.youtube.models import (
    AcquisitionSource,
    Channel,
    PaginationStatus,
    VideoAcquisitionProvenance,
)

_MINIMUM_ELIGIBLE_STANDARD_VIDEOS = 5
_RESOLUTION_THRESHOLD_NUMERATOR = 3
_RESOLUTION_THRESHOLD_DENOMINATOR = 5


class SubscriberState(StrEnum):
    """Closed canonical subscriber states used by qualification."""

    AVAILABLE_POSITIVE = "available_positive"
    HIDDEN = "hidden"
    UNAVAILABLE = "unavailable"
    NOT_POSITIVE = "not_positive"


class QualificationFailureReason(StrEnum):
    """Ordered normal failures defined by qualification policy v1."""

    ACQUISITION_TRUNCATED = "acquisition_truncated"
    INSUFFICIENT_REQUESTED_ID_RESOLUTION = (
        "insufficient_requested_id_resolution"
    )
    SUBSCRIBER_COUNT_HIDDEN = "subscriber_count_hidden"
    SUBSCRIBER_COUNT_UNAVAILABLE = "subscriber_count_unavailable"
    SUBSCRIBER_COUNT_NOT_POSITIVE = "subscriber_count_not_positive"
    INSUFFICIENT_ELIGIBLE_STANDARD_VIDEOS = (
        "insufficient_eligible_standard_videos"
    )


_FAILURE_ORDER = tuple(QualificationFailureReason)


class SubscriberRelativeQualification(BaseModel):
    """Immutable dataset qualification with typed supporting facts."""

    model_config = ConfigDict(frozen=True)

    qualified: bool
    failures: tuple[QualificationFailureReason, ...]
    provenance: VideoAcquisitionProvenance
    requested_id_resolution_rate: float | None = Field(default=None, ge=0, le=1)
    eligible_standard_video_count: int = Field(ge=0)
    subscriber_state: SubscriberState
    evaluated_at: datetime
    policy_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_result(self) -> SubscriberRelativeQualification:
        if self.qualified != (not self.failures):
            raise ValueError("qualified must be true exactly when failures are empty")
        if len(set(self.failures)) != len(self.failures):
            raise ValueError("qualification failures must be unique")
        positions = tuple(_FAILURE_ORDER.index(reason) for reason in self.failures)
        if positions != tuple(sorted(positions)):
            raise ValueError("qualification failures must follow policy order")
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("qualification evaluation time must be timezone-aware")
        return self


class SubscriberRelativeAnalysisResult(BaseModel):
    """Factual subscriber-relative analytics with its qualification state."""

    model_config = ConfigDict(frozen=True)

    qualification: SubscriberRelativeQualification
    analytics: SubscriberRelativeAnalytics


class SubscriberRelativeQualificationService:
    """Evaluate dataset usability without calculating analytics or signals."""

    def qualify(
        self,
        provenance: VideoAcquisitionProvenance,
        classification: EligibleVideoClassification,
        channel: Channel,
        evaluation_time: datetime,
    ) -> SubscriberRelativeQualification:
        """Return all applicable normal failures in approved deterministic order."""
        self._validate_inputs(provenance, classification, channel, evaluation_time)

        eligible_count = len(classification.eligible_standard_videos)
        subscriber_state = self._subscriber_state(channel)
        resolution_rate = self._resolution_rate(provenance)
        failures: list[QualificationFailureReason] = []

        if provenance.pagination.status is PaginationStatus.TRUNCATED:
            failures.append(QualificationFailureReason.ACQUISITION_TRUNCATED)
        if self._resolution_is_insufficient(provenance):
            failures.append(
                QualificationFailureReason.INSUFFICIENT_REQUESTED_ID_RESOLUTION
            )
        if subscriber_state is SubscriberState.HIDDEN:
            failures.append(QualificationFailureReason.SUBSCRIBER_COUNT_HIDDEN)
        elif subscriber_state is SubscriberState.UNAVAILABLE:
            failures.append(QualificationFailureReason.SUBSCRIBER_COUNT_UNAVAILABLE)
        elif subscriber_state is SubscriberState.NOT_POSITIVE:
            failures.append(QualificationFailureReason.SUBSCRIBER_COUNT_NOT_POSITIVE)
        if eligible_count < _MINIMUM_ELIGIBLE_STANDARD_VIDEOS:
            failures.append(
                QualificationFailureReason.INSUFFICIENT_ELIGIBLE_STANDARD_VIDEOS
            )

        failure_tuple = tuple(failures)
        return SubscriberRelativeQualification(
            qualified=not failure_tuple,
            failures=failure_tuple,
            provenance=provenance,
            requested_id_resolution_rate=resolution_rate,
            eligible_standard_video_count=eligible_count,
            subscriber_state=subscriber_state,
            evaluated_at=evaluation_time,
        )

    @staticmethod
    def _validate_inputs(
        provenance: VideoAcquisitionProvenance,
        classification: EligibleVideoClassification,
        channel: Channel,
        evaluation_time: datetime,
    ) -> None:
        if not isinstance(provenance, VideoAcquisitionProvenance):
            raise AnalyticsValidationError("acquisition provenance is required")
        if provenance.source is not AcquisitionSource.UPLOADS_PLAYLIST:
            raise AnalyticsValidationError(
                "subscriber-relative qualification requires uploads provenance"
            )
        if not isinstance(channel, Channel):
            raise AnalyticsValidationError("canonical channel is required")
        if provenance.source_channel_id != channel.id:
            raise AnalyticsValidationError(
                "acquisition provenance channel must match the canonical channel"
            )
        if not isinstance(classification, EligibleVideoClassification):
            raise AnalyticsValidationError("eligible video classification is required")
        if not isinstance(evaluation_time, datetime):
            raise AnalyticsValidationError("evaluation time must be a datetime")
        if evaluation_time.tzinfo is None or evaluation_time.utcoffset() is None:
            raise AnalyticsValidationError("evaluation time must be timezone-aware")
        if classification.evaluated_at != evaluation_time:
            raise AnalyticsValidationError(
                "classification evaluation time must match qualification"
            )

    @staticmethod
    def _subscriber_state(channel: Channel) -> SubscriberState:
        statistics = channel.statistics
        if statistics is None:
            return SubscriberState.UNAVAILABLE
        subscriber_count = statistics.subscriber_count
        if statistics.subscriber_count_hidden:
            if subscriber_count is not None:
                raise AnalyticsValidationError(
                    "hidden subscriber count must not include a numeric value"
                )
            return SubscriberState.HIDDEN
        if subscriber_count is None:
            return SubscriberState.UNAVAILABLE
        if subscriber_count < 0:
            raise AnalyticsValidationError("subscriber count must not be negative")
        if subscriber_count == 0:
            return SubscriberState.NOT_POSITIVE
        return SubscriberState.AVAILABLE_POSITIVE

    @staticmethod
    def _resolution_rate(provenance: VideoAcquisitionProvenance) -> float | None:
        denominator = provenance.enrichment_requested_unique_count
        if denominator == 0:
            return None
        return provenance.enriched_unique_video_count / denominator

    @staticmethod
    def _resolution_is_insufficient(
        provenance: VideoAcquisitionProvenance,
    ) -> bool:
        denominator = provenance.enrichment_requested_unique_count
        if denominator == 0:
            return False
        return (
            provenance.enriched_unique_video_count
            * _RESOLUTION_THRESHOLD_DENOMINATOR
            < denominator * _RESOLUTION_THRESHOLD_NUMERATOR
        )
