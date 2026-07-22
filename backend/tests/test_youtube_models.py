"""Unit tests for typed YouTube domain models."""

from datetime import timedelta
from unittest import TestCase

from pydantic import ValidationError

from app.services.youtube.models import (
    AcquisitionSource,
    PaginationProvenance,
    PaginationStatus,
    PrivacyStatus,
    Video,
    VideoAcquisitionProvenance,
    VideoAcquisitionResult,
)


class VideoModelTests(TestCase):
    """Verify the enriched video model remains typed and immutable."""

    def test_video_accepts_analytics_metadata(self) -> None:
        video = Video(
            id="video-1",
            channel_id="channel-1",
            title="Video",
            tags=("analytics", "youtube"),
            category_id="28",
            default_language="en",
            like_count=125,
            comment_count=12,
            duration=timedelta(minutes=5, seconds=30),
            privacy_status=PrivacyStatus.PUBLIC,
        )

        self.assertEqual(video.tags, ("analytics", "youtube"))
        self.assertEqual(video.category_id, "28")
        self.assertEqual(video.default_language, "en")
        self.assertEqual(video.like_count, 125)
        self.assertEqual(video.comment_count, 12)
        self.assertEqual(video.duration, timedelta(minutes=5, seconds=30))
        self.assertIs(video.privacy_status, PrivacyStatus.PUBLIC)

    def test_video_rejects_unknown_privacy_status(self) -> None:
        with self.assertRaises(ValidationError):
            Video(
                id="video-1",
                channel_id="channel-1",
                title="Video",
                privacy_status="unknown",
            )

    def test_video_rejects_negative_like_count(self) -> None:
        with self.assertRaises(ValidationError):
            Video(
                id="video-1",
                channel_id="channel-1",
                title="Video",
                like_count=-1,
            )

    def test_video_rejects_negative_comment_count(self) -> None:
        with self.assertRaises(ValidationError):
            Video(
                id="video-1",
                channel_id="channel-1",
                title="Video",
                comment_count=-1,
            )

    def test_video_remains_immutable(self) -> None:
        video = Video(id="video-1", channel_id="channel-1", title="Video")

        with self.assertRaises(ValidationError):
            video.like_count = 1


class VideoAcquisitionModelTests(TestCase):
    """Verify acquisition collections and provenance cannot contradict."""

    @staticmethod
    def provenance() -> VideoAcquisitionProvenance:
        return VideoAcquisitionProvenance(
            source=AcquisitionSource.UPLOADS_PLAYLIST,
            source_channel_id="channel-1",
            discovery_request_capacity=2,
            discovered_position_count=2,
            discovered_unique_video_count=1,
            enrichment_requested_unique_count=1,
            enriched_unique_video_count=1,
            enriched_output_position_count=2,
            omitted_unique_video_count=0,
            pagination=PaginationProvenance(
                status=PaginationStatus.COMPLETE,
                pages_fetched=1,
                page_size_requested=2,
                page_limit=1,
                next_page_token_present=False,
            ),
        )

    def test_duplicate_positions_and_unique_collection_are_valid_and_immutable(self) -> None:
        video = Video(id="video-1", channel_id="channel-1", title="Video")
        result = VideoAcquisitionResult(
            resolved_discovery_videos=(video, video),
            unique_canonical_videos=(video,),
            provenance=self.provenance(),
        )
        self.assertIs(result.resolved_discovery_videos[0], result.resolved_discovery_videos[1])
        with self.assertRaises(ValidationError):
            result.unique_canonical_videos = ()

    def test_pagination_status_must_match_token_presence(self) -> None:
        with self.assertRaises(ValidationError):
            PaginationProvenance(
                status=PaginationStatus.COMPLETE,
                pages_fetched=1,
                page_size_requested=1,
                page_limit=1,
                next_page_token_present=True,
            )

    def test_result_rejects_non_unique_or_wrong_order_unique_collection(self) -> None:
        first = Video(id="video-1", channel_id="channel-1", title="First")
        second = Video(id="video-2", channel_id="channel-1", title="Second")
        provenance = self.provenance().model_copy(
            update={
                "discovered_unique_video_count": 2,
                "enrichment_requested_unique_count": 2,
                "enriched_unique_video_count": 2,
                "omitted_unique_video_count": 0,
            }
        )
        with self.assertRaises(ValidationError):
            VideoAcquisitionResult(
                resolved_discovery_videos=(first, second),
                unique_canonical_videos=(second, first),
                provenance=provenance,
            )
