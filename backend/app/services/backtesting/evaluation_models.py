"""Immutable human observations for governed threshold-study evaluation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.methodology_models import (
    ResearchRecommendation,
    ThresholdEvaluationMethodology,
    ThresholdEvaluationMetric,
)
from app.services.backtesting.models import ResearchIdentifier
from app.services.backtesting.study_models import BacktestStudyArtifact


class CriterionObservationStatus(StrEnum):
    """Closed qualitative states for one human criterion observation."""

    REVIEWED = "reviewed"
    NOT_REVIEWED = "not_reviewed"
    NEEDS_CLARIFICATION = "needs_clarification"


class CriterionObservation(BaseModel):
    """One human observation bound to a methodology criterion and report metric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    criterion_id: ResearchIdentifier
    metric: ThresholdEvaluationMetric
    status: CriterionObservationStatus
    notes: Annotated[str | None, Field(default=None, min_length=1, max_length=2_000)]


class BacktestStudyEvaluation(BaseModel):
    """One immutable human evaluation of an executed study and methodology."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_id: ResearchIdentifier
    version: int = Field(ge=1)
    evaluated_at: datetime
    reviewer: Annotated[str, Field(min_length=1, max_length=200)]
    study: BacktestStudyArtifact
    methodology: ThresholdEvaluationMethodology
    observations: Annotated[tuple[CriterionObservation, ...], Field(min_length=1)]
    recommendation: ResearchRecommendation

    @model_validator(mode="after")
    def validate_evaluation(self) -> BacktestStudyEvaluation:
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("study evaluation timestamp must be timezone-aware")
        if self.study.execution is None:
            raise ValueError("study evaluation requires an executed study artifact")
        if self.evaluated_at < self.study.execution.metadata.executed_at:
            raise ValueError("study evaluation cannot precede study execution")

        expected = tuple(
            (criterion.criterion_id, criterion.metric)
            for criterion in self.methodology.criteria
        )
        observed = tuple(
            (observation.criterion_id, observation.metric)
            for observation in self.observations
        )
        if observed != expected:
            raise ValueError(
                "criterion observations must match methodology criteria in order"
            )
        if any(
            criterion.required
            and observation.status is CriterionObservationStatus.NOT_REVIEWED
            for criterion, observation in zip(
                self.methodology.criteria, self.observations, strict=True
            )
        ):
            raise ValueError("required criteria cannot be marked not reviewed")
        if self.recommendation not in self.methodology.permitted_recommendations:
            raise ValueError("research recommendation is not permitted by methodology")
        return self
