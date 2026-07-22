"""Immutable policy-free evidence derived from subscriber-relative analysis."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.analytics.models import MetricType
from app.services.analytics.qualification import (
    QualificationFailureReason,
    SubscriberState,
)
from app.services.youtube.models import VideoAcquisitionProvenance

EvidenceValueT = TypeVar("EvidenceValueT")


class EvidenceFact(StrEnum):
    """Closed identities for evidence facts that are not calculator metrics."""

    QUALIFICATION = "qualification"
    SUBSCRIBER_STATE = "subscriber_state"
    REQUESTED_ID_RESOLUTION_RATE = "requested_id_resolution_rate"


class EvidenceUnit(StrEnum):
    """Semantic units attached to evidence values."""

    BOOLEAN = "boolean"
    COUNT = "count"
    STATE = "state"
    RATIO = "ratio"


class EvidenceAvailability(StrEnum):
    """Whether an evidence value is present in the source analysis."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class SignalEvidenceContext(BaseModel):
    """Shared immutable provenance reference for all evidence in one bundle."""

    model_config = ConfigDict(frozen=True)

    provenance: VideoAcquisitionProvenance
    evaluated_at: datetime

    @model_validator(mode="after")
    def validate_evaluation_time(self) -> SignalEvidenceContext:
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("evidence evaluation time must be timezone-aware")
        return self


class MetricEvidence(BaseModel, Generic[EvidenceValueT]):
    """One typed factual metric without business interpretation."""

    model_config = ConfigDict(frozen=True)

    metric: MetricType | EvidenceFact
    value: EvidenceValueT | None
    unit: EvidenceUnit
    availability: EvidenceAvailability
    context: SignalEvidenceContext

    @model_validator(mode="after")
    def validate_availability(self) -> MetricEvidence[EvidenceValueT]:
        expected = (
            EvidenceAvailability.UNAVAILABLE
            if self.value is None
            else EvidenceAvailability.AVAILABLE
        )
        if self.availability is not expected:
            raise ValueError("evidence availability must match value presence")
        return self


class QualificationEvidence(BaseModel):
    """Typed qualification outcome without duplicated acquisition provenance."""

    model_config = ConfigDict(frozen=True)

    metric: Literal[EvidenceFact.QUALIFICATION] = EvidenceFact.QUALIFICATION
    value: bool
    unit: Literal[EvidenceUnit.BOOLEAN] = EvidenceUnit.BOOLEAN
    availability: Literal[EvidenceAvailability.AVAILABLE] = (
        EvidenceAvailability.AVAILABLE
    )
    failures: tuple[QualificationFailureReason, ...]
    policy_version: int = Field(ge=1)
    context: SignalEvidenceContext


class SignalEvidenceBundle(BaseModel):
    """Complete typed evidence projection for one subscriber-relative analysis."""

    model_config = ConfigDict(frozen=True)

    qualification: QualificationEvidence
    eligible_sample: MetricEvidence[int]
    subscriber: MetricEvidence[SubscriberState]
    requested_id_resolution: MetricEvidence[float]
    median_standard_video_vsr: MetricEvidence[float]

    @model_validator(mode="after")
    def validate_structure(self) -> SignalEvidenceBundle:
        expected = (
            (
                self.eligible_sample,
                MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                EvidenceUnit.COUNT,
            ),
            (
                self.subscriber,
                EvidenceFact.SUBSCRIBER_STATE,
                EvidenceUnit.STATE,
            ),
            (
                self.requested_id_resolution,
                EvidenceFact.REQUESTED_ID_RESOLUTION_RATE,
                EvidenceUnit.RATIO,
            ),
            (
                self.median_standard_video_vsr,
                MetricType.MEDIAN_STANDARD_VIDEO_VSR,
                EvidenceUnit.RATIO,
            ),
        )
        for evidence, metric, unit in expected:
            if evidence.metric is not metric or evidence.unit is not unit:
                raise ValueError("evidence metric and unit must match its bundle slot")

        context = self.qualification.context
        if any(evidence.context != context for evidence, _, _ in expected):
            raise ValueError("all bundle evidence must reference the same context")
        return self
