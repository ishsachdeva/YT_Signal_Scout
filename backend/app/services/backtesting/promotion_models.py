"""Immutable policy contracts for production threshold promotion eligibility."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.methodology_models import ResearchRecommendation
from app.services.backtesting.models import ResearchIdentifier
from app.services.backtesting.study_models import BacktestStudyStatus

REQUIRED_PROMOTION_REQUIREMENT_KINDS = frozenset(
    {
        "approved_study",
        "methodology_version",
        "minimum_evaluations",
        "evaluation_completion",
        "research_recommendation",
        "manual_approval",
    }
)


class _PromotionRequirement(BaseModel):
    """Shared immutable identity for one declarative promotion prerequisite."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requirement_id: ResearchIdentifier


class ApprovedStudyRequirement(_PromotionRequirement):
    """Require the governed research study to have approved status."""

    kind: Literal["approved_study"]
    required_status: Literal[BacktestStudyStatus.APPROVED]


class MethodologyVersionRequirement(_PromotionRequirement):
    """Require evaluation against one exact methodology identity and version."""

    kind: Literal["methodology_version"]
    methodology_id: ResearchIdentifier
    methodology_version: int = Field(ge=1)


class MinimumEvaluationsRequirement(_PromotionRequirement):
    """Require a positive minimum count of governed human evaluations."""

    kind: Literal["minimum_evaluations"]
    minimum_count: int = Field(gt=0)


class EvaluationCompletionRequirement(_PromotionRequirement):
    """Define qualitative completion required of criterion observations."""

    kind: Literal["evaluation_completion"]
    allow_required_needs_clarification: bool
    require_optional_criteria_reviewed: bool


class ResearchRecommendationRequirement(_PromotionRequirement):
    """Require one of the explicitly permitted research recommendations."""

    kind: Literal["research_recommendation"]
    permitted_recommendations: Annotated[
        tuple[ResearchRecommendation, ...], Field(min_length=1)
    ]

    @model_validator(mode="after")
    def validate_recommendations(self) -> ResearchRecommendationRequirement:
        if len(set(self.permitted_recommendations)) != len(
            self.permitted_recommendations
        ):
            raise ValueError("promotion research recommendations must be unique")
        return self


class ManualApprovalRequirement(_PromotionRequirement):
    """Declare that a separate manual production approval remains required."""

    kind: Literal["manual_approval"]
    required: Literal[True]


PromotionRequirement = Annotated[
    ApprovedStudyRequirement
    | MethodologyVersionRequirement
    | MinimumEvaluationsRequirement
    | EvaluationCompletionRequirement
    | ResearchRecommendationRequirement
    | ManualApprovalRequirement,
    Field(discriminator="kind"),
]


class ProductionPromotionPolicy(BaseModel):
    """Versioned prerequisites that never perform or decide promotion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: ResearchIdentifier
    version: int = Field(ge=1)
    requirements: Annotated[tuple[PromotionRequirement, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_requirements(self) -> ProductionPromotionPolicy:
        requirement_ids = tuple(
            requirement.requirement_id for requirement in self.requirements
        )
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("promotion requirement IDs must be unique")
        requirement_kinds = tuple(requirement.kind for requirement in self.requirements)
        if len(set(requirement_kinds)) != len(requirement_kinds):
            raise ValueError("promotion requirement kinds must be unique")
        if set(requirement_kinds) != REQUIRED_PROMOTION_REQUIREMENT_KINDS:
            raise ValueError(
                "production promotion policy requires exactly one of each "
                "supported requirement kind"
            )
        return self
