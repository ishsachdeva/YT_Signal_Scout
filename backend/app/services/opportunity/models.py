"""Immutable canonical business identity for one Product Opportunity."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

OPPORTUNITY_SCHEMA_VERSION = 1

OpportunityIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
CanonicalContextText = Annotated[
    str,
    Field(min_length=1, max_length=100, pattern=r"^\S(?:.*\S)?$"),
]
CanonicalProposition = Annotated[
    str,
    Field(min_length=1, max_length=4_000, pattern=r"^\S(?:.*\S)?$"),
]


class SourcePlatform(StrEnum):
    """Closed source-platform vocabulary for Opportunity schema v1."""

    YOUTUBE = "youtube"


class KnownOpportunityContext(BaseModel):
    """One explicitly known canonical context value."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: Literal["known"]
    value: CanonicalContextText


class UnknownOpportunityContext(BaseModel):
    """One explicitly unknown context value without a fabricated value."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: Literal["unknown"]


OpportunityContext = Annotated[
    KnownOpportunityContext | UnknownOpportunityContext,
    Field(discriminator="state"),
]


class Opportunity(BaseModel):
    """One immutable versioned bounded market proposition identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    opportunity_id: OpportunityIdentifier
    opportunity_version: int = Field(ge=1, strict=True)
    market_id: OpportunityIdentifier
    niche_id: OpportunityIdentifier
    source_platform: SourcePlatform
    proposition: CanonicalProposition
    language: OpportunityContext
    region: OpportunityContext

    @field_validator("schema_version", mode="before")
    @classmethod
    def validate_schema_version(cls, value: object) -> object:
        """Reject Boolean or coercible schema identities before Literal validation."""
        if type(value) is not int:
            raise ValueError("schema version must be the integer 1")
        return value

    @model_validator(mode="after")
    def validate_unique_identifiers(self) -> Opportunity:
        """Keep every opaque identity distinct within one Opportunity snapshot."""
        identifiers = (self.opportunity_id, self.market_id, self.niche_id)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("opportunity, market, and niche identifiers must be unique")
        return self
