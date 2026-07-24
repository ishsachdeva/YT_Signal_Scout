"""Immutable contracts for governed historical dataset import."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.models import (
    ResearchIdentifier,
    SubscriberRelativeBacktestDataset,
)

HISTORICAL_DATASET_SCHEMA_VERSION = 2

DatasetText = Annotated[str, Field(min_length=1, max_length=4_000)]


class HistoricalDatasetDigest(BaseModel):
    """Digest declared for canonical manifest metadata and observations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    algorithm: Literal["sha256"]
    value: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class HistoricalDatasetCustody(BaseModel):
    """Identity and time responsible for creating one dataset version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    creator_identity: Annotated[str, Field(min_length=1, max_length=200)]
    created_at: datetime

    @model_validator(mode="after")
    def validate_created_at(self) -> HistoricalDatasetCustody:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("dataset creation timestamp must be timezone-aware")
        return self


class HistoricalDatasetProvenance(BaseModel):
    """Collection scope, method, cutoff, and limitations for one dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_description: DatasetText
    collection_methodology: DatasetText
    selection_methodology_id: ResearchIdentifier
    selection_methodology_version: int = Field(ge=1)
    collection_started_at: datetime
    collection_ended_at: datetime
    observation_cutoff: datetime
    known_limitations: tuple[DatasetText, ...]

    @model_validator(mode="after")
    def validate_times(self) -> HistoricalDatasetProvenance:
        timestamps = (
            self.collection_started_at,
            self.collection_ended_at,
            self.observation_cutoff,
        )
        if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
            raise ValueError("dataset provenance timestamps must be timezone-aware")
        if self.collection_ended_at < self.collection_started_at:
            raise ValueError("dataset collection end must not precede its start")
        if self.collection_ended_at < self.observation_cutoff:
            raise ValueError("dataset collection end must not precede observation cutoff")
        if len(set(self.known_limitations)) != len(self.known_limitations):
            raise ValueError("dataset known limitations must be unique")
        return self


class HistoricalDatasetManifest(BaseModel):
    """Versioned identity declared by one governed historical JSON document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[2]
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    custody: HistoricalDatasetCustody
    provenance: HistoricalDatasetProvenance
    digest: HistoricalDatasetDigest

    @model_validator(mode="after")
    def validate_manifest_times(self) -> HistoricalDatasetManifest:
        if self.custody.created_at < self.provenance.collection_ended_at:
            raise ValueError("dataset creation time must not precede collection end")
        return self


class HistoricalDatasetImportResult(BaseModel):
    """Imported immutable dataset with its validated external schema manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest: HistoricalDatasetManifest
    dataset: SubscriberRelativeBacktestDataset

    @model_validator(mode="after")
    def validate_identity(self) -> HistoricalDatasetImportResult:
        if self.manifest.dataset_id != self.dataset.dataset_id:
            raise ValueError("manifest and imported dataset IDs must match")
        if self.manifest.dataset_version != self.dataset.version:
            raise ValueError("manifest and imported dataset versions must match")
        return self
