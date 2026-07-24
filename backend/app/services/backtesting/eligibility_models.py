"""Immutable outcomes for production-promotion eligibility assessment."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.evaluation_models import BacktestStudyEvaluation
from app.services.backtesting.models import ResearchIdentifier
from app.services.backtesting.promotion_models import ProductionPromotionPolicy
from app.services.backtesting.study_models import BacktestStudyArtifact

PromotionRequirementKind = Literal[
    "approved_study",
    "methodology_version",
    "approved_product_policy",
    "release_governance_reviews",
]


class EligibilityRequirementResult(BaseModel):
    """Factual satisfaction outcome for one policy requirement."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requirement_id: ResearchIdentifier
    requirement_kind: PromotionRequirementKind
    satisfied: bool
    failure_reason: Annotated[
        str | None, Field(default=None, min_length=1, max_length=1_000)
    ]

    @model_validator(mode="after")
    def validate_failure(self) -> EligibilityRequirementResult:
        if self.satisfied and self.failure_reason is not None:
            raise ValueError("satisfied eligibility requirements cannot have a failure reason")
        if not self.satisfied and self.failure_reason is None:
            raise ValueError("failed eligibility requirements require a failure reason")
        return self


class ProductionEligibilityAssessment(BaseModel):
    """Immutable factual outcome for one study and promotion policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assessment_id: ResearchIdentifier
    version: int = Field(ge=1)
    assessed_at: datetime
    policy: ProductionPromotionPolicy
    study: BacktestStudyArtifact
    evaluations: tuple[BacktestStudyEvaluation, ...]
    requirement_results: Annotated[
        tuple[EligibilityRequirementResult, ...], Field(min_length=1)
    ]
    eligible: bool
    failed_requirement_ids: tuple[ResearchIdentifier, ...]

    @model_validator(mode="after")
    def validate_assessment(self) -> ProductionEligibilityAssessment:
        if self.assessed_at.tzinfo is None or self.assessed_at.utcoffset() is None:
            raise ValueError("eligibility assessment timestamp must be timezone-aware")
        if self.study.execution is None:
            raise ValueError("eligibility assessment requires an executed study")
        if self.assessed_at < self.study.execution.metadata.executed_at:
            raise ValueError("eligibility assessment cannot precede study execution")
        self._validate_evaluations()

        expected = tuple(
            (requirement.requirement_id, requirement.kind)
            for requirement in self.policy.requirements
        )
        actual = tuple(
            (result.requirement_id, result.requirement_kind)
            for result in self.requirement_results
        )
        if actual != expected:
            raise ValueError(
                "eligibility results must match promotion requirements in order"
            )
        expected_failures = tuple(
            result.requirement_id
            for result in self.requirement_results
            if not result.satisfied
        )
        if self.failed_requirement_ids != expected_failures:
            raise ValueError("failed requirement IDs must match eligibility results")
        if self.eligible != (not expected_failures):
            raise ValueError("eligibility outcome must match requirement results")
        return self

    def _validate_evaluations(self) -> None:
        evaluation_ids = tuple(
            evaluation.evaluation_id for evaluation in self.evaluations
        )
        if len(set(evaluation_ids)) != len(evaluation_ids):
            raise ValueError("eligibility evaluation IDs must be unique")
        for evaluation in self.evaluations:
            if evaluation.study != self.study:
                raise ValueError("eligibility evaluations must match the assessed study")
            if self.assessed_at < evaluation.evaluated_at:
                raise ValueError("eligibility assessment cannot precede an evaluation")
