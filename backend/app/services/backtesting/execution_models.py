"""Immutable contracts for controlled offline backtest execution."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.import_models import HistoricalDatasetImportResult
from app.services.backtesting.models import (
    MedianVsrThresholdSet,
    ResearchIdentifier,
    SubscriberBandSet,
    ThresholdBacktestReport,
)


class BacktestExecutionConfiguration(BaseModel):
    """Versioned study inputs bound to one governed historical dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    configuration_id: ResearchIdentifier
    version: int = Field(ge=1)
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    band_set: SubscriberBandSet
    threshold_set: MedianVsrThresholdSet


class BacktestExecutionRequest(BaseModel):
    """Complete deterministic input for one controlled execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: ResearchIdentifier
    executed_at: datetime
    imported_dataset: HistoricalDatasetImportResult
    configuration: BacktestExecutionConfiguration

    @model_validator(mode="after")
    def validate_execution_time(self) -> BacktestExecutionRequest:
        if self.executed_at.tzinfo is None or self.executed_at.utcoffset() is None:
            raise ValueError("execution timestamp must be timezone-aware")
        return self


class BacktestExecutionMetadata(BaseModel):
    """Factual identities and versions for one completed execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: ResearchIdentifier
    executed_at: datetime
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    band_set_id: ResearchIdentifier
    band_set_version: int = Field(ge=1)
    threshold_set_id: ResearchIdentifier
    threshold_set_version: int = Field(ge=1)


class BacktestExecutionResult(BaseModel):
    """Immutable metadata and factual report from one complete execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: BacktestExecutionMetadata
    report: ThresholdBacktestReport
