"""Immutable governance contracts for offline threshold studies."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.execution_models import (
    BacktestExecutionConfiguration,
    BacktestExecutionResult,
)
from app.services.backtesting.models import ResearchIdentifier


class BacktestStudyStatus(StrEnum):
    """Closed lifecycle states for immutable research study artifacts."""

    DRAFT = "draft"
    EXECUTED = "executed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class BacktestStudyDecision(StrEnum):
    """Closed research-review decisions with no production authority."""

    APPROVE_STUDY = "approve_study"
    REJECT_STUDY = "reject_study"


class BacktestStudyDefinition(BaseModel):
    """Versioned purpose and execution configuration for one study."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    study_id: ResearchIdentifier
    version: int = Field(ge=1)
    title: Annotated[str, Field(min_length=1, max_length=200)]
    objective: Annotated[str, Field(min_length=1, max_length=1_000)]
    created_at: datetime
    configuration: BacktestExecutionConfiguration

    @model_validator(mode="after")
    def validate_created_at(self) -> BacktestStudyDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("study creation timestamp must be timezone-aware")
        return self


class BacktestStudyReview(BaseModel):
    """Immutable human review of one executed research study version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    review_id: ResearchIdentifier
    study_id: ResearchIdentifier
    study_version: int = Field(ge=1)
    execution_id: ResearchIdentifier
    reviewed_at: datetime
    reviewer: Annotated[str, Field(min_length=1, max_length=200)]
    decision: BacktestStudyDecision
    rationale: Annotated[str, Field(min_length=1, max_length=2_000)]

    @model_validator(mode="after")
    def validate_reviewed_at(self) -> BacktestStudyReview:
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("study review timestamp must be timezone-aware")
        return self


class BacktestStudyArtifact(BaseModel):
    """Complete immutable representation of one study lifecycle state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_version: int = Field(ge=1)
    status: BacktestStudyStatus
    definition: BacktestStudyDefinition
    execution: BacktestExecutionResult | None = None
    reviews: tuple[BacktestStudyReview, ...] = ()

    @model_validator(mode="after")
    def validate_lifecycle(self) -> BacktestStudyArtifact:
        if self.status is BacktestStudyStatus.DRAFT:
            if self.execution is not None or self.reviews:
                raise ValueError("draft studies cannot contain execution or review artifacts")
            return self

        if self.execution is None:
            raise ValueError("non-draft studies require an execution result")
        self._validate_execution_identity()
        if self.definition.created_at > self.execution.metadata.executed_at:
            raise ValueError("study execution cannot precede study creation")

        if self.status is BacktestStudyStatus.EXECUTED:
            if self.reviews:
                raise ValueError("executed studies cannot contain review artifacts")
            return self

        if not self.reviews:
            raise ValueError("reviewed study states require at least one review")
        self._validate_reviews()
        if self.status is BacktestStudyStatus.APPROVED and (
            self.reviews[-1].decision is not BacktestStudyDecision.APPROVE_STUDY
        ):
            raise ValueError("approved study status requires a final approval review")
        if self.status is BacktestStudyStatus.REJECTED and (
            self.reviews[-1].decision is not BacktestStudyDecision.REJECT_STUDY
        ):
            raise ValueError("rejected study status requires a final rejection review")
        return self

    def _validate_execution_identity(self) -> None:
        assert self.execution is not None
        expected = self.definition.configuration
        metadata = self.execution.metadata
        if (
            metadata.configuration_id != expected.configuration_id
            or metadata.configuration_version != expected.version
            or metadata.dataset_id != expected.dataset_id
            or metadata.dataset_version != expected.dataset_version
            or metadata.band_set_id != expected.band_set.band_set_id
            or metadata.band_set_version != expected.band_set.version
            or metadata.threshold_set_id != expected.threshold_set.threshold_set_id
            or metadata.threshold_set_version != expected.threshold_set.version
        ):
            raise ValueError("study execution must match the definition configuration")

    def _validate_reviews(self) -> None:
        assert self.execution is not None
        review_ids = tuple(review.review_id for review in self.reviews)
        if len(set(review_ids)) != len(review_ids):
            raise ValueError("study review IDs must be unique")
        timestamps = tuple(review.reviewed_at for review in self.reviews)
        if any(
            current >= following
            for current, following in zip(timestamps, timestamps[1:], strict=False)
        ):
            raise ValueError("study review timestamps must be strictly increasing")
        for review in self.reviews:
            if (
                review.study_id != self.definition.study_id
                or review.study_version != self.definition.version
                or review.execution_id != self.execution.metadata.execution_id
            ):
                raise ValueError("study review must match the study execution")
            if review.reviewed_at < self.execution.metadata.executed_at:
                raise ValueError("study review cannot precede study execution")
