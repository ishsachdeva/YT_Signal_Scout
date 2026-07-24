"""Immutable contracts for counts-only evaluation aggregation."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.label_models import LabelContentDigest
from app.services.backtesting.labelled_evaluation_models import EvaluationResult
from app.services.backtesting.models import ResearchIdentifier

EVALUATION_AGGREGATION_SCHEMA_VERSION = 1
AggregationText = Annotated[str, Field(min_length=1, max_length=4_000)]


class EvaluationAggregationConfiguration(BaseModel):
    """Versioned source identity and expected cohort size."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    configuration_id: ResearchIdentifier
    version: int = Field(ge=1)
    evaluation_id: ResearchIdentifier
    evaluation_version: int = Field(ge=1)
    evaluation_schema_version: Literal[1]
    expected_observation_count: int = Field(ge=1)


class EvaluationAggregationDefinition(BaseModel):
    """Pre-declared counts-only aggregation purpose and configuration binding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    aggregation_id: ResearchIdentifier
    version: int = Field(ge=1)
    title: Annotated[str, Field(min_length=1, max_length=200)]
    objective: AggregationText
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_created_at(self) -> EvaluationAggregationDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("aggregation definition timestamp must be timezone-aware")
        return self


class EvaluationAggregationRequest(BaseModel):
    """Complete input for one deterministic aggregation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    aggregated_at: datetime
    definition: EvaluationAggregationDefinition
    configuration: EvaluationAggregationConfiguration
    evaluation_result: EvaluationResult

    @model_validator(mode="after")
    def validate_time(self) -> EvaluationAggregationRequest:
        if self.aggregated_at.tzinfo is None or self.aggregated_at.utcoffset() is None:
            raise ValueError("aggregation timestamp must be timezone-aware")
        if self.definition.created_at > self.aggregated_at:
            raise ValueError("aggregation cannot precede its definition")
        if self.evaluation_result.metadata.evaluated_at > self.aggregated_at:
            raise ValueError("aggregation cannot precede its evaluation")
        return self


class EvaluationAggregationSummary(BaseModel):
    """Factual integer counts with no rates, percentages, or metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    true_positive_count: int = Field(ge=0)
    true_negative_count: int = Field(ge=0)
    false_positive_count: int = Field(ge=0)
    false_negative_count: int = Field(ge=0)
    unknown_count: int = Field(ge=0)
    not_evaluated_count: int = Field(ge=0)
    total_evaluated: int = Field(ge=0)
    total_observations: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_counts(self) -> EvaluationAggregationSummary:
        evaluated = (
            self.true_positive_count
            + self.true_negative_count
            + self.false_positive_count
            + self.false_negative_count
            + self.unknown_count
        )
        if self.total_evaluated != evaluated:
            raise ValueError("total evaluated must equal all non-skipped outcome counts")
        if self.total_observations != evaluated + self.not_evaluated_count:
            raise ValueError("total observations must equal every outcome count")
        return self


class EvaluationAggregationMetadata(BaseModel):
    """Factual aggregation, configuration, and source evaluation identities."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    aggregation_id: ResearchIdentifier
    aggregation_version: int = Field(ge=1)
    aggregated_at: datetime
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    evaluation_id: ResearchIdentifier
    evaluation_version: int = Field(ge=1)


class EvaluationAggregationManifest(BaseModel):
    """Content-addressed source and aggregation result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    evaluation_result_digest: LabelContentDigest
    result_digest: LabelContentDigest


class EvaluationAggregationResult(BaseModel):
    """Immutable factual cohort counts from exactly one evaluation result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: EvaluationAggregationMetadata
    summary: EvaluationAggregationSummary
    manifest: EvaluationAggregationManifest

