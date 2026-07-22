"""Immutable domain contracts for subscriber-relative threshold backtesting."""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.analytics.qualification import (
    QualificationFailureReason,
    SubscriberRelativeAnalysisResult,
    SubscriberState,
)

ResearchIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
    ),
]


class ComparisonOperator(StrEnum):
    """Closed comparison operators retained for threshold research."""

    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"


class BacktestExclusionReason(StrEnum):
    """Normal reasons a valid observation cannot enter threshold evaluation."""

    UNQUALIFIED_ANALYSIS = "unqualified_analysis"
    MEDIAN_VSR_UNAVAILABLE = "median_vsr_unavailable"
    NO_MATCHING_SUBSCRIBER_BAND = "no_matching_subscriber_band"


class SubscriberRelativeBacktestObservation(BaseModel):
    """Minimum immutable historical input needed for subscriber-band research."""

    model_config = ConfigDict(frozen=True)

    observation_id: ResearchIdentifier
    channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    observed_at: datetime
    subscriber_count: int = Field(gt=0)
    analysis: SubscriberRelativeAnalysisResult

    @model_validator(mode="after")
    def validate_consistency(self) -> SubscriberRelativeBacktestObservation:
        qualification = self.analysis.qualification
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("backtest observation timestamp must be timezone-aware")
        if qualification.evaluated_at != self.observed_at:
            raise ValueError("analysis evaluation timestamp must match observation timestamp")
        if qualification.provenance.source_channel_id != self.channel_id:
            raise ValueError("analysis provenance channel must match observation channel")
        if qualification.subscriber_state is not SubscriberState.AVAILABLE_POSITIVE:
            raise ValueError(
                "positive backtest subscriber count requires available-positive subscriber state"
            )
        if (
            qualification.eligible_standard_video_count
            != self.analysis.analytics.eligible_standard_video_count
        ):
            raise ValueError("qualification and analytics eligible counts must match")
        median_vsr = self.analysis.analytics.median_standard_video_vsr
        if median_vsr is not None and (
            not math.isfinite(median_vsr) or median_vsr < 0
        ):
            raise ValueError("median standard-video VSR must be finite and non-negative")
        return self


class SubscriberRelativeBacktestDataset(BaseModel):
    """Versioned immutable historical observation cohort."""

    model_config = ConfigDict(frozen=True)

    dataset_id: ResearchIdentifier
    version: int = Field(ge=1)
    observations: tuple[SubscriberRelativeBacktestObservation, ...]


class SubscriberBandDefinition(BaseModel):
    """One inclusive-lower, exclusive-upper positive subscriber range."""

    model_config = ConfigDict(frozen=True)

    band_id: ResearchIdentifier
    lower_bound: int = Field(gt=0)
    upper_bound: int | None = Field(default=None, gt=0)
    label: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_bounds(self) -> SubscriberBandDefinition:
        if self.upper_bound is not None and self.upper_bound <= self.lower_bound:
            raise ValueError("subscriber band upper bound must exceed lower bound")
        return self

    def contains(self, subscriber_count: int) -> bool:
        """Return whether the positive count belongs to this half-open band."""
        return self.lower_bound <= subscriber_count and (
            self.upper_bound is None or subscriber_count < self.upper_bound
        )


class SubscriberBandSet(BaseModel):
    """Explicitly ordered, versioned subscriber-band research configuration."""

    model_config = ConfigDict(frozen=True)

    band_set_id: ResearchIdentifier
    version: int = Field(ge=1)
    bands: Annotated[tuple[SubscriberBandDefinition, ...], Field(min_length=1)]
    allow_gaps: bool = False

    @model_validator(mode="after")
    def validate_bands(self) -> SubscriberBandSet:
        identifiers = tuple(band.band_id for band in self.bands)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("subscriber band IDs must be unique")
        if not self.allow_gaps and self.bands[0].lower_bound != 1:
            raise ValueError("subscriber band gaps require allow_gaps=true")
        if not self.allow_gaps and self.bands[-1].upper_bound is not None:
            raise ValueError("subscriber band gaps require allow_gaps=true")
        for index, band in enumerate(self.bands):
            if band.upper_bound is None and index != len(self.bands) - 1:
                raise ValueError("only the final subscriber band may be unbounded")
            if index == 0:
                continue
            previous = self.bands[index - 1]
            if previous.upper_bound is None:
                raise ValueError("an unbounded subscriber band must be final")
            if band.lower_bound < previous.upper_bound:
                raise ValueError("subscriber bands must not overlap")
            if not self.allow_gaps and band.lower_bound != previous.upper_bound:
                raise ValueError("subscriber band gaps require allow_gaps=true")
        return self

    def assign(self, subscriber_count: int) -> SubscriberBandDefinition | None:
        """Return the sole configured band for a positive subscriber count."""
        matches = tuple(band for band in self.bands if band.contains(subscriber_count))
        if len(matches) > 1:
            raise ValueError("subscriber count matched more than one configured band")
        return matches[0] if matches else None


class MedianVsrThresholdCandidate(BaseModel):
    """One explicitly identified median-VSR threshold research candidate."""

    model_config = ConfigDict(frozen=True)

    candidate_id: ResearchIdentifier
    threshold: float = Field(ge=0)
    operator: ComparisonOperator

    @model_validator(mode="after")
    def validate_threshold(self) -> MedianVsrThresholdCandidate:
        if not math.isfinite(self.threshold):
            raise ValueError("median VSR threshold must be finite")
        return self

    def matches(self, observed_value: float) -> bool:
        """Compare without rounding according to the configured operator."""
        if self.operator is ComparisonOperator.GREATER_THAN:
            return observed_value > self.threshold
        return observed_value >= self.threshold


class MedianVsrThresholdSet(BaseModel):
    """Explicitly ordered, versioned threshold research configuration."""

    model_config = ConfigDict(frozen=True)

    threshold_set_id: ResearchIdentifier
    version: int = Field(ge=1)
    candidates: Annotated[
        tuple[MedianVsrThresholdCandidate, ...], Field(min_length=1)
    ]

    @model_validator(mode="after")
    def validate_candidates(self) -> MedianVsrThresholdSet:
        identifiers = tuple(candidate.candidate_id for candidate in self.candidates)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("threshold candidate IDs must be unique")
        return self


class QualificationCoverageSummary(BaseModel):
    """Factual qualification and metric-availability coverage counts."""

    model_config = ConfigDict(frozen=True)

    total_observations: int = Field(ge=0)
    qualified_observations: int = Field(ge=0)
    unqualified_observations: int = Field(ge=0)
    qualified_percentage: float | None = Field(default=None, ge=0, le=1)
    median_vsr_available_count: int = Field(ge=0)
    median_vsr_unavailable_count: int = Field(ge=0)
    threshold_eligible_count: int = Field(ge=0)
    threshold_excluded_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_counts(self) -> QualificationCoverageSummary:
        if self.qualified_observations + self.unqualified_observations != self.total_observations:
            raise ValueError("qualified and unqualified counts must cover observations")
        if (
            self.median_vsr_available_count + self.median_vsr_unavailable_count
            != self.total_observations
        ):
            raise ValueError("median availability counts must cover observations")
        if (
            self.threshold_eligible_count + self.threshold_excluded_count
            != self.total_observations
        ):
            raise ValueError("threshold coverage counts must cover observations")
        expected_percentage = (
            None
            if self.total_observations == 0
            else self.qualified_observations / self.total_observations
        )
        if self.qualified_percentage != expected_percentage:
            raise ValueError("qualified percentage must match coverage counts")
        return self


class DistributionSummary(BaseModel):
    """Deterministic unrounded distribution statistics for eligible VSR values."""

    model_config = ConfigDict(frozen=True)

    eligible_observation_count: int = Field(ge=0)
    minimum: float | None
    maximum: float | None
    arithmetic_mean: float | None
    median: float | None

    @model_validator(mode="after")
    def validate_availability(self) -> DistributionSummary:
        statistics = (
            self.minimum,
            self.maximum,
            self.arithmetic_mean,
            self.median,
        )
        if self.eligible_observation_count == 0 and any(
            value is not None for value in statistics
        ):
            raise ValueError("empty distributions must have unavailable statistics")
        if self.eligible_observation_count > 0 and any(
            value is None for value in statistics
        ):
            raise ValueError("non-empty distributions require every statistic")
        return self


class ThresholdEvaluationResult(BaseModel):
    """Factual result for one subscriber-band and threshold-candidate pair."""

    model_config = ConfigDict(frozen=True)

    band_id: ResearchIdentifier
    candidate_id: ResearchIdentifier
    threshold: float = Field(ge=0)
    operator: ComparisonOperator
    band_set_version: int = Field(ge=1)
    threshold_set_version: int = Field(ge=1)
    eligible_observation_count: int = Field(ge=0)
    hit_count: int = Field(ge=0)
    non_hit_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    hit_rate: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_counts(self) -> ThresholdEvaluationResult:
        if self.hit_count + self.non_hit_count != self.eligible_observation_count:
            raise ValueError("hit and non-hit counts must cover eligible observations")
        expected_rate = (
            None
            if self.eligible_observation_count == 0
            else self.hit_count / self.eligible_observation_count
        )
        if self.hit_rate != expected_rate:
            raise ValueError("hit rate must match threshold counts")
        return self


class QualificationFailureCount(BaseModel):
    """Count of one existing qualification failure in enum order."""

    model_config = ConfigDict(frozen=True)

    failure: QualificationFailureReason
    count: int = Field(gt=0)


class BacktestExclusion(BaseModel):
    """Normal typed exclusion retained in canonical observation order."""

    model_config = ConfigDict(frozen=True)

    observation_id: ResearchIdentifier
    channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    reason: BacktestExclusionReason
    qualification_failures: tuple[QualificationFailureReason, ...] = ()


class SubscriberBandBacktestResult(BaseModel):
    """Coverage, distribution, and candidate results for one configured band."""

    model_config = ConfigDict(frozen=True)

    band_id: ResearchIdentifier
    coverage: QualificationCoverageSummary
    distribution: DistributionSummary
    threshold_results: tuple[ThresholdEvaluationResult, ...]


class ThresholdBacktestReport(BaseModel):
    """Serializable immutable factual report for one complete backtest invocation."""

    model_config = ConfigDict(frozen=True)

    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    band_set_id: ResearchIdentifier
    band_set_version: int = Field(ge=1)
    threshold_set_id: ResearchIdentifier
    threshold_set_version: int = Field(ge=1)
    generated_at: datetime
    source_observation_count: int = Field(ge=0)
    global_coverage: QualificationCoverageSummary
    qualification_failure_counts: tuple[QualificationFailureCount, ...]
    band_results: tuple[SubscriberBandBacktestResult, ...]
    exclusions: tuple[BacktestExclusion, ...]

    @model_validator(mode="after")
    def validate_report(self) -> ThresholdBacktestReport:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("report generation time must be timezone-aware")
        if self.source_observation_count != self.global_coverage.total_observations:
            raise ValueError("source observation count must match global coverage")
        return self
