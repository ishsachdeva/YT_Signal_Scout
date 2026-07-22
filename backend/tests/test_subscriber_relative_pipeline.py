"""Integration tests for the subscriber-relative analytics pipeline."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest import TestCase
from unittest.mock import create_autospec

from pydantic import ValidationError

from app.application import create_application
from app.core.config import Settings
from app.services.analytics.composition import (
    build_subscriber_relative_analytics_service,
)
from app.services.analytics.eligibility import (
    EligibleVideoClassification,
    EligibleVideoClassifier,
)
from app.services.analytics.models import (
    ChannelAnalytics,
    MetricResult,
    MetricType,
    SubscriberRelativeAnalytics,
)
from app.services.analytics.subscriber_relative_orchestrator import (
    SubscriberRelativeAnalyticsOrchestrator,
)
from app.services.analytics.subscriber_relative_result_assembler import (
    SubscriberRelativeResultAssembler,
)
from app.services.analytics.subscriber_relative_service import (
    SubscriberRelativeAnalyticsService,
)
from app.services.youtube.models import (
    Channel,
    LiveState,
    PrivacyStatus,
    Video,
    VideoAvailability,
    VideoFormat,
)

_EVALUATION_TIME = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _dataset() -> ChannelAnalytics:
    return ChannelAnalytics(
        channel=Channel(id="channel-1", title="Channel"),
        videos=[
            Video(
                id="standard-1",
                channel_id="channel-1",
                title="Standard 1",
                published_at=_EVALUATION_TIME - timedelta(days=2),
                view_count=200,
                privacy_status=PrivacyStatus.PUBLIC,
                availability=VideoAvailability.AVAILABLE,
                live_state=LiveState.NOT_LIVE,
                format=VideoFormat.STANDARD,
            ),
            Video(
                id="standard-2",
                channel_id="channel-1",
                title="Standard 2",
                published_at=_EVALUATION_TIME - timedelta(days=3),
                view_count=400,
                privacy_status=PrivacyStatus.PUBLIC,
                availability=VideoAvailability.AVAILABLE,
                live_state=LiveState.NOT_LIVE,
                format=VideoFormat.STANDARD,
            ),
        ],
        generated_at=_EVALUATION_TIME,
    )


class SubscriberRelativePipelineIntegrationTests(TestCase):
    """Verify production composition and single-pass stage integration."""

    def test_complete_pipeline_returns_expected_immutable_aggregate(self) -> None:
        service = build_subscriber_relative_analytics_service()

        analytics = service.calculate(_dataset(), 100, _EVALUATION_TIME)

        self.assertEqual(
            analytics,
            SubscriberRelativeAnalytics(
                eligible_standard_video_count=2,
                median_standard_video_vsr=3.0,
            ),
        )
        with self.assertRaises(ValidationError):
            analytics.eligible_standard_video_count = 3

    def test_complete_pipeline_is_deterministic_across_repeated_execution(self) -> None:
        service = build_subscriber_relative_analytics_service()
        dataset = _dataset()

        first = service.calculate(dataset, 100, _EVALUATION_TIME)
        second = service.calculate(dataset, 100, _EVALUATION_TIME)

        self.assertEqual(first, second)

    def test_each_pipeline_stage_is_invoked_once_with_the_previous_output(self) -> None:
        dataset = _dataset()
        classification = EligibleVideoClassification(
            eligible_standard_videos=(),
            eligible_shorts=(),
            eligible_livestream_replays=(),
            exclusions=(),
            evaluated_at=_EVALUATION_TIME,
        )
        metric_results: tuple[MetricResult[object], ...] = (
            MetricResult[int](
                metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                value=0,
            ),
            MetricResult[float | None](
                metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR,
                value=None,
            ),
        )
        expected = SubscriberRelativeAnalytics(
            eligible_standard_video_count=0,
            median_standard_video_vsr=None,
        )
        classifier = create_autospec(EligibleVideoClassifier, instance=True)
        orchestrator = create_autospec(
            SubscriberRelativeAnalyticsOrchestrator,
            instance=True,
        )
        assembler = create_autospec(
            SubscriberRelativeResultAssembler,
            instance=True,
        )
        classifier.classify.return_value = classification
        orchestrator.calculate_all.return_value = metric_results
        assembler.assemble.return_value = expected
        service = SubscriberRelativeAnalyticsService(
            classifier,
            orchestrator,
            assembler,
        )

        actual = service.calculate(dataset, None, _EVALUATION_TIME)

        self.assertIs(actual, expected)
        classifier.classify.assert_called_once_with(dataset, _EVALUATION_TIME)
        orchestrator.calculate_all.assert_called_once_with(classification, None)
        assembler.assemble.assert_called_once_with(metric_results)

    def test_failure_propagates_and_stops_the_pipeline(self) -> None:
        expected_error = RuntimeError("classification failed")
        classifier = create_autospec(EligibleVideoClassifier, instance=True)
        orchestrator = create_autospec(
            SubscriberRelativeAnalyticsOrchestrator,
            instance=True,
        )
        assembler = create_autospec(
            SubscriberRelativeResultAssembler,
            instance=True,
        )
        classifier.classify.side_effect = expected_error
        service = SubscriberRelativeAnalyticsService(
            classifier,
            orchestrator,
            assembler,
        )

        with self.assertRaises(RuntimeError) as raised:
            service.calculate(_dataset(), 100, _EVALUATION_TIME)

        self.assertIs(raised.exception, expected_error)
        orchestrator.calculate_all.assert_not_called()
        assembler.assemble.assert_not_called()

    def test_orchestrator_failure_propagates_without_assembly(self) -> None:
        expected_error = RuntimeError("orchestration failed")
        classifier = create_autospec(EligibleVideoClassifier, instance=True)
        orchestrator = create_autospec(
            SubscriberRelativeAnalyticsOrchestrator,
            instance=True,
        )
        assembler = create_autospec(
            SubscriberRelativeResultAssembler,
            instance=True,
        )
        classifier.classify.return_value = EligibleVideoClassification(
            eligible_standard_videos=(),
            eligible_shorts=(),
            eligible_livestream_replays=(),
            exclusions=(),
            evaluated_at=_EVALUATION_TIME,
        )
        orchestrator.calculate_all.side_effect = expected_error
        service = SubscriberRelativeAnalyticsService(
            classifier,
            orchestrator,
            assembler,
        )

        with self.assertRaises(RuntimeError) as raised:
            service.calculate(_dataset(), 100, _EVALUATION_TIME)

        self.assertIs(raised.exception, expected_error)
        classifier.classify.assert_called_once()
        orchestrator.calculate_all.assert_called_once()
        assembler.assemble.assert_not_called()

    def test_assembler_failure_propagates(self) -> None:
        expected_error = RuntimeError("assembly failed")
        classifier = create_autospec(EligibleVideoClassifier, instance=True)
        orchestrator = create_autospec(
            SubscriberRelativeAnalyticsOrchestrator,
            instance=True,
        )
        assembler = create_autospec(
            SubscriberRelativeResultAssembler,
            instance=True,
        )
        classification = EligibleVideoClassification(
            eligible_standard_videos=(),
            eligible_shorts=(),
            eligible_livestream_replays=(),
            exclusions=(),
            evaluated_at=_EVALUATION_TIME,
        )
        metric_results: tuple[MetricResult[object], ...] = (
            MetricResult[int](
                metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                value=0,
            ),
            MetricResult[float | None](
                metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR,
                value=None,
            ),
        )
        classifier.classify.return_value = classification
        orchestrator.calculate_all.return_value = metric_results
        assembler.assemble.side_effect = expected_error
        service = SubscriberRelativeAnalyticsService(
            classifier,
            orchestrator,
            assembler,
        )

        with self.assertRaises(RuntimeError) as raised:
            service.calculate(_dataset(), 100, _EVALUATION_TIME)

        self.assertIs(raised.exception, expected_error)
        classifier.classify.assert_called_once()
        orchestrator.calculate_all.assert_called_once()
        assembler.assemble.assert_called_once_with(metric_results)

    def test_application_composition_registers_the_public_service(self) -> None:
        application = create_application(
            Settings(environment="test", log_level="CRITICAL")
        )

        self.assertIsInstance(
            application.state.subscriber_relative_analytics_service,
            SubscriberRelativeAnalyticsService,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
