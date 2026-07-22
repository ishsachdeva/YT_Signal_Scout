"""Immutable contracts for governed historical dataset import."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.models import (
    ResearchIdentifier,
    SubscriberRelativeBacktestDataset,
)

HISTORICAL_DATASET_SCHEMA_VERSION = 1


class HistoricalDatasetManifest(BaseModel):
    """Versioned identity declared by one governed historical JSON document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)


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
