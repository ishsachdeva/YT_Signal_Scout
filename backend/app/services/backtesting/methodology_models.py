"""Immutable methodology contracts for factual threshold-study evaluation."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.models import ResearchIdentifier


class ThresholdEvaluationMetric(StrEnum):
    """Closed factual measures already available in threshold reports."""

    QUALIFICATION_COVERAGE = "qualification_coverage"
    MEDIAN_VSR_AVAILABILITY = "median_vsr_availability"
    THRESHOLD_ELIGIBLE_SUPPORT = "threshold_eligible_support"
    MEDIAN_VSR_DISTRIBUTION = "median_vsr_distribution"
    CANDIDATE_HIT_RATE = "candidate_hit_rate"
    EXCLUSION_PROFILE = "exclusion_profile"
    QUALIFICATION_FAILURE_PROFILE = "qualification_failure_profile"


class ResearchRecommendation(StrEnum):
    """Closed research-only dispositions without production authority."""

    FURTHER_INVESTIGATION = "further_investigation"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CANDIDATE_WORTH_REVIEWING = "candidate_worth_reviewing"
    READY_FOR_HUMAN_REVIEW = "ready_for_human_review"


class ThresholdEvaluationCriterion(BaseModel):
    """One explicitly identified factual measure to inspect during review."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    criterion_id: ResearchIdentifier
    metric: ThresholdEvaluationMetric
    description: Annotated[str, Field(min_length=1, max_length=1_000)]
    required: bool


class ThresholdEvaluationMethodology(BaseModel):
    """Versioned ordered criteria and permitted research dispositions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    methodology_id: ResearchIdentifier
    version: int = Field(ge=1)
    name: Annotated[str, Field(min_length=1, max_length=200)]
    objective: Annotated[str, Field(min_length=1, max_length=1_000)]
    criteria: Annotated[tuple[ThresholdEvaluationCriterion, ...], Field(min_length=1)]
    permitted_recommendations: Annotated[
        tuple[ResearchRecommendation, ...], Field(min_length=1)
    ]

    @model_validator(mode="after")
    def validate_methodology(self) -> ThresholdEvaluationMethodology:
        criterion_ids = tuple(criterion.criterion_id for criterion in self.criteria)
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("threshold evaluation criterion IDs must be unique")
        metrics = tuple(criterion.metric for criterion in self.criteria)
        if len(set(metrics)) != len(metrics):
            raise ValueError("threshold evaluation metrics must be unique")
        if len(set(self.permitted_recommendations)) != len(
            self.permitted_recommendations
        ):
            raise ValueError("research recommendations must be unique")
        return self
