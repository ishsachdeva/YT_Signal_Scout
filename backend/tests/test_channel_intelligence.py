"""Deterministic coverage for governed channel intelligence."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.services.backtesting import (
    ChannelIntelligenceCanonicalizer,
    ChannelIntelligenceConfiguration,
    ChannelIntelligenceDefinition,
    ChannelIntelligenceDigestMismatchError,
    ChannelIntelligenceRequest,
    ChannelIntelligenceService,
    ChannelIntelligenceValidationError,
    LabelContentDigest,
    MissingValueKind,
)
from app.services.youtube.models import (
    Channel,
    ChannelStatistics,
    LiveState,
    PrivacyStatus,
    Video,
    VideoAvailability,
    VideoFormat,
)

NOW = datetime(2026, 7, 24, 12, tzinfo=timezone.utc)


def channel(subscribers: int | None = 100, *, hidden: bool = False) -> Channel:
    return Channel(
        id="channel-1",
        title="Channel",
        statistics=ChannelStatistics(
            view_count=10_000,
            subscriber_count=subscribers,
            subscriber_count_hidden=hidden,
            video_count=20,
        ),
    )


def video(
    identity: str,
    days_ago: int,
    views: int | None,
    video_format: VideoFormat = VideoFormat.STANDARD,
    *,
    published_at: datetime | None = None,
) -> Video:
    return Video(
        id=identity,
        channel_id="channel-1",
        title=identity,
        published_at=published_at if published_at is not None else NOW - timedelta(days=days_ago),
        view_count=views,
        privacy_status=PrivacyStatus.PUBLIC,
        availability=VideoAvailability.AVAILABLE,
        live_state=(
            LiveState.COMPLETE
            if video_format is VideoFormat.LIVE_REPLAY
            else LiveState.NOT_LIVE
        ),
        format=video_format,
    )


def request_for(
    videos: tuple[Video, ...], source_channel: Channel | None = None
) -> ChannelIntelligenceRequest:
    source_channel = source_channel or channel()
    digest = ChannelIntelligenceCanonicalizer.calculate_source_digest(source_channel, videos)
    return ChannelIntelligenceRequest(
        evaluated_at=NOW,
        definition=ChannelIntelligenceDefinition(
            channel_intelligence_id="channel-intelligence.v1",
            version=1,
            title="Channel intelligence",
            objective="Calculate immutable factual channel characteristics.",
            configuration_id="channel-intelligence-config.v1",
            configuration_version=1,
            created_at=NOW - timedelta(days=100),
        ),
        configuration=ChannelIntelligenceConfiguration(
            configuration_id="channel-intelligence-config.v1",
            version=1,
            source_schema_version=1,
            eligibility_policy_version=1,
            canonical_ordering="published_at_ascending_video_id_ascending_missing_last",
        ),
        channel=source_channel,
        videos=videos,
        source_digest=LabelContentDigest(algorithm="sha256", value=digest),
    )


def test_normal_channel_and_mathematical_correctness() -> None:
    videos = tuple(
        video(identity, days, views, video_format)
        for identity, days, views, video_format in (
            ("v1", 50, 50, VideoFormat.STANDARD),
            ("v2", 40, 101, VideoFormat.SHORT),
            ("v3", 30, 201, VideoFormat.STANDARD),
            ("v4", 20, 501, VideoFormat.SHORT),
            ("v5", 10, 1001, VideoFormat.LIVE_REPLAY),
        )
    )
    result = ChannelIntelligenceService().analyze(request_for(videos))
    population = result.summary.video_population
    assert (population.total_videos, population.eligible_videos) == (5, 5)
    assert (
        population.long_form_videos,
        population.shorts,
        population.livestream_replays,
    ) == (2, 2, 1)
    ratios = result.summary.view_subscriber_analysis
    assert ratios.videos_exceeding_subscriber_count == 4
    assert ratios.videos_below_subscriber_count == 1
    assert ratios.percentage_exceeding_subscriber_count == 80
    assert ratios.percentage_exceeding_2x_subscriber_count == 60
    assert ratios.percentage_exceeding_5x_subscriber_count == 40
    assert ratios.percentage_exceeding_10x_subscriber_count == 20
    assert ratios.lowest_view_subscriber_ratio == 0.5
    assert ratios.highest_view_subscriber_ratio == 10.01
    assert ratios.mean_view_subscriber_ratio == pytest.approx(3.708)
    assert ratios.median_view_subscriber_ratio == 2.01
    upload = result.summary.upload_behaviour
    assert upload.median_upload_interval_days == 10
    assert upload.mean_upload_interval_days == 10
    assert upload.upload_frequency_per_week == pytest.approx(0.875)
    assert upload.days_since_latest_upload == 10


@pytest.mark.parametrize(
    ("video_format", "long_form", "shorts"),
    ((VideoFormat.SHORT, 0, 2), (VideoFormat.STANDARD, 2, 0)),
)
def test_format_only_channels(video_format: VideoFormat, long_form: int, shorts: int) -> None:
    videos = (video("v1", 20, 100, video_format), video("v2", 10, 200, video_format))
    population = ChannelIntelligenceService().analyze(request_for(videos)).summary.video_population
    assert population.long_form_videos == long_form
    assert population.shorts == shorts


def test_single_video_channel_has_no_interval() -> None:
    result = ChannelIntelligenceService().analyze(request_for((video("v1", 10, 100),)))
    assert result.summary.upload_behaviour.upload_frequency_per_week == 1
    assert result.summary.upload_behaviour.median_upload_interval_days is None
    assert result.summary.eligible_view_distribution.population_standard_deviation == 0


def test_zero_eligible_videos_produces_empty_descriptive_domains() -> None:
    result = ChannelIntelligenceService().analyze(request_for((video("old", 100, 100),)))
    assert result.summary.video_population.eligible_videos == 0
    assert result.summary.eligible_view_distribution.count == 0
    assert result.summary.upload_behaviour.upload_frequency_per_week is None
    assert result.summary.data_quality.excluded_videos == 1
    assert result.summary.view_subscriber_analysis.percentage_exceeding_subscriber_count == 0


def test_duplicate_videos_are_rejected() -> None:
    item = video("duplicate", 10, 100)
    with pytest.raises(ChannelIntelligenceValidationError, match="duplicate videos"):
        ChannelIntelligenceService().analyze(request_for((item, item)))


def test_unordered_videos_are_rejected() -> None:
    with pytest.raises(ChannelIntelligenceValidationError, match="canonical chronological"):
        ChannelIntelligenceService().analyze(
            request_for((video("new", 10, 100), video("old", 20, 100)))
        )


def test_malformed_timestamp_is_rejected() -> None:
    naive = video("naive", 10, 100, published_at=datetime(2026, 7, 1, 12))
    with pytest.raises(ChannelIntelligenceValidationError, match="timezone-aware"):
        ChannelIntelligenceService().analyze(request_for((naive,)))


def test_source_digest_corruption_is_rejected() -> None:
    request = request_for((video("v1", 10, 100),)).model_copy(
        update={"source_digest": LabelContentDigest(algorithm="sha256", value="f" * 64)}
    )
    with pytest.raises(ChannelIntelligenceDigestMismatchError, match="source digest"):
        ChannelIntelligenceService().analyze(request)


def test_result_digest_corruption_is_rejected() -> None:
    result = ChannelIntelligenceService().analyze(request_for((video("v1", 10, 100),)))
    corrupt = result.model_copy(
        update={
            "manifest": result.manifest.model_copy(
                update={"result_digest": LabelContentDigest(algorithm="sha256", value="f" * 64)}
            )
        }
    )
    with pytest.raises(ChannelIntelligenceDigestMismatchError, match="canonical content"):
        ChannelIntelligenceCanonicalizer.serialize_result(corrupt)


def test_serialization_is_deterministic_compact_sorted_utf8() -> None:
    result = ChannelIntelligenceService().analyze(request_for((video("v1", 10, 100),)))
    first = ChannelIntelligenceCanonicalizer.serialize_result(result)
    second = ChannelIntelligenceCanonicalizer.serialize_result(result)
    assert first == second
    assert b"\n" not in first and b" " not in first
    assert first == json.dumps(
        result.model_dump(mode="json"),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def test_missing_values_and_hidden_subscribers_are_factual() -> None:
    missing = video("missing", 10, None).model_copy(update={"published_at": None})
    result = ChannelIntelligenceService().analyze(
        request_for((missing,), channel(subscribers=None, hidden=True))
    )
    kinds = {item.kind for item in result.summary.data_quality.missing_values}
    assert kinds == {
        MissingValueKind.SUBSCRIBER_COUNT,
        MissingValueKind.VIDEO_PUBLICATION_TIME,
        MissingValueKind.VIDEO_VIEW_COUNT,
    }
    assert result.summary.view_subscriber_analysis.mean_view_subscriber_ratio is None
