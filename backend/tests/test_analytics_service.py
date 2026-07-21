from __future__ import annotations

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import CalculatedChannelAnalytics, ChannelAnalytics
from app.services.analytics.service import AnalyticsService
from app.services.youtube.models import Channel, Video


class AnalyticsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generated_at = datetime(2026, 7, 21, 12, 30, tzinfo=UTC)
        self.service = AnalyticsService(clock=lambda: self.generated_at)
        self.channel = Channel(id="channel-1", title="Example Channel")
        self.videos = [
            Video(id="video-1", channel_id="channel-1", title="First Video"),
            Video(id="video-2", channel_id="channel-1", title="Second Video"),
        ]

    def test_successful_creation(self) -> None:
        analytics = self.service.build_channel_analytics(self.channel, self.videos)

        self.assertIsInstance(analytics, ChannelAnalytics)
        self.assertNotIsInstance(analytics, CalculatedChannelAnalytics)
        self.assertEqual(analytics.channel, self.channel)
        self.assertEqual(analytics.videos, self.videos)
        self.assertEqual(analytics.video_count, 2)
        self.assertEqual(analytics.generated_at, self.generated_at)

    def test_empty_video_list_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsValidationError,
            "Cannot build analytics for a channel with no videos",
        ):
            self.service.build_channel_analytics(self.channel, [])

    def test_video_count_is_derived_from_videos(self) -> None:
        analytics = ChannelAnalytics(
            channel=self.channel,
            videos=self.videos,
            generated_at=self.generated_at,
        )

        self.assertNotIn("video_count", ChannelAnalytics.model_fields)
        self.assertEqual(analytics.video_count, len(analytics.videos))

    def test_mixed_channel_video_dataset_is_accepted(self) -> None:
        videos = [
            self.videos[0],
            Video(
                id="video-2",
                channel_id="another-channel",
                title="Collaboration Video",
            ),
        ]

        analytics = self.service.build_channel_analytics(self.channel, videos)

        self.assertEqual(analytics.videos, videos)
        self.assertEqual(analytics.video_count, 2)

    def test_invalid_channel_is_rejected(self) -> None:
        invalid_channel = Channel(id="", title="Example Channel")
        with self.assertRaisesRegex(AnalyticsValidationError, "channel id"):
            self.service.build_channel_analytics(invalid_channel, self.videos)

    def test_input_types_are_validated(self) -> None:
        with self.assertRaisesRegex(AnalyticsValidationError, "must be a Channel"):
            self.service.build_channel_analytics("channel-1", self.videos)  # type: ignore[arg-type]
        with self.assertRaisesRegex(AnalyticsValidationError, "must be a list"):
            self.service.build_channel_analytics(self.channel, tuple(self.videos))  # type: ignore[arg-type]
        with self.assertRaisesRegex(AnalyticsValidationError, "only Video"):
            self.service.build_channel_analytics(self.channel, ["video-1"])  # type: ignore[list-item]

    def test_analytics_model_is_immutable(self) -> None:
        analytics = self.service.build_channel_analytics(self.channel, self.videos)

        with self.assertRaises(ValidationError):
            analytics.video_count = 3

    def test_input_video_list_is_copied(self) -> None:
        analytics = self.service.build_channel_analytics(self.channel, self.videos)

        self.videos.clear()

        self.assertEqual(analytics.video_count, 2)
        self.assertEqual(len(analytics.videos), 2)


if __name__ == "__main__":
    unittest.main()
