"""Immutable contracts for factual observation-level labelled evaluation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.import_models import HistoricalDatasetImportResult
from app.services.backtesting.label_models import (
    GroundTruthLabel,
    GroundTruthLabelImportResult,
    LabelContentDigest,
)
from app.services.backtesting.models import ResearchIdentifier
from app.services.backtesting.study_execution_models import StudyExecutionResult

LABELLED_EVALUATION_SCHEMA_VERSION = 1
EvaluationText = Annotated[str, Field(min_length=1, max_length=4_000)]


class PredictedOutcome(StrEnum):
    """Closed supplied prediction vocabulary; no threshold is evaluated here."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"
    NOT_EVALUATED = "not_evaluated"


class EvaluationOutcome(StrEnum):
    """Closed factual relationship between one prediction and governed truth."""

    TRUE_POSITIVE = "true_positive"
    TRUE_NEGATIVE = "true_negative"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    UNKNOWN = "unknown"
    NOT_EVALUATED = "not_evaluated"


class ObservationPrediction(BaseModel):
    """One supplied prediction bound to an exact dataset observation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prediction_id: ResearchIdentifier
    observation_id: ResearchIdentifier
    channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    predicted_outcome: PredictedOutcome


class EvaluationConfiguration(BaseModel):
    """Versioned bindings and vocabulary for one labelled evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    configuration_id: ResearchIdentifier
    version: int = Field(ge=1)
    study_execution_id: ResearchIdentifier
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    label_set_id: ResearchIdentifier
    label_set_version: int = Field(ge=1)
    prediction_vocabulary_version: Literal[1]


class EvaluationDefinition(BaseModel):
    """Pre-declared purpose and exact evaluation-configuration binding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_id: ResearchIdentifier
    version: int = Field(ge=1)
    title: Annotated[str, Field(min_length=1, max_length=200)]
    objective: EvaluationText
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_created_at(self) -> EvaluationDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("evaluation definition timestamp must be timezone-aware")
        return self


class EvaluationRequest(BaseModel):
    """Complete governed input for one deterministic labelled evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluated_at: datetime
    definition: EvaluationDefinition
    configuration: EvaluationConfiguration
    study_execution: StudyExecutionResult
    dataset: HistoricalDatasetImportResult
    ground_truth_labels: GroundTruthLabelImportResult
    predictions: Annotated[tuple[ObservationPrediction, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_time(self) -> EvaluationRequest:
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("evaluation timestamp must be timezone-aware")
        if self.definition.created_at > self.evaluated_at:
            raise ValueError("evaluation cannot precede its definition")
        if self.study_execution.metadata.completed_at > self.evaluated_at:
            raise ValueError("evaluation cannot precede governed study execution")
        return self


class ObservationEvaluation(BaseModel):
    """One immutable prediction-versus-truth fact; never an aggregate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_id: ResearchIdentifier
    channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    prediction_id: ResearchIdentifier
    predicted_outcome: PredictedOutcome
    ground_truth_label: GroundTruthLabel
    outcome: EvaluationOutcome


class EvaluationMetadata(BaseModel):
    """Factual identity, versions, and supplied evaluation time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_id: ResearchIdentifier
    evaluation_version: int = Field(ge=1)
    evaluated_at: datetime
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    study_execution_id: ResearchIdentifier
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    label_set_id: ResearchIdentifier
    label_set_version: int = Field(ge=1)


class EvaluationManifest(BaseModel):
    """Content-addressed identities for every evaluation input and result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    study_execution_digest: LabelContentDigest
    dataset_digest: LabelContentDigest
    ground_truth_label_digest: LabelContentDigest
    predictions_digest: LabelContentDigest
    result_digest: LabelContentDigest


class EvaluationResult(BaseModel):
    """Immutable canonically ordered observation-level evaluation artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: EvaluationMetadata
    observations: Annotated[tuple[ObservationEvaluation, ...], Field(min_length=1)]
    manifest: EvaluationManifest

