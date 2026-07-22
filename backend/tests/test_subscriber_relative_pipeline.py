"""Integration tests for the ADR-010 subscriber-relative pipeline."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest import TestCase
from unittest.mock import create_autospec

from pydantic import ValidationError

from app.application import create_application
from app.core.config import Settings
from app.services.analytics.composition import build_subscriber_relative_analytics_service
from app.services.analytics.eligibility import (
    EligibleVideoClassification,
    EligibleVideoClassifier,
)
from app.services.analytics.models import MetricResult, MetricType, SubscriberRelativeAnalytics
from app.services.analytics.qualification import (
    SubscriberRelativeAnalysisResult,
    SubscriberRelativeQualification,
    SubscriberRelativeQualificationService,
    SubscriberState,
)
from app.services.analytics.subscriber_relative_orchestrator import (
    SubscriberRelativeAnalyticsOrchestrator,
)
from app.services.analytics.subscriber_relative_result_assembler import (
    SubscriberRelativeResultAssembler,
)
from app.services.analytics.subscriber_relative_service import SubscriberRelativeAnalyticsService
from app.services.youtube.models import (
    AcquisitionSource,
    Channel,
    ChannelStatistics,
    LiveState,
    PaginationProvenance,
    PaginationStatus,
    PrivacyStatus,
    Video,
    VideoAcquisitionProvenance,
    VideoAcquisitionResult,
    VideoAvailability,
    VideoFormat,
)

_EVALUATION_TIME = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _videos() -> tuple[Video, ...]:
    return tuple(
        Video(
            id=f"standard-{number}",
            channel_id="channel-1",
            title=f"Standard {number}",
            published_at=_EVALUATION_TIME - timedelta(days=number),
            view_count=number * 100,
            privacy_status=PrivacyStatus.PUBLIC,
            availability=VideoAvailability.AVAILABLE,
            live_state=LiveState.NOT_LIVE,
            format=VideoFormat.STANDARD,
        )
        for number in range(1, 6)
    )


def _channel(*, hidden: bool = False) -> Channel:
    return Channel(
        id="channel-1",
        title="Channel",
        statistics=ChannelStatistics(
            view_count=1_000,
            subscriber_count=None if hidden else 100,
            subscriber_count_hidden=hidden,
            video_count=5,
        ),
    )


def _acquisition(*, duplicate_positions: bool = False) -> VideoAcquisitionResult:
    unique = _videos()
    resolved = unique + (unique[0],) if duplicate_positions else unique
    return VideoAcquisitionResult(
        resolved_discovery_videos=resolved,
        unique_canonical_videos=unique,
        provenance=VideoAcquisitionProvenance(
            source=AcquisitionSource.UPLOADS_PLAYLIST,
            source_channel_id="channel-1",
            discovery_request_capacity=50,
            discovered_position_count=len(resolved),
            discovered_unique_video_count=5,
            enrichment_requested_unique_count=5,
            enriched_unique_video_count=5,
            enriched_output_position_count=len(resolved),
            omitted_unique_video_count=0,
            pagination=PaginationProvenance(
                status=PaginationStatus.COMPLETE,
                pages_fetched=1,
                page_size_requested=50,
                page_limit=1,
                next_page_token_present=False,
                upstream_total_results=len(resolved),
            ),
        ),
    )


class SubscriberRelativePipelineIntegrationTests(TestCase):
    """Verify production composition and exactly-once stage integration."""

    def test_complete_pipeline_returns_qualification_and_factual_analytics(self) -> None:
        result = build_subscriber_relative_analytics_service().analyze(
            _channel(), _acquisition(), _EVALUATION_TIME
        )

        self.assertTrue(result.qualification.qualified)
        self.assertEqual(result.qualification.eligible_standard_video_count, 5)
        self.assertEqual(
            result.analytics,
            SubscriberRelativeAnalytics(
                eligible_standard_video_count=5,
                median_standard_video_vsr=3.0,
            ),
        )
        with self.assertRaises(ValidationError):
            result.analytics.eligible_standard_video_count = 6

    def test_complete_pipeline_is_deterministic(self) -> None:
        service = build_subscriber_relative_analytics_service()
        first = service.analyze(_channel(), _acquisition(), _EVALUATION_TIME)
        second = service.analyze(_channel(), _acquisition(), _EVALUATION_TIME)
        self.assertEqual(first, second)

    def test_factual_analytics_are_computed_when_qualification_fails(self) -> None:
        result = build_subscriber_relative_analytics_service().analyze(
            _channel(hidden=True), _acquisition(), _EVALUATION_TIME
        )

        self.assertFalse(result.qualification.qualified)
        self.assertIs(result.qualification.subscriber_state, SubscriberState.HIDDEN)
        self.assertEqual(result.analytics.eligible_standard_video_count, 5)
        self.assertIsNone(result.analytics.median_standard_video_vsr)

    def test_duplicate_discovery_positions_do_not_reach_classification(self) -> None:
        result = build_subscriber_relative_analytics_service().analyze(
            _channel(), _acquisition(duplicate_positions=True), _EVALUATION_TIME
        )
        self.assertEqual(result.analytics.eligible_standard_video_count, 5)

    def test_each_stage_is_invoked_once_with_previous_stage_output(self) -> None:
        acquisition = _acquisition()
        channel = _channel()
        classification = EligibleVideoClassification(
            eligible_standard_videos=acquisition.unique_canonical_videos,
            eligible_shorts=(),
            eligible_livestream_replays=(),
            exclusions=(),
            evaluated_at=_EVALUATION_TIME,
        )
        qualification = SubscriberRelativeQualification(
            qualified=True,
            failures=(),
            provenance=acquisition.provenance,
            requested_id_resolution_rate=1.0,
            eligible_standard_video_count=5,
            subscriber_state=SubscriberState.AVAILABLE_POSITIVE,
            evaluated_at=_EVALUATION_TIME,
        )
        metrics: tuple[MetricResult[object], ...] = (
            MetricResult[int](metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT, value=5),
            MetricResult[float | None](metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR, value=3.0),
        )
        analytics = SubscriberRelativeAnalytics(
            eligible_standard_video_count=5, median_standard_video_vsr=3.0
        )
        classifier = create_autospec(EligibleVideoClassifier, instance=True)
        qualifier = create_autospec(SubscriberRelativeQualificationService, instance=True)
        orchestrator = create_autospec(SubscriberRelativeAnalyticsOrchestrator, instance=True)
        assembler = create_autospec(SubscriberRelativeResultAssembler, instance=True)
        classifier.classify.return_value = classification
        qualifier.qualify.return_value = qualification
        orchestrator.calculate_all.return_value = metrics
        assembler.assemble.return_value = analytics
        service = SubscriberRelativeAnalyticsService(
            classifier, qualifier, orchestrator, assembler
        )

        actual = service.analyze(channel, acquisition, _EVALUATION_TIME)

        self.assertEqual(
            actual,
            SubscriberRelativeAnalysisResult(
                qualification=qualification, analytics=analytics
            ),
        )
        source_dataset = classifier.classify.call_args.args[0]
        self.assertEqual(tuple(source_dataset.videos), acquisition.unique_canonical_videos)
        classifier.classify.assert_called_once_with(source_dataset, _EVALUATION_TIME)
        qualifier.qualify.assert_called_once_with(
            acquisition.provenance, classification, channel, _EVALUATION_TIME
        )
        orchestrator.calculate_all.assert_called_once_with(classification, 100)
        assembler.assemble.assert_called_once_with(metrics)

    def test_application_composition_registers_public_service(self) -> None:
        application = create_application(Settings(environment="test", log_level="CRITICAL"))
        self.assertIsInstance(
            application.state.subscriber_relative_analytics_service,
            SubscriberRelativeAnalyticsService,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
