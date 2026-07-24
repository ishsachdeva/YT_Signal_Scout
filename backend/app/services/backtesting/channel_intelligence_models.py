"""Immutable contracts for governed channel intelligence."""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.analytics.eligibility import VideoExclusionReason
from app.services.backtesting.label_models import LabelContentDigest
from app.services.backtesting.models import ResearchIdentifier
from app.services.youtube.models import Channel, Video

CHANNEL_INTELLIGENCE_SCHEMA_VERSION = 1
FiniteNonNegative = Annotated[float, Field(ge=0)]
Percentage = Annotated[float, Field(ge=0, le=100)]


class SubscriberDataState(StrEnum):
    """Factual subscriber denominator state at evaluation time."""

    AVAILABLE_POSITIVE = "available_positive"
    HIDDEN = "hidden"
    ZERO = "zero"
    MISSING_STATISTICS = "missing_statistics"


class MissingValueKind(StrEnum):
    """Closed missing-value facts reported by intelligence schema v1."""

    CHANNEL_STATISTICS = "channel_statistics"
    SUBSCRIBER_COUNT = "subscriber_count"
    VIDEO_PUBLICATION_TIME = "video_publication_time"
    VIDEO_VIEW_COUNT = "video_view_count"


class ChannelIntelligenceDefinition(BaseModel):
    """Versioned factual research purpose and configuration binding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel_intelligence_id: ResearchIdentifier
    version: int = Field(ge=1, strict=True)
    title: Annotated[str, Field(min_length=1, max_length=200)]
    objective: Annotated[str, Field(min_length=1, max_length=4_000)]
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1, strict=True)
    created_at: datetime

    @model_validator(mode="after")
    def validate_time(self) -> ChannelIntelligenceDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("channel intelligence definition timestamp must be timezone-aware")
        return self


class ChannelIntelligenceConfiguration(BaseModel):
    """Versioned source-schema and eligibility-policy bindings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    configuration_id: ResearchIdentifier
    version: int = Field(ge=1, strict=True)
    source_schema_version: Literal[1]
    eligibility_policy_version: Literal[1]
    canonical_ordering: Literal["published_at_ascending_video_id_ascending_missing_last"]


class ChannelIntelligenceRequest(BaseModel):
    """One immutable channel, canonical population, and declared source digest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluated_at: datetime
    definition: ChannelIntelligenceDefinition
    configuration: ChannelIntelligenceConfiguration
    channel: Channel
    videos: tuple[Video, ...]
    source_digest: LabelContentDigest

    @model_validator(mode="after")
    def validate_time(self) -> ChannelIntelligenceRequest:
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("channel intelligence evaluation timestamp must be timezone-aware")
        if self.definition.created_at > self.evaluated_at:
            raise ValueError("channel intelligence cannot precede its definition")
        return self


class DescriptiveDistribution(BaseModel):
    """Deterministic population statistics without inference."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    count: int = Field(ge=0, strict=True)
    minimum: FiniteNonNegative | None
    maximum: FiniteNonNegative | None
    mean: FiniteNonNegative | None
    median: FiniteNonNegative | None
    population_standard_deviation: FiniteNonNegative | None

    @model_validator(mode="after")
    def validate_domain(self) -> DescriptiveDistribution:
        values = (
            self.minimum,
            self.maximum,
            self.mean,
            self.median,
            self.population_standard_deviation,
        )
        if any(value is not None and not math.isfinite(value) for value in values):
            raise ValueError("distribution values must be finite")
        if self.count == 0 and any(value is not None for value in values):
            raise ValueError("empty distributions cannot contain statistics")
        if self.count > 0 and any(value is None for value in values):
            raise ValueError("non-empty distributions require all statistics")
        if self.count > 0 and not self.minimum <= self.median <= self.maximum:
            raise ValueError("distribution median must be within its range")
        return self


class VideoPopulationSummary(BaseModel):
    """Counts and observed upload extent for the supplied population."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_videos: int = Field(ge=0, strict=True)
    eligible_videos: int = Field(ge=0, strict=True)
    long_form_videos: int = Field(ge=0, strict=True)
    shorts: int = Field(ge=0, strict=True)
    livestream_replays: int = Field(ge=0, strict=True)
    earliest_upload: datetime | None
    latest_upload: datetime | None

    @model_validator(mode="after")
    def validate_counts_and_times(self) -> VideoPopulationSummary:
        if self.eligible_videos != (
            self.long_form_videos + self.shorts + self.livestream_replays
        ):
            raise ValueError("eligible video count must equal format counts")
        if self.eligible_videos > self.total_videos:
            raise ValueError("eligible video count cannot exceed total videos")
        for value in (self.earliest_upload, self.latest_upload):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("upload timestamps must be timezone-aware")
        if (self.earliest_upload is None) != (self.latest_upload is None):
            raise ValueError("upload extent must be wholly available or unavailable")
        if self.earliest_upload is not None and self.earliest_upload > self.latest_upload:
            raise ValueError("earliest upload cannot follow latest upload")
        return self


class ViewSubscriberAnalysis(BaseModel):
    """Subscriber-relative facts, unavailable without a positive denominator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subscriber_state: SubscriberDataState
    subscriber_count: int | None = Field(default=None, ge=0, strict=True)
    videos_exceeding_subscriber_count: int | None = Field(default=None, ge=0, strict=True)
    videos_below_subscriber_count: int | None = Field(default=None, ge=0, strict=True)
    percentage_exceeding_subscriber_count: Percentage | None
    percentage_exceeding_2x_subscriber_count: Percentage | None
    percentage_exceeding_5x_subscriber_count: Percentage | None
    percentage_exceeding_10x_subscriber_count: Percentage | None
    highest_view_subscriber_ratio: FiniteNonNegative | None
    lowest_view_subscriber_ratio: FiniteNonNegative | None
    mean_view_subscriber_ratio: FiniteNonNegative | None
    median_view_subscriber_ratio: FiniteNonNegative | None

    @model_validator(mode="after")
    def validate_availability(self) -> ViewSubscriberAnalysis:
        derived = (
            self.videos_exceeding_subscriber_count,
            self.videos_below_subscriber_count,
            self.percentage_exceeding_subscriber_count,
            self.percentage_exceeding_2x_subscriber_count,
            self.percentage_exceeding_5x_subscriber_count,
            self.percentage_exceeding_10x_subscriber_count,
            self.highest_view_subscriber_ratio,
            self.lowest_view_subscriber_ratio,
            self.mean_view_subscriber_ratio,
            self.median_view_subscriber_ratio,
        )
        if any(
            value is not None
            and isinstance(value, float)
            and not math.isfinite(value)
            for value in derived
        ):
            raise ValueError("subscriber-relative values must be finite")
        if self.subscriber_state is SubscriberDataState.AVAILABLE_POSITIVE:
            if self.subscriber_count is None or self.subscriber_count <= 0:
                raise ValueError("available subscriber state requires a positive count")
        elif self.subscriber_count not in (None, 0) or any(value is not None for value in derived):
            raise ValueError("unavailable subscriber state cannot contain derived values")
        return self


class UploadBehaviourSummary(BaseModel):
    """Descriptive upload timing over eligible videos."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    upload_frequency_per_week: FiniteNonNegative | None
    median_upload_interval_days: FiniteNonNegative | None
    mean_upload_interval_days: FiniteNonNegative | None
    days_since_latest_upload: FiniteNonNegative | None


class ExclusionReasonSummary(BaseModel):
    """Count for one Eligible Video Policy v1 exclusion reason."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reason: VideoExclusionReason
    count: int = Field(gt=0, strict=True)


class MissingValueSummary(BaseModel):
    """Count for one factual missing-value kind."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: MissingValueKind
    count: int = Field(gt=0, strict=True)


class DataQualitySummary(BaseModel):
    """Factual qualification, exclusion, missingness, and ordering facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    qualified_videos: int = Field(ge=0, strict=True)
    excluded_videos: int = Field(ge=0, strict=True)
    exclusion_reasons: tuple[ExclusionReasonSummary, ...]
    missing_values: tuple[MissingValueSummary, ...]
    canonical_ordering_confirmed: Literal[True]


class ChannelIntelligenceSummary(BaseModel):
    """Complete factual channel characteristics for schema v1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    video_population: VideoPopulationSummary
    view_subscriber_analysis: ViewSubscriberAnalysis
    upload_behaviour: UploadBehaviourSummary
    eligible_view_distribution: DescriptiveDistribution
    data_quality: DataQualitySummary

    @model_validator(mode="after")
    def validate_continuity(self) -> ChannelIntelligenceSummary:
        population = self.video_population
        quality = self.data_quality
        if population.eligible_videos != quality.qualified_videos:
            raise ValueError("qualified and eligible video counts must match")
        if quality.qualified_videos + quality.excluded_videos != population.total_videos:
            raise ValueError("quality counts must equal total videos")
        if sum(item.count for item in quality.exclusion_reasons) != quality.excluded_videos:
            raise ValueError("exclusion reasons must account for every excluded video")
        if self.eligible_view_distribution.count != population.eligible_videos:
            raise ValueError("view distribution count must equal eligible videos")
        ratios = self.view_subscriber_analysis
        ratio_statistics = (
            ratios.highest_view_subscriber_ratio,
            ratios.lowest_view_subscriber_ratio,
            ratios.mean_view_subscriber_ratio,
            ratios.median_view_subscriber_ratio,
        )
        if ratios.subscriber_state is SubscriberDataState.AVAILABLE_POSITIVE:
            comparison_values = (
                ratios.videos_exceeding_subscriber_count,
                ratios.videos_below_subscriber_count,
                ratios.percentage_exceeding_subscriber_count,
                ratios.percentage_exceeding_2x_subscriber_count,
                ratios.percentage_exceeding_5x_subscriber_count,
                ratios.percentage_exceeding_10x_subscriber_count,
            )
            if any(value is None for value in comparison_values):
                raise ValueError("available subscriber analysis requires comparisons")
            if population.eligible_videos == 0 and any(
                value is not None for value in ratio_statistics
            ):
                raise ValueError("empty eligibility cannot contain ratio statistics")
            if population.eligible_videos > 0 and any(value is None for value in ratio_statistics):
                raise ValueError("non-empty eligibility requires ratio statistics")
        return self


class ChannelIntelligenceMetadata(BaseModel):
    """Definition, configuration, channel, and evaluation identities."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel_intelligence_id: ResearchIdentifier
    channel_intelligence_version: int = Field(ge=1, strict=True)
    configuration_id: ResearchIdentifier
    configuration_version: int = Field(ge=1, strict=True)
    channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    evaluated_at: datetime

    @model_validator(mode="after")
    def validate_time(self) -> ChannelIntelligenceMetadata:
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("channel intelligence metadata timestamp must be timezone-aware")
        return self


class ChannelIntelligenceManifest(BaseModel):
    """Content-addressed immutable input and output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    source_digest: LabelContentDigest
    result_digest: LabelContentDigest


class ChannelIntelligenceResult(BaseModel):
    """Immutable factual channel-intelligence artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: ChannelIntelligenceMetadata
    summary: ChannelIntelligenceSummary
    manifest: ChannelIntelligenceManifest
