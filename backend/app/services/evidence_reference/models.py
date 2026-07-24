"""Immutable canonical identity for one pointer to evidence."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EVIDENCE_REFERENCE_SCHEMA_VERSION = 1

EvidenceReferenceIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
SourceObjectIdentity = Annotated[
    str,
    Field(
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z0-9_-]+$",
    ),
]


class EvidenceType(StrEnum):
    """Closed YouTube evidence-object vocabulary for schema v1."""

    CHANNEL = "channel"
    VIDEO = "video"


class EvidenceSourcePlatform(StrEnum):
    """Closed evidence source-platform vocabulary for schema v1."""

    YOUTUBE = "youtube"


class EvidenceReference(BaseModel):
    """One immutable versioned pointer that contains no evidence payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    evidence_reference_id: EvidenceReferenceIdentifier
    evidence_version: int = Field(ge=1, strict=True)
    evidence_type: EvidenceType
    source_platform: EvidenceSourcePlatform
    source_object_id: SourceObjectIdentity

    @field_validator("schema_version", mode="before")
    @classmethod
    def validate_schema_version(cls, value: object) -> object:
        """Reject Boolean or coercible schema identities before Literal validation."""
        if type(value) is not int:
            raise ValueError("schema version must be the integer 1")
        return value

    @model_validator(mode="after")
    def validate_distinct_identities(self) -> EvidenceReference:
        """Keep reference identity distinct from the pointed-to source identity."""
        if self.evidence_reference_id == self.source_object_id:
            raise ValueError("evidence reference and source object identities must be distinct")
        return self
