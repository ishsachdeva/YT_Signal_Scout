"""Immutable contracts for governed statistical evaluation."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.evaluation_aggregation_models import (
    EvaluationAggregationResult,
)
from app.services.backtesting.label_models import LabelContentDigest
from app.services.backtesting.models import ResearchIdentifier

STATISTICAL_EVALUATION_SCHEMA_VERSION = 1
StatisticalText = Annotated[str, Field(min_length=1, max_length=4_000)]
UnitInterval = Annotated[float, Field(ge=0, le=1)]


class StatisticalEvaluationConfiguration(BaseModel):
    """Versioned aggregation binding and fixed Wilson convention."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    configuration_id: ResearchIdentifier
    version: int = Field(ge=1)
    aggregation_id: ResearchIdentifier
    aggregation_version: int = Field(ge=1)
    aggregation_schema_version: Literal[1]
    confidence_level: Literal["0.95"]
    wilson_z: Literal["1.959963984540054"]


class StatisticalEvaluationDefinition(BaseModel):
    """Pre-declared mathematical purpose and configuration binding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    statistical_evaluation_id: ResearchIdentifier
    version: int = Field(ge=1)
    title: Annotated[str, Field(min_length=1, max_length=200)]
    objective: StatisticalText
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_created_at(self) -> StatisticalEvaluationDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("statistical definition timestamp must be timezone-aware")
        return self


class StatisticalEvaluationRequest(BaseModel):
    """Complete input for one deterministic statistical evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluated_at: datetime
    definition: StatisticalEvaluationDefinition
    configuration: StatisticalEvaluationConfiguration
    aggregation_result: EvaluationAggregationResult

    @model_validator(mode="after")
    def validate_time(self) -> StatisticalEvaluationRequest:
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("statistical evaluation timestamp must be timezone-aware")
        if self.definition.created_at > self.evaluated_at:
            raise ValueError("statistical evaluation cannot precede its definition")
        if self.aggregation_result.metadata.aggregated_at > self.evaluated_at:
            raise ValueError("statistical evaluation cannot precede aggregation")
        return self


class WilsonScoreInterval(BaseModel):
    """Two-sided 95% Wilson score interval under the configured convention."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    estimate: UnitInterval
    lower_bound: UnitInterval
    upper_bound: UnitInterval
    sample_size: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> WilsonScoreInterval:
        values = (self.estimate, self.lower_bound, self.upper_bound)
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Wilson interval values must be finite")
        if not self.lower_bound <= self.estimate <= self.upper_bound:
            raise ValueError("Wilson interval must contain its estimate")
        return self


class StatisticalEvaluationSummary(BaseModel):
    """Approved mathematical metrics and specified Wilson intervals only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    accuracy: UnitInterval
    precision: UnitInterval
    recall: UnitInterval
    sensitivity: UnitInterval
    specificity: UnitInterval
    negative_predictive_value: UnitInterval
    false_positive_rate: UnitInterval
    false_negative_rate: UnitInterval
    balanced_accuracy: UnitInterval
    f1_score: UnitInterval
    matthews_correlation_coefficient: Annotated[float, Field(ge=-1, le=1)]
    accuracy_interval: WilsonScoreInterval
    precision_interval: WilsonScoreInterval
    recall_interval: WilsonScoreInterval
    specificity_interval: WilsonScoreInterval
    balanced_accuracy_interval: WilsonScoreInterval

    @model_validator(mode="after")
    def validate_metrics(self) -> StatisticalEvaluationSummary:
        metrics = (
            self.accuracy,
            self.precision,
            self.recall,
            self.sensitivity,
            self.specificity,
            self.negative_predictive_value,
            self.false_positive_rate,
            self.false_negative_rate,
            self.balanced_accuracy,
            self.f1_score,
            self.matthews_correlation_coefficient,
        )
        if any(not math.isfinite(value) for value in metrics):
            raise ValueError("statistical metrics must be finite")
        if self.sensitivity != self.recall:
            raise ValueError("sensitivity must equal recall")
        interval_bindings = (
            (self.accuracy, self.accuracy_interval),
            (self.precision, self.precision_interval),
            (self.recall, self.recall_interval),
            (self.specificity, self.specificity_interval),
            (self.balanced_accuracy, self.balanced_accuracy_interval),
        )
        if any(metric != interval.estimate for metric, interval in interval_bindings):
            raise ValueError("Wilson interval estimates must match summary metrics")
        return self


class StatisticalEvaluationMetadata(BaseModel):
    """Factual statistical, configuration, and aggregation identities."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    statistical_evaluation_id: ResearchIdentifier
    statistical_evaluation_version: int = Field(ge=1)
    evaluated_at: datetime
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1)
    aggregation_id: ResearchIdentifier
    aggregation_version: int = Field(ge=1)


class StatisticalEvaluationManifest(BaseModel):
    """Content-addressed aggregation input and statistical output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    aggregation_result_digest: LabelContentDigest
    result_digest: LabelContentDigest


class StatisticalEvaluationResult(BaseModel):
    """Immutable mathematical artifact with no interpretation or ranking."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: StatisticalEvaluationMetadata
    summary: StatisticalEvaluationSummary
    manifest: StatisticalEvaluationManifest

