"""Pure deterministic research facts for one immutable channel population."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from statistics import fmean, median, pstdev
from typing import Iterable, cast

from app.services.analytics.eligibility import EligibleVideoClassifier, VideoExclusion
from app.services.analytics.models import ChannelAnalytics
from app.services.backtesting.channel_intelligence_canonicalizer import (
    ChannelIntelligenceCanonicalizer,
)
from app.services.backtesting.channel_intelligence_models import (
    CHANNEL_INTELLIGENCE_SCHEMA_VERSION,
    ChannelIntelligenceManifest,
    ChannelIntelligenceMetadata,
    ChannelIntelligenceRequest,
    ChannelIntelligenceResult,
    ChannelIntelligenceSummary,
    DataQualitySummary,
    DescriptiveDistribution,
    ExclusionReasonSummary,
    MissingValueKind,
    MissingValueSummary,
    SubscriberDataState,
    UploadBehaviourSummary,
    VideoPopulationSummary,
    ViewSubscriberAnalysis,
)
from app.services.backtesting.exceptions import (
    ChannelIntelligenceDigestMismatchError,
    ChannelIntelligenceValidationError,
)
from app.services.backtesting.label_models import LabelContentDigest
from app.services.youtube.models import Channel, Video

_SECONDS_PER_DAY = 86_400
_DAYS_PER_WEEK = 7


def _ordering_key(video: Video) -> tuple[bool, datetime, str]:
    published_at = video.published_at
    return (
        published_at is None,
        published_at or datetime.max.replace(tzinfo=timezone.utc),
        video.id,
    )


class ChannelIntelligenceValidator:
    """Reject corrupt, unordered, duplicate, mismatched, or mutable inputs."""

    def validate(self, request: ChannelIntelligenceRequest) -> None:
        if not isinstance(request, ChannelIntelligenceRequest):
            self._fail("typed channel intelligence request is required")
        if not isinstance(request.videos, tuple):
            self._fail("channel intelligence videos must be an immutable tuple")

        definition = request.definition
        configuration = request.configuration
        if (definition.configuration_id, definition.configuration_version) != (
            configuration.configuration_id,
            configuration.version,
        ):
            self._fail("channel intelligence definition configuration mismatch")
        if configuration.source_schema_version != CHANNEL_INTELLIGENCE_SCHEMA_VERSION:
            self._fail("channel intelligence source schema-version mismatch")

        identities = (definition.channel_intelligence_id, configuration.configuration_id)
        if len(set(identities)) != len(identities):
            self._fail("channel intelligence identities must be unique")

        video_ids = tuple(video.id for video in request.videos)
        if len(set(video_ids)) != len(video_ids):
            self._fail("duplicate videos are not permitted")
        if any(video.channel_id != request.channel.id for video in request.videos):
            self._fail("every video identity must bind to the requested channel")
        for video in request.videos:
            published_at = video.published_at
            if published_at is not None:
                if published_at.tzinfo is None or published_at.utcoffset() is None:
                    self._fail(f"video publication timestamp must be timezone-aware: {video.id}")
                if published_at > request.evaluated_at:
                    self._fail(f"video publication timestamp cannot be in the future: {video.id}")
            if video.view_count is not None and (
                type(video.view_count) is not int or video.view_count < 0
            ):
                self._fail(f"video view count must be a non-negative integer: {video.id}")

        expected_order = tuple(sorted(request.videos, key=_ordering_key))
        if request.videos != expected_order:
            self._fail("videos must use canonical chronological ordering")

        expected_digest = ChannelIntelligenceCanonicalizer.calculate_source_digest(
            request.channel, request.videos
        )
        if expected_digest != request.source_digest.value:
            raise ChannelIntelligenceDigestMismatchError(
                ("channel intelligence source digest does not match canonical input",)
            )

    @staticmethod
    def _fail(issue: str) -> None:
        raise ChannelIntelligenceValidationError((issue,))


class ChannelIntelligenceService:
    """Transform one valid immutable population into descriptive facts only."""

    def __init__(
        self,
        validator: ChannelIntelligenceValidator | None = None,
        classifier: EligibleVideoClassifier | None = None,
    ) -> None:
        self._validator = validator or ChannelIntelligenceValidator()
        self._classifier = classifier or EligibleVideoClassifier()

    def analyze(self, request: ChannelIntelligenceRequest) -> ChannelIntelligenceResult:
        self._validator.validate(request)
        classification = self._classifier.classify(
            ChannelAnalytics(
                channel=request.channel,
                videos=list(request.videos),
                generated_at=request.evaluated_at,
            ),
            request.evaluated_at,
        )
        eligible = tuple(
            sorted(
                classification.eligible_standard_videos
                + classification.eligible_shorts
                + classification.eligible_livestream_replays,
                key=_ordering_key,
            )
        )
        publication_times = tuple(
            cast(datetime, video.published_at)
            for video in request.videos
            if video.published_at is not None
        )
        view_counts = tuple(cast(int, video.view_count) for video in eligible)

        summary = ChannelIntelligenceSummary(
            video_population=VideoPopulationSummary(
                total_videos=len(request.videos),
                eligible_videos=len(eligible),
                long_form_videos=len(classification.eligible_standard_videos),
                shorts=len(classification.eligible_shorts),
                livestream_replays=len(classification.eligible_livestream_replays),
                earliest_upload=min(publication_times) if publication_times else None,
                latest_upload=max(publication_times) if publication_times else None,
            ),
            view_subscriber_analysis=self._view_subscriber_analysis(
                request.channel, view_counts
            ),
            upload_behaviour=self._upload_behaviour(eligible, request.evaluated_at),
            eligible_view_distribution=self._distribution(view_counts),
            data_quality=self._data_quality(request, classification.exclusions, len(eligible)),
        )
        definition = request.definition
        configuration = request.configuration
        metadata = ChannelIntelligenceMetadata(
            channel_intelligence_id=definition.channel_intelligence_id,
            channel_intelligence_version=definition.version,
            configuration_id=configuration.configuration_id,
            configuration_version=configuration.version,
            channel_id=request.channel.id,
            evaluated_at=request.evaluated_at,
        )
        provisional_manifest = ChannelIntelligenceManifest(
            schema_version=CHANNEL_INTELLIGENCE_SCHEMA_VERSION,
            source_digest=request.source_digest,
            result_digest=LabelContentDigest(algorithm="sha256", value="0" * 64),
        )
        digest = ChannelIntelligenceCanonicalizer.calculate_result_digest(
            metadata, summary, provisional_manifest
        )
        return ChannelIntelligenceResult(
            metadata=metadata,
            summary=summary,
            manifest=provisional_manifest.model_copy(
                update={"result_digest": LabelContentDigest(algorithm="sha256", value=digest)}
            ),
        )

    @staticmethod
    def _distribution(values: tuple[int, ...]) -> DescriptiveDistribution:
        if not values:
            return DescriptiveDistribution(
                count=0,
                minimum=None,
                maximum=None,
                mean=None,
                median=None,
                population_standard_deviation=None,
            )
        return DescriptiveDistribution(
            count=len(values),
            minimum=float(min(values)),
            maximum=float(max(values)),
            mean=fmean(values),
            median=float(median(values)),
            population_standard_deviation=pstdev(values),
        )

    @staticmethod
    def _subscriber_state(channel: Channel) -> tuple[SubscriberDataState, int | None]:
        if channel.statistics is None:
            return SubscriberDataState.MISSING_STATISTICS, None
        if channel.statistics.subscriber_count_hidden:
            return SubscriberDataState.HIDDEN, None
        count = channel.statistics.subscriber_count
        if count is None:
            return SubscriberDataState.HIDDEN, None
        if count == 0:
            return SubscriberDataState.ZERO, 0
        return SubscriberDataState.AVAILABLE_POSITIVE, count

    @classmethod
    def _view_subscriber_analysis(
        cls, channel: Channel, views: tuple[int, ...]
    ) -> ViewSubscriberAnalysis:
        state, subscriber_count = cls._subscriber_state(channel)
        if state is not SubscriberDataState.AVAILABLE_POSITIVE:
            return ViewSubscriberAnalysis(
                subscriber_state=state,
                subscriber_count=subscriber_count,
                videos_exceeding_subscriber_count=None,
                videos_below_subscriber_count=None,
                percentage_exceeding_subscriber_count=None,
                percentage_exceeding_2x_subscriber_count=None,
                percentage_exceeding_5x_subscriber_count=None,
                percentage_exceeding_10x_subscriber_count=None,
                highest_view_subscriber_ratio=None,
                lowest_view_subscriber_ratio=None,
                mean_view_subscriber_ratio=None,
                median_view_subscriber_ratio=None,
            )
        denominator = cast(int, subscriber_count)
        ratios = tuple(view / denominator for view in views)
        percentage = lambda multiplier: (
            sum(view > multiplier * denominator for view in views) / len(views) * 100
            if views
            else 0.0
        )
        return ViewSubscriberAnalysis(
            subscriber_state=state,
            subscriber_count=denominator,
            videos_exceeding_subscriber_count=sum(view > denominator for view in views),
            videos_below_subscriber_count=sum(view < denominator for view in views),
            percentage_exceeding_subscriber_count=percentage(1),
            percentage_exceeding_2x_subscriber_count=percentage(2),
            percentage_exceeding_5x_subscriber_count=percentage(5),
            percentage_exceeding_10x_subscriber_count=percentage(10),
            highest_view_subscriber_ratio=max(ratios) if ratios else None,
            lowest_view_subscriber_ratio=min(ratios) if ratios else None,
            mean_view_subscriber_ratio=fmean(ratios) if ratios else None,
            median_view_subscriber_ratio=float(median(ratios)) if ratios else None,
        )

    @staticmethod
    def _upload_behaviour(
        eligible: tuple[Video, ...], evaluated_at: datetime
    ) -> UploadBehaviourSummary:
        dates = tuple(cast(datetime, video.published_at) for video in eligible)
        if not dates:
            return UploadBehaviourSummary(
                upload_frequency_per_week=None,
                median_upload_interval_days=None,
                mean_upload_interval_days=None,
                days_since_latest_upload=None,
            )
        latest = max(dates)
        frequency = 1.0
        intervals: tuple[float, ...] = ()
        if len(dates) > 1:
            elapsed_days = max((latest - min(dates)).total_seconds() / _SECONDS_PER_DAY, 1.0)
            frequency = len(dates) / elapsed_days * _DAYS_PER_WEEK
            ordered = tuple(sorted(dates))
            intervals = tuple(
                (current - previous).total_seconds() / _SECONDS_PER_DAY
                for previous, current in zip(ordered, ordered[1:])
            )
        return UploadBehaviourSummary(
            upload_frequency_per_week=frequency,
            median_upload_interval_days=float(median(intervals)) if intervals else None,
            mean_upload_interval_days=fmean(intervals) if intervals else None,
            days_since_latest_upload=(evaluated_at - latest).total_seconds() / _SECONDS_PER_DAY,
        )

    @staticmethod
    def _data_quality(
        request: ChannelIntelligenceRequest,
        exclusions: Iterable[VideoExclusion],
        eligible_count: int,
    ) -> DataQualitySummary:
        reason_counts = Counter(exclusion.reason for exclusion in exclusions)
        missing_counts: Counter[MissingValueKind] = Counter()
        if request.channel.statistics is None:
            missing_counts[MissingValueKind.CHANNEL_STATISTICS] += 1
        elif request.channel.statistics.subscriber_count is None:
            missing_counts[MissingValueKind.SUBSCRIBER_COUNT] += 1
        for video in request.videos:
            if video.published_at is None:
                missing_counts[MissingValueKind.VIDEO_PUBLICATION_TIME] += 1
            if video.view_count is None:
                missing_counts[MissingValueKind.VIDEO_VIEW_COUNT] += 1
        return DataQualitySummary(
            qualified_videos=eligible_count,
            excluded_videos=len(request.videos) - eligible_count,
            exclusion_reasons=tuple(
                ExclusionReasonSummary(reason=reason, count=count)
                for reason, count in sorted(reason_counts.items(), key=lambda item: item[0].value)
            ),
            missing_values=tuple(
                MissingValueSummary(kind=kind, count=count)
                for kind, count in sorted(missing_counts.items(), key=lambda item: item[0].value)
            ),
            canonical_ordering_confirmed=True,
        )
