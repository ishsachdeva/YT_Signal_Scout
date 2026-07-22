"""Tests for deterministic Eligible Video Policy v1 classification."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest import TestCase

from pydantic import ValidationError

from app.services.analytics.eligibility import (
    EligibleVideoClassification,
    EligibleVideoClassifier,
    VideoExclusionReason,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import ChannelAnalytics
from app.services.youtube.models import (
    Channel,
    LiveState,
    PrivacyStatus,
    Video,
    VideoAvailability,
    VideoFormat,
)


class EligibleVideoClassifierTests(TestCase):
    """Verify every Eligible Video Policy v1 boundary and invariant."""

    def setUp(self) -> None:
        self.evaluation_time = datetime(2026, 7, 22, 12, tzinfo=UTC)
        self.channel = Channel(id="channel-1", title="Channel")
        self.classifier = EligibleVideoClassifier()

    def video(
        self,
        identifier: str,
        *,
        video_format: VideoFormat = VideoFormat.STANDARD,
        live_state: LiveState = LiveState.NOT_LIVE,
        availability: VideoAvailability = VideoAvailability.AVAILABLE,
        privacy_status: PrivacyStatus | None = PrivacyStatus.PUBLIC,
        published_at: datetime | None = None,
        view_count: int | None = 100,
    ) -> Video:
        return Video(
            id=identifier,
            channel_id=self.channel.id,
            title=identifier,
            availability=availability,
            privacy_status=privacy_status,
            live_state=live_state,
            format=video_format,
            published_at=(
                self.evaluation_time - timedelta(days=7)
                if published_at is None
                else published_at
            ),
            view_count=view_count,
        )

    def dataset(self, videos: list[Video]) -> ChannelAnalytics:
        return ChannelAnalytics(
            channel=self.channel,
            videos=videos,
            generated_at=self.evaluation_time,
        )

    def classify(self, videos: list[Video]) -> EligibleVideoClassification:
        return self.classifier.classify(
            self.dataset(videos),
            self.evaluation_time,
        )

    def test_empty_dataset_returns_empty_ordered_bases(self) -> None:
        result = self.classify([])

        self.assertEqual(result.eligible_standard_videos, ())
        self.assertEqual(result.eligible_shorts, ())
        self.assertEqual(result.eligible_livestream_replays, ())
        self.assertEqual(result.exclusions, ())
        self.assertEqual(result.evaluated_at, self.evaluation_time)
        self.assertEqual(result.policy_version, 1)

    def test_only_standard_videos_enter_standard_basis(self) -> None:
        videos = [self.video("standard-1"), self.video("standard-2")]

        result = self.classify(videos)

        self.assertEqual(result.eligible_standard_videos, tuple(videos))
        self.assertEqual(result.eligible_shorts, ())
        self.assertEqual(result.eligible_livestream_replays, ())

    def test_only_shorts_enter_short_basis(self) -> None:
        videos = [
            self.video("short-1", video_format=VideoFormat.SHORT),
            self.video("short-2", video_format=VideoFormat.SHORT),
        ]

        result = self.classify(videos)

        self.assertEqual(result.eligible_standard_videos, ())
        self.assertEqual(result.eligible_shorts, tuple(videos))
        self.assertEqual(result.eligible_livestream_replays, ())

    def test_only_completed_replays_enter_livestream_replay_basis(self) -> None:
        videos = [
            self.video(
                "replay-1",
                video_format=VideoFormat.LIVE_REPLAY,
                live_state=LiveState.COMPLETE,
            ),
            self.video(
                "replay-2",
                video_format=VideoFormat.LIVE_REPLAY,
                live_state=LiveState.COMPLETE,
            ),
        ]

        result = self.classify(videos)

        self.assertEqual(result.eligible_standard_videos, ())
        self.assertEqual(result.eligible_shorts, ())
        self.assertEqual(result.eligible_livestream_replays, tuple(videos))

    def test_mixed_dataset_separates_formats_and_preserves_source_order(self) -> None:
        standard_1 = self.video("standard-1")
        short_1 = self.video("short-1", video_format=VideoFormat.SHORT)
        excluded = self.video(
            "unknown",
            video_format=VideoFormat.UNKNOWN,
        )
        replay = self.video(
            "replay",
            video_format=VideoFormat.LIVE_REPLAY,
            live_state=LiveState.COMPLETE,
        )
        standard_2 = self.video("standard-2")
        short_2 = self.video("short-2", video_format=VideoFormat.SHORT)

        result = self.classify(
            [standard_1, short_1, excluded, replay, standard_2, short_2]
        )

        self.assertEqual(result.eligible_standard_videos, (standard_1, standard_2))
        self.assertEqual(result.eligible_shorts, (short_1, short_2))
        self.assertEqual(result.eligible_livestream_replays, (replay,))
        self.assertEqual(
            [(item.video_id, item.reason) for item in result.exclusions],
            [("unknown", VideoExclusionReason.UNKNOWN_FORMAT)],
        )

    def test_normal_exclusions_have_documented_primary_reasons(self) -> None:
        cases = (
            (
                self.video(
                    "unavailable",
                    availability=VideoAvailability.UNAVAILABLE,
                ),
                VideoExclusionReason.UNAVAILABLE,
            ),
            (
                self.video("deleted", availability=VideoAvailability.DELETED),
                VideoExclusionReason.DELETED,
            ),
            (
                self.video(
                    "unknown-availability",
                    availability=VideoAvailability.UNKNOWN,
                ),
                VideoExclusionReason.UNKNOWN_AVAILABILITY,
            ),
            (
                self.video("private", privacy_status=PrivacyStatus.PRIVATE),
                VideoExclusionReason.PRIVATE,
            ),
            (
                self.video("unlisted", privacy_status=PrivacyStatus.UNLISTED),
                VideoExclusionReason.UNLISTED,
            ),
            (
                self.video("unknown-privacy", privacy_status=None),
                VideoExclusionReason.UNKNOWN_PRIVACY,
            ),
            (
                self.video("missing-publication").model_copy(
                    update={"published_at": None}
                ),
                VideoExclusionReason.MISSING_PUBLICATION_TIME,
            ),
            (
                self.video(
                    "too-young",
                    published_at=self.evaluation_time - timedelta(hours=23, minutes=59),
                ),
                VideoExclusionReason.TOO_YOUNG,
            ),
            (
                self.video(
                    "too-old",
                    published_at=self.evaluation_time - timedelta(days=90, seconds=1),
                ),
                VideoExclusionReason.TOO_OLD,
            ),
            (
                self.video("missing-views", view_count=None),
                VideoExclusionReason.MISSING_VIEW_COUNT,
            ),
            (
                self.video("upcoming", live_state=LiveState.UPCOMING),
                VideoExclusionReason.UPCOMING,
            ),
            (
                self.video("live", live_state=LiveState.LIVE),
                VideoExclusionReason.CURRENTLY_LIVE,
            ),
            (
                self.video("unknown-live", live_state=LiveState.UNKNOWN),
                VideoExclusionReason.UNKNOWN_LIVE_STATE,
            ),
            (
                self.video("unknown-format", video_format=VideoFormat.UNKNOWN),
                VideoExclusionReason.UNKNOWN_FORMAT,
            ),
            (
                self.video(
                    "unsupported-format",
                    video_format=VideoFormat.LIVE_REPLAY,
                    live_state=LiveState.NOT_LIVE,
                ),
                VideoExclusionReason.UNSUPPORTED_FORMAT,
            ),
        )

        for video, expected_reason in cases:
            with self.subTest(video_id=video.id):
                result = self.classify([video])
                self.assertEqual(len(result.exclusions), 1)
                self.assertIs(result.exclusions[0].reason, expected_reason)

    def test_exclusion_precedence_follows_documented_sequence(self) -> None:
        cases = (
            (
                self.video(
                    "availability-before-privacy",
                    availability=VideoAvailability.UNAVAILABLE,
                    privacy_status=PrivacyStatus.PRIVATE,
                ),
                VideoExclusionReason.UNAVAILABLE,
            ),
            (
                self.video(
                    "privacy-before-publication",
                    privacy_status=PrivacyStatus.PRIVATE,
                ).model_copy(update={"published_at": None}),
                VideoExclusionReason.PRIVATE,
            ),
            (
                self.video(
                    "publication-before-views",
                    view_count=None,
                ).model_copy(update={"published_at": None}),
                VideoExclusionReason.MISSING_PUBLICATION_TIME,
            ),
            (
                self.video(
                    "age-before-views",
                    published_at=self.evaluation_time - timedelta(hours=23),
                    view_count=None,
                ),
                VideoExclusionReason.TOO_YOUNG,
            ),
            (
                self.video(
                    "views-before-live-state",
                    view_count=None,
                    live_state=LiveState.UPCOMING,
                ),
                VideoExclusionReason.MISSING_VIEW_COUNT,
            ),
            (
                self.video(
                    "live-state-before-format",
                    live_state=LiveState.UPCOMING,
                    video_format=VideoFormat.UNKNOWN,
                ),
                VideoExclusionReason.UPCOMING,
            ),
            (
                self.video(
                    "format-before-supported-combination",
                    video_format=VideoFormat.UNKNOWN,
                ),
                VideoExclusionReason.UNKNOWN_FORMAT,
            ),
        )

        for video, expected_reason in cases:
            with self.subTest(video_id=video.id):
                result = self.classify([video])
                self.assertIs(result.exclusions[0].reason, expected_reason)

    def test_exclusions_preserve_source_order(self) -> None:
        videos = [
            self.video("unknown-1", video_format=VideoFormat.UNKNOWN),
            self.video("private", privacy_status=PrivacyStatus.PRIVATE),
            self.video("unknown-2", video_format=VideoFormat.UNKNOWN),
        ]

        result = self.classify(videos)

        self.assertEqual(
            [exclusion.video_id for exclusion in result.exclusions],
            ["unknown-1", "private", "unknown-2"],
        )

    def test_exact_age_boundaries_and_zero_views_are_eligible(self) -> None:
        at_lower_bound = self.video(
            "lower-bound",
            published_at=self.evaluation_time - timedelta(hours=24),
            view_count=0,
        )
        at_upper_bound = self.video(
            "upper-bound",
            published_at=self.evaluation_time - timedelta(days=90),
        )

        result = self.classify([at_lower_bound, at_upper_bound])

        self.assertEqual(
            result.eligible_standard_videos,
            (at_lower_bound, at_upper_bound),
        )
        self.assertEqual(result.exclusions, ())

    def test_duplicate_video_ids_are_rejected_before_classification(self) -> None:
        videos = [
            self.video("duplicate"),
            self.video(
                "duplicate",
                availability=VideoAvailability.UNAVAILABLE,
            ),
        ]

        with self.assertRaisesRegex(AnalyticsValidationError, "duplicate video id"):
            self.classify(videos)

    def test_invalid_video_timestamps_are_rejected(self) -> None:
        cases = (
            self.video(
                "naive",
                published_at=datetime(2026, 7, 20, 12),
            ),
            self.video(
                "future",
                published_at=self.evaluation_time + timedelta(seconds=1),
            ),
        )

        for video in cases:
            with self.subTest(video_id=video.id):
                with self.assertRaises(AnalyticsValidationError):
                    self.classify([video])

    def test_negative_view_count_is_rejected_for_unavailable_video(self) -> None:
        video = self.video(
            "negative",
            availability=VideoAvailability.UNAVAILABLE,
            view_count=-1,
        )

        with self.assertRaisesRegex(AnalyticsValidationError, "cannot be negative"):
            self.classify([video])

    def test_invalid_evaluation_time_is_rejected(self) -> None:
        dataset = self.dataset([])

        with self.assertRaisesRegex(AnalyticsValidationError, "timezone-aware"):
            self.classifier.classify(dataset, datetime(2026, 7, 22, 12))
        with self.assertRaisesRegex(AnalyticsValidationError, "must be a datetime"):
            self.classifier.classify(dataset, None)  # type: ignore[arg-type]

    def test_invalid_source_dataset_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsValidationError,
            "source dataset is required",
        ):
            self.classifier.classify(
                None,  # type: ignore[arg-type]
                self.evaluation_time,
            )

    def test_result_and_exclusions_are_immutable(self) -> None:
        result = self.classify(
            [self.video("unknown", video_format=VideoFormat.UNKNOWN)]
        )

        with self.assertRaises(ValidationError):
            result.policy_version = 2  # type: ignore[misc]
        with self.assertRaises(ValidationError):
            result.exclusions[0].reason = (  # type: ignore[misc]
                VideoExclusionReason.PRIVATE
            )

    def test_classifier_does_not_mutate_or_reorder_source_dataset(self) -> None:
        videos = [
            self.video("standard-2"),
            self.video("short", video_format=VideoFormat.SHORT),
            self.video("standard-1"),
        ]
        source_dataset = self.dataset(videos)
        original_order = tuple(source_dataset.videos)

        result = self.classifier.classify(source_dataset, self.evaluation_time)

        self.assertEqual(tuple(source_dataset.videos), original_order)
        self.assertEqual(
            result.eligible_standard_videos,
            (videos[0], videos[2]),
        )

    def test_repeated_execution_is_deterministic(self) -> None:
        source_dataset = self.dataset(
            [
                self.video("standard"),
                self.video("short", video_format=VideoFormat.SHORT),
                self.video("unknown", video_format=VideoFormat.UNKNOWN),
            ]
        )

        first = self.classifier.classify(source_dataset, self.evaluation_time)
        second = self.classifier.classify(source_dataset, self.evaluation_time)

        self.assertEqual(first, second)
        self.assertIsNot(first, second)


class CanonicalEligibilityFieldTests(TestCase):
    """Verify canonical eligibility facts default conservatively."""

    def test_new_canonical_fields_default_to_unknown(self) -> None:
        video = Video(id="video-1", channel_id="channel-1", title="Video")

        self.assertIs(video.availability, VideoAvailability.UNKNOWN)
        self.assertIs(video.live_state, LiveState.UNKNOWN)
        self.assertIs(video.format, VideoFormat.UNKNOWN)
