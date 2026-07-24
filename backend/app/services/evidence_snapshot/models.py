"""Immutable versioned identity binding to one Evidence Manifest version."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.evidence_manifest.models import EvidenceManifestIdentifier

EVIDENCE_SNAPSHOT_SCHEMA_VERSION = 1

EvidenceSnapshotIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]
SnapshotDescription = Annotated[
    str,
    Field(min_length=1, max_length=1_000, pattern=r"^\S(?:.*\S)?$"),
]
ManifestCanonicalSha256Digest = Annotated[
    str,
    Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        strict=True,
    ),
]


class EvidenceSnapshot(BaseModel):
    """One immutable identity binding to an exact Evidence Manifest version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    snapshot_id: EvidenceSnapshotIdentifier
    snapshot_version: int = Field(ge=1, strict=True)
    manifest_id: EvidenceManifestIdentifier
    manifest_version: int = Field(ge=1, strict=True)
    manifest_digest: ManifestCanonicalSha256Digest
    snapshot_timestamp: datetime
    description: SnapshotDescription | None = None

    @field_validator("schema_version", mode="before")
    @classmethod
    def validate_schema_version(cls, value: object) -> object:
        """Reject Boolean or coercible schema identities before Literal validation."""
        if type(value) is not int:
            raise ValueError("schema version must be the integer 1")
        return value

    @field_validator("snapshot_timestamp", mode="before")
    @classmethod
    def validate_snapshot_timestamp(cls, value: object) -> datetime:
        """Require an aware datetime and normalize equivalent instants to UTC."""
        if not isinstance(value, datetime):
            raise ValueError("snapshot timestamp must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("snapshot timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)
