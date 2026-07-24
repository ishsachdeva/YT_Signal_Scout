"""Immutable discovery facts for one possible Product Opportunity."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

OPPORTUNITY_CANDIDATE_SCHEMA_VERSION = 1

CandidateIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
ReferenceIdentity = Annotated[
    str,
    Field(
        min_length=1,
        max_length=200,
        pattern=r"^[a-z][a-z0-9]*(?:[._:/-][a-z0-9]+)*$",
    ),
]


class CandidateSourcePlatform(StrEnum):
    """Closed source-platform vocabulary for Candidate schema v1."""

    YOUTUBE = "youtube"


class OpportunityCandidate(BaseModel):
    """One immutable versioned set of pre-qualification discovery facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    candidate_id: CandidateIdentifier
    discovery_version: int = Field(ge=1, strict=True)
    source_platform: CandidateSourcePlatform
    discovery_source_id: ReferenceIdentity
    evidence_reference_ids: tuple[ReferenceIdentity, ...] = Field(min_length=1)
    acquisition_timestamp: datetime
    provenance_reference_ids: tuple[ReferenceIdentity, ...] = Field(min_length=1)

    @field_validator("schema_version", mode="before")
    @classmethod
    def validate_schema_version(cls, value: object) -> object:
        """Reject Boolean or coercible schema identities before Literal validation."""
        if type(value) is not int:
            raise ValueError("schema version must be the integer 1")
        return value

    @field_validator("evidence_reference_ids", "provenance_reference_ids", mode="before")
    @classmethod
    def validate_reference_collection_type(cls, value: object) -> object:
        """Require immutable reference collections without coercing mutable inputs."""
        if type(value) is not tuple:
            raise ValueError("reference identities must be supplied as a tuple")
        return value

    @field_validator("evidence_reference_ids")
    @classmethod
    def validate_unique_evidence_references(
        cls, value: tuple[str, ...]
    ) -> tuple[str, ...]:
        """Reject repeated evidence identities without changing source order."""
        if len(set(value)) != len(value):
            raise ValueError("evidence reference identities must be unique")
        return value

    @field_validator("provenance_reference_ids")
    @classmethod
    def validate_unique_provenance_references(
        cls, value: tuple[str, ...]
    ) -> tuple[str, ...]:
        """Reject repeated provenance identities without changing source order."""
        if len(set(value)) != len(value):
            raise ValueError("provenance reference identities must be unique")
        return value

    @field_validator("acquisition_timestamp", mode="before")
    @classmethod
    def validate_acquisition_timestamp(cls, value: object) -> datetime:
        """Require an aware datetime and normalize equivalent instants to UTC."""
        if not isinstance(value, datetime):
            raise ValueError("acquisition timestamp must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("acquisition timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)
