"""Immutable facts defining one future qualification evaluation request."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.creator_profile.models import CreatorProfileIdentifier
from app.services.evidence_snapshot.models import EvidenceSnapshotIdentifier
from app.services.opportunity_candidate.models import CandidateIdentifier

QUALIFICATION_CONTEXT_SCHEMA_VERSION = 1

QualificationContextIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
QualificationPolicyIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
QualificationContextDescription = Annotated[
    str,
    Field(min_length=1, max_length=1_000, pattern=r"^\S(?:.*\S)?$"),
]


class QualificationContext(BaseModel):
    """One immutable request of identities bound at an evaluation instant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    qualification_context_id: QualificationContextIdentifier
    qualification_context_version: int = Field(ge=1, strict=True)
    candidate_id: CandidateIdentifier
    snapshot_id: EvidenceSnapshotIdentifier
    profile_id: CreatorProfileIdentifier
    qualification_policy_id: QualificationPolicyIdentifier
    qualification_policy_version: int = Field(ge=1, strict=True)
    evaluation_timestamp: datetime
    description: QualificationContextDescription | None = None

    @field_validator("schema_version", mode="before")
    @classmethod
    def validate_schema_version(cls, value: object) -> object:
        """Reject Boolean or coercible schema identities before Literal validation."""
        if type(value) is not int:
            raise ValueError("schema version must be the integer 1")
        return value

    @field_validator("evaluation_timestamp", mode="before")
    @classmethod
    def validate_evaluation_timestamp(cls, value: object) -> datetime:
        """Require an aware datetime and normalize equivalent instants to UTC."""
        if not isinstance(value, datetime):
            raise ValueError("evaluation timestamp must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("evaluation timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)
