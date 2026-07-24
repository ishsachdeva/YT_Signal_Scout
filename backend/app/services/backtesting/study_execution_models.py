"""Immutable contracts for governed, non-analytical study execution."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.evidence_models import EvidencePackImportResult
from app.services.backtesting.import_models import HistoricalDatasetImportResult
from app.services.backtesting.label_models import (
    GroundTruthLabelImportResult,
    LabelContentDigest,
)
from app.services.backtesting.models import ResearchIdentifier
from app.services.backtesting.rubric_models import RubricImportResult

STUDY_EXECUTION_SCHEMA_VERSION = 1
StudyText = Annotated[str, Field(min_length=1, max_length=4_000)]


class StudyConfiguration(BaseModel):
    """Versioned compatibility declaration for one governed study."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    configuration_id: ResearchIdentifier
    version: int = Field(ge=1)
    dataset_schema_version: Literal[2]
    evidence_pack_schema_version: Literal[1]
    labelling_rubric_schema_version: Literal[1]
    ground_truth_label_schema_version: Literal[1]


class StudyDefinition(BaseModel):
    """Pre-declared identity, purpose, protocol, and configuration binding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    study_id: ResearchIdentifier
    version: int = Field(ge=1)
    title: Annotated[str, Field(min_length=1, max_length=200)]
    objective: StudyText
    protocol_id: ResearchIdentifier
    protocol_version: int = Field(ge=1)
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_created_at(self) -> StudyDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("study creation timestamp must be timezone-aware")
        return self


class StudyInputBundle(BaseModel):
    """Exactly one strictly imported artifact of each governed input kind."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset: HistoricalDatasetImportResult
    evidence_packs: Annotated[tuple[EvidencePackImportResult, ...], Field(min_length=1)]
    labelling_rubric: RubricImportResult
    ground_truth_labels: GroundTruthLabelImportResult
    configuration: StudyConfiguration


class StudyExecutionRequest(BaseModel):
    """Complete supplied request for one deterministic synchronous execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: ResearchIdentifier
    requested_at: datetime
    started_at: datetime
    completed_at: datetime
    definition: StudyDefinition
    inputs: StudyInputBundle

    @model_validator(mode="after")
    def validate_timestamps(self) -> StudyExecutionRequest:
        timestamps = (self.requested_at, self.started_at, self.completed_at)
        if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
            raise ValueError("execution timestamps must be timezone-aware")
        if self.requested_at > self.started_at or self.started_at > self.completed_at:
            raise ValueError("execution timestamps must be chronological")
        if self.definition.created_at > self.requested_at:
            raise ValueError("study definition cannot postdate its execution request")
        return self


class StudyExecutionMetadata(BaseModel):
    """Factual execution identity and caller-supplied timestamps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: ResearchIdentifier
    requested_at: datetime
    started_at: datetime
    completed_at: datetime
    study_id: ResearchIdentifier
    study_version: int = Field(ge=1)


class StudyExecutionContext(BaseModel):
    """Validated identities for the sole observation executed by this boundary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    observation_count: int = Field(ge=1)
    evidence_pack_count: int = Field(ge=1)
    label_count: int = Field(ge=1)
    evidence_pack_definition_id: ResearchIdentifier
    evidence_pack_definition_version: int = Field(ge=1)
    rubric_id: ResearchIdentifier
    rubric_version: int = Field(ge=1)
    label_set_id: ResearchIdentifier
    label_set_version: int = Field(ge=1)
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)


class StudyExecutionManifest(BaseModel):
    """Content-addressed manifest of every governed execution input."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    dataset_digest: LabelContentDigest
    evidence_definition_digest: LabelContentDigest
    evidence_pack_digests: Annotated[tuple[LabelContentDigest, ...], Field(min_length=1)]
    rubric_digest: LabelContentDigest
    ground_truth_label_digest: LabelContentDigest
    result_digest: LabelContentDigest


class StudyExecutionResult(BaseModel):
    """Immutable, non-interpretive execution artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: StudyExecutionMetadata
    context: StudyExecutionContext
    manifest: StudyExecutionManifest
