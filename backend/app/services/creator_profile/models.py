"""Immutable deterministic facts for one personal Creator Profile."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CREATOR_PROFILE_SCHEMA_VERSION = 1

CreatorProfileIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
CanonicalLanguageTag = Annotated[
    str,
    Field(
        min_length=2,
        max_length=35,
        pattern=r"^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$",
    ),
]
GeographyCode = Annotated[str, Field(pattern=r"^[A-Z]{2}$")]


class PresentationStyle(StrEnum):
    """Self-declared preference for visible creator presentation."""

    FACELESS = "faceless"
    ON_CAMERA = "on_camera"
    MIXED = "mixed"


class AIAssistancePreference(StrEnum):
    """Self-declared preference for future AI-assisted production."""

    AVOID = "avoid"
    OPEN = "open"
    PREFER = "prefer"


class EditingCapability(StrEnum):
    """Self-assessed editing capability, never an objective skill score."""

    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class NarrationPreference(StrEnum):
    """Self-declared preferred narration approach."""

    OWN_VOICE = "own_voice"
    AI_VOICE = "ai_voice"
    NO_NARRATION = "no_narration"
    FLEXIBLE = "flexible"


class ProductionBudgetCategory(StrEnum):
    """Self-declared relative budget category without monetary inference."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UploadCadenceGoal(StrEnum):
    """Self-declared publishing goal, not a feasibility assessment."""

    NO_CURRENT_GOAL = "no_current_goal"
    MONTHLY = "monthly"
    TWICE_MONTHLY = "twice_monthly"
    WEEKLY = "weekly"
    MULTIPLE_PER_WEEK = "multiple_per_week"
    DAILY = "daily"


class CreatorProfile(BaseModel):
    """One immutable snapshot of explicit owner-supplied creator facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    profile_id: CreatorProfileIdentifier
    profile_version: int = Field(ge=1, strict=True)
    preferred_presentation_style: PresentationStyle | None = None
    ai_assistance_preference: AIAssistancePreference | None = None
    language_preference: CanonicalLanguageTag | None = None
    target_geography: GeographyCode | None = None
    available_production_hours_per_week: int | None = Field(
        default=None,
        ge=0,
        le=168,
        strict=True,
    )
    editing_capability: EditingCapability | None = None
    narration_preference: NarrationPreference | None = None
    production_budget_category: ProductionBudgetCategory | None = None
    upload_cadence_goal: UploadCadenceGoal | None = None

    @field_validator("schema_version", mode="before")
    @classmethod
    def validate_schema_version(cls, value: object) -> object:
        """Reject Boolean or coerced schema identities before Literal validation."""
        if type(value) is not int:
            raise ValueError("schema version must be the integer 1")
        return value
