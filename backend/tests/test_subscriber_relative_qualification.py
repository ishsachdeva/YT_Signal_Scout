"""Unit tests for deterministic subscriber-relative qualification policy v1."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from pydantic import ValidationError

from app.services.analytics.eligibility import EligibleVideoClassification
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.qualification import (
    QualificationFailureReason,
    SubscriberRelativeQualificationService,
    SubscriberState,
)
from app.services.youtube.models import (
    AcquisitionSource,
    Channel,
    ChannelStatistics,
    PaginationProvenance,
    PaginationStatus,
    Video,
    VideoAcquisitionProvenance,
)

_NOW = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _provenance(
    *, requested: int = 5, enriched: int = 5, truncated: bool = False
) -> VideoAcquisitionProvenance:
    return VideoAcquisitionProvenance(
        source=AcquisitionSource.UPLOADS_PLAYLIST,
        source_channel_id="channel-1",
        discovery_request_capacity=max(requested, 1),
        discovered_position_count=requested,
        discovered_unique_video_count=requested,
        enrichment_requested_unique_count=requested,
        enriched_unique_video_count=enriched,
        enriched_output_position_count=enriched,
        omitted_unique_video_count=requested - enriched,
        pagination=PaginationProvenance(
            status=PaginationStatus.TRUNCATED if truncated else PaginationStatus.COMPLETE,
            pages_fetched=1,
            page_size_requested=max(requested, 1),
            page_limit=1,
            next_page_token_present=truncated,
        ),
    )


def _classification(count: int = 5) -> EligibleVideoClassification:
    videos = tuple(
        Video(id=f"video-{index}", channel_id="channel-1", title=f"Video {index}")
        for index in range(count)
    )
    return EligibleVideoClassification(
        eligible_standard_videos=videos,
        eligible_shorts=(),
        eligible_livestream_replays=(),
        exclusions=(),
        evaluated_at=_NOW,
    )


def _channel(
    *, subscriber_count: int | None = 100, hidden: bool = False
) -> Channel:
    return Channel(
        id="channel-1",
        title="Channel",
        statistics=ChannelStatistics(
            view_count=1_000,
            subscriber_count=subscriber_count,
            subscriber_count_hidden=hidden,
            video_count=5,
        ),
    )


class SubscriberRelativeQualificationServiceTests(TestCase):
    def setUp(self) -> None:
        self.service = SubscriberRelativeQualificationService()

    def qualify(
        self,
        *,
        provenance: VideoAcquisitionProvenance | None = None,
        classification: EligibleVideoClassification | None = None,
        channel: Channel | None = None,
    ):
        return self.service.qualify(
            provenance or _provenance(),
            classification or _classification(),
            channel or _channel(),
            _NOW,
        )

    def test_qualified_result_contains_complete_facts_and_is_immutable(self) -> None:
        result = self.qualify()
        self.assertTrue(result.qualified)
        self.assertEqual(result.failures, ())
        self.assertEqual(result.requested_id_resolution_rate, 1.0)
        self.assertEqual(result.eligible_standard_video_count, 5)
        self.assertIs(result.subscriber_state, SubscriberState.AVAILABLE_POSITIVE)
        self.assertEqual(result.policy_version, 1)
        with self.assertRaises(ValidationError):
            result.qualified = False

    def test_exact_sixty_percent_resolution_passes(self) -> None:
        result = self.qualify(provenance=_provenance(requested=5, enriched=3))
        self.assertTrue(result.qualified)
        self.assertEqual(result.requested_id_resolution_rate, 0.6)

    def test_below_sixty_percent_resolution_fails(self) -> None:
        result = self.qualify(provenance=_provenance(requested=5, enriched=2))
        self.assertEqual(
            result.failures,
            (QualificationFailureReason.INSUFFICIENT_REQUESTED_ID_RESOLUTION,),
        )

    def test_zero_requested_ids_has_undefined_rate_without_resolution_failure(self) -> None:
        result = self.qualify(provenance=_provenance(requested=0, enriched=0))
        self.assertIsNone(result.requested_id_resolution_rate)
        self.assertNotIn(
            QualificationFailureReason.INSUFFICIENT_REQUESTED_ID_RESOLUTION,
            result.failures,
        )

    def test_all_normal_failures_are_accumulated_in_policy_order(self) -> None:
        result = self.qualify(
            provenance=_provenance(requested=5, enriched=2, truncated=True),
            classification=_classification(4),
            channel=_channel(subscriber_count=None, hidden=True),
        )
        self.assertEqual(
            result.failures,
            (
                QualificationFailureReason.ACQUISITION_TRUNCATED,
                QualificationFailureReason.INSUFFICIENT_REQUESTED_ID_RESOLUTION,
                QualificationFailureReason.SUBSCRIBER_COUNT_HIDDEN,
                QualificationFailureReason.INSUFFICIENT_ELIGIBLE_STANDARD_VIDEOS,
            ),
        )

    def test_unavailable_and_not_positive_subscriber_states_are_distinct(self) -> None:
        unavailable = self.qualify(channel=Channel(id="channel-1", title="Channel"))
        zero = self.qualify(channel=_channel(subscriber_count=0))
        self.assertIs(unavailable.subscriber_state, SubscriberState.UNAVAILABLE)
        self.assertEqual(
            unavailable.failures,
            (QualificationFailureReason.SUBSCRIBER_COUNT_UNAVAILABLE,),
        )
        self.assertIs(zero.subscriber_state, SubscriberState.NOT_POSITIVE)
        self.assertEqual(
            zero.failures,
            (QualificationFailureReason.SUBSCRIBER_COUNT_NOT_POSITIVE,),
        )

    def test_contradictory_hidden_numeric_state_is_invalid(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "hidden subscriber"):
            self.qualify(channel=_channel(subscriber_count=100, hidden=True))

    def test_negative_subscriber_count_is_invalid_even_for_unvalidated_input(self) -> None:
        statistics = ChannelStatistics.model_construct(
            view_count=1_000,
            subscriber_count=-1,
            subscriber_count_hidden=False,
            video_count=5,
        )
        channel = Channel(id="channel-1", title="Channel", statistics=statistics)
        with self.assertRaisesRegex(AnalyticsValidationError, "must not be negative"):
            self.qualify(channel=channel)

    def test_non_uploads_and_channel_mismatch_provenance_are_invalid(self) -> None:
        search = _provenance().model_copy(
            update={"source": AcquisitionSource.SEARCH, "source_channel_id": None}
        )
        with self.assertRaisesRegex(AnalyticsValidationError, "uploads provenance"):
            self.qualify(provenance=search)
        mismatch = _provenance().model_copy(update={"source_channel_id": "other"})
        with self.assertRaisesRegex(AnalyticsValidationError, "must match"):
            self.qualify(provenance=mismatch)

    def test_repeated_execution_is_deterministic(self) -> None:
        first = self.qualify()
        second = self.qualify()
        self.assertEqual(first, second)


if __name__ == "__main__":
    import unittest

    unittest.main()
