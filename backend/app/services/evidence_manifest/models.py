"""Immutable identity snapshot for an ordered Evidence Reference collection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.evidence_reference.models import EvidenceReferenceIdentifier

EVIDENCE_MANIFEST_SCHEMA_VERSION = 1

EvidenceManifestIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
ManifestDescription = Annotated[
    str,
    Field(min_length=1, max_length=1_000, pattern=r"^\S(?:.*\S)?$"),
]


class EvidenceManifest(BaseModel):
    """One immutable versioned declaration of ordered evidence-reference IDs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    manifest_id: EvidenceManifestIdentifier
    manifest_version: int = Field(ge=1, strict=True)
    evidence_reference_ids: tuple[EvidenceReferenceIdentifier, ...] = Field(
        min_length=1
    )
    created_at: datetime
    description: ManifestDescription | None = None

    @field_validator("schema_version", mode="before")
    @classmethod
    def validate_schema_version(cls, value: object) -> object:
        """Reject Boolean or coercible schema identities before Literal validation."""
        if type(value) is not int:
            raise ValueError("schema version must be the integer 1")
        return value

    @field_validator("evidence_reference_ids", mode="before")
    @classmethod
    def validate_reference_collection_type(cls, value: object) -> object:
        """Require an immutable tuple without coercing mutable collections."""
        if type(value) is not tuple:
            raise ValueError("evidence reference identities must be supplied as a tuple")
        return value

    @field_validator("evidence_reference_ids")
    @classmethod
    def validate_unique_references(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject duplicate references without sorting or deduplicating source order."""
        if len(set(value)) != len(value):
            raise ValueError("evidence reference identities must be unique")
        return value

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, value: object) -> datetime:
        """Require an aware datetime and normalize equivalent instants to UTC."""
        if not isinstance(value, datetime):
            raise ValueError("manifest creation timestamp must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("manifest creation timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)
