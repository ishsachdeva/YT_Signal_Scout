"""Unit tests for typed YouTube domain models."""

from datetime import timedelta
from unittest import TestCase

from pydantic import ValidationError

from app.services.youtube.models import PrivacyStatus, Video


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
