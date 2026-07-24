"""Immutable policy contracts for production threshold promotion eligibility."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.models import ResearchIdentifier
from app.services.backtesting.study_models import BacktestStudyStatus

REQUIRED_PROMOTION_REQUIREMENT_KINDS = frozenset(
    {
        "approved_study",
        "methodology_version",
        "approved_product_policy",
        "release_governance_reviews",
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


class ApprovedProductPolicyRequirement(_PromotionRequirement):
    """Require one approved, versioned Product policy for a release."""

    kind: Literal["approved_product_policy"]
    decision_id: Annotated[
        str,
        Field(min_length=1, max_length=100, pattern=r"^PDR-[0-9]{3,}$"),
    ]
    decision_version: int = Field(ge=1)
    effective_release: Annotated[
        str,
        Field(pattern=r"^v[0-9]+\.[0-9]+\.[0-9]+$"),
    ]


ReleaseGovernanceReviewer = Literal["analytics_owner", "architecture_owner"]


class ReleaseGovernanceReviewsRequirement(_PromotionRequirement):
    """Require one-time release-governance review dispositions."""

    kind: Literal["release_governance_reviews"]
    required_reviewers: tuple[ReleaseGovernanceReviewer, ...]

    @model_validator(mode="after")
    def validate_reviewers(self) -> ReleaseGovernanceReviewsRequirement:
        if set(self.required_reviewers) != {"analytics_owner", "architecture_owner"}:
            raise ValueError(
                "release governance requires Analytics and Architecture reviewers"
            )
        if len(self.required_reviewers) != 2:
            raise ValueError("release governance reviewers must be unique")
        return self


PromotionRequirement = Annotated[
    ApprovedStudyRequirement
    | MethodologyVersionRequirement
    | ApprovedProductPolicyRequirement
    | ReleaseGovernanceReviewsRequirement,
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
