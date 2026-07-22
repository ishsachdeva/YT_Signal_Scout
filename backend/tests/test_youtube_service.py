from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, call

from app.services.youtube.client import YouTubeClient
from app.services.youtube.exceptions import (
    ChannelNotFoundError,
    VideoNotFoundError,
    YouTubeAPIError,
)
from app.services.youtube.models import (
    Channel,
    LiveState,
    PrivacyStatus,
    Video,
    VideoAvailability,
    VideoFormat,
)
from app.services.youtube.service import YouTubeService


def _channel_item(*, hidden_subscribers: bool = False) -> dict[str, object]:
    statistics: dict[str, object] = {
        "viewCount": "1200",
        "hiddenSubscriberCount": hidden_subscribers,
        "videoCount": "12",
    }
    if not hidden_subscribers:
        statistics["subscriberCount"] = "300"
    return {
        "id": "channel-1",
        "snippet": {
            "title": "Example Channel",
            "description": "Public description",
            "customUrl": "@example",
            "country": "IN",
            "publishedAt": "2025-01-02T03:04:05Z",
            "thumbnails": {
                "default": {"url": "https://example.test/channel.jpg", "width": 88}
            },
        },
        "statistics": statistics,
        "contentDetails": {"relatedPlaylists": {"uploads": "uploads-1"}},
    }


def _video_item(video_id: str) -> dict[str, object]:
    return {
        "id": {"videoId": video_id},
        "snippet": {
            "channelId": "channel-1",
            "channelTitle": "Example Channel",
            "title": f"Video {video_id}",
            "description": "Video description",
            "publishedAt": "2026-02-03T04:05:06Z",
            "thumbnails": {
                "medium": {
                    "url": f"https://example.test/{video_id}.jpg",
                    "width": 320,
                    "height": 180,
                }
            },
        },
    }


def _videos_resource(video_id: str = "video-1") -> dict[str, object]:
    item = _video_item(video_id)
    item["id"] = video_id
    snippet = item["snippet"]
    assert isinstance(snippet, dict)
    snippet.update(
        {
            "tags": ["engineering", "python"],
            "categoryId": "28",
            "defaultLanguage": "en",
            "liveBroadcastContent": "none",
        }
    )
    item["statistics"] = {
        "viewCount": "400",
        "likeCount": "40",
        "commentCount": "4",
    }
    item["contentDetails"] = {"duration": "PT5M30S"}
    item["status"] = {
        "privacyStatus": "public",
        "uploadStatus": "processed",
    }
    return item


class YouTubeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = MagicMock(spec=YouTubeClient)
        self.client.page_size = 25
        self.service = YouTubeService(self.client)

    def test_search_channels_parses_typed_page(self) -> None:
        item = _channel_item()
        item["id"] = {"channelId": "channel-1"}
        item.pop("statistics")
        item.pop("contentDetails")
        self.client.search.return_value = {
            "items": [item],
            "pageInfo": {"totalResults": 42, "resultsPerPage": 1},
            "nextPageToken": "page-2",
        }

        result = self.service.search_channels("engineering", region_code="IN")

        self.assertIsInstance(result.items[0], Channel)
        self.assertEqual(result.items[0].id, "channel-1")
        self.assertEqual(result.page_info.total_results, 42)
        self.assertEqual(result.next_page_token, "page-2")
        self.client.search.assert_called_once_with(
            query="engineering",
            resource_type="channel",
            max_results=25,
            page_token=None,
            region_code="IN",
            relevance_language=None,
        )

    def test_search_videos_parses_datetime_and_thumbnail(self) -> None:
        self.client.search.return_value = {
            "items": [_video_item("video-1")],
            "pageInfo": {"totalResults": 1, "resultsPerPage": 1},
        }

        result = self.service.search_videos("engineering", page_size=10)

        video = result.items[0]
        self.assertIsInstance(video, Video)
        self.assertEqual(video.published_at, datetime(2026, 2, 3, 4, 5, 6, tzinfo=UTC))
        self.assertEqual(video.thumbnails[0].width, 320)

    def test_get_channel_parses_statistics_and_uploads_playlist(self) -> None:
        self.client.get_channels.return_value = {"items": [_channel_item()]}

        channel = self.service.get_channel("channel-1")

        self.assertEqual(channel.uploads_playlist_id, "uploads-1")
        self.assertEqual(channel.statistics.subscriber_count, 300)
        self.assertEqual(channel.statistics.view_count, 1200)
        self.client.get_channels.assert_called_once_with(
            ["channel-1"], parts=("snippet", "statistics", "contentDetails")
        )

    def test_get_video_returns_parsed_video(self) -> None:
        item = _video_item("video-1")
        item["id"] = "video-1"
        item["statistics"] = {"viewCount": "100"}
        item["contentDetails"] = {"duration": "PT5M"}
        self.client.get_videos.return_value = {"items": [item]}

        video = self.service.get_video("video-1")

        self.assertIsInstance(video, Video)
        self.assertEqual(video.id, "video-1")
        self.assertEqual(video.view_count, 100)
        self.client.get_videos.assert_called_once_with(
            ["video-1"],
            parts=(
                "snippet",
                "statistics",
                "contentDetails",
                "status",
                "liveStreamingDetails",
            ),
        )

    def test_get_video_populates_complete_canonical_metadata(self) -> None:
        self.client.get_videos.return_value = {"items": [_videos_resource()]}

        video = self.service.get_video("video-1")

        self.assertEqual(video.tags, ("engineering", "python"))
        self.assertEqual(video.category_id, "28")
        self.assertEqual(video.default_language, "en")
        self.assertEqual(video.like_count, 40)
        self.assertEqual(video.comment_count, 4)
        self.assertEqual(video.duration, timedelta(minutes=5, seconds=30))
        self.assertIs(video.privacy_status, PrivacyStatus.PUBLIC)
        self.assertIs(video.availability, VideoAvailability.AVAILABLE)
        self.assertIs(video.live_state, LiveState.NOT_LIVE)
        self.assertIs(video.format, VideoFormat.STANDARD)

    def test_missing_optional_statistics_remain_none(self) -> None:
        item = _videos_resource()
        statistics = item["statistics"]
        assert isinstance(statistics, dict)
        statistics.pop("likeCount")
        statistics.pop("commentCount")
        self.client.get_videos.return_value = {"items": [item]}

        video = self.service.get_video("video-1")

        self.assertIsNone(video.like_count)
        self.assertIsNone(video.comment_count)

    def test_duration_parsing_preserves_zero_and_missing_values(self) -> None:
        cases = (
            ("PT0S", timedelta(0)),
            ("P1DT2H3M4S", timedelta(days=1, hours=2, minutes=3, seconds=4)),
            (None, None),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                item = _videos_resource()
                content_details = item["contentDetails"]
                assert isinstance(content_details, dict)
                if value is None:
                    content_details.pop("duration")
                else:
                    content_details["duration"] = value
                self.client.get_videos.return_value = {"items": [item]}

                video = self.service.get_video("video-1")

                self.assertEqual(video.duration, expected)

    def test_malformed_or_calendar_duration_is_rejected(self) -> None:
        for value in ("five minutes", "PT-1S", "P1Y", "P1M"):
            with self.subTest(value=value):
                item = _videos_resource()
                content_details = item["contentDetails"]
                assert isinstance(content_details, dict)
                content_details["duration"] = value
                self.client.get_videos.return_value = {"items": [item]}

                with self.assertRaisesRegex(YouTubeAPIError, "video duration"):
                    self.service.get_video("video-1")

    def test_privacy_mapping_is_closed_and_optional(self) -> None:
        cases = (
            ("public", PrivacyStatus.PUBLIC),
            ("private", PrivacyStatus.PRIVATE),
            ("unlisted", PrivacyStatus.UNLISTED),
            ("future-value", None),
            (None, None),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                item = _videos_resource()
                status = item["status"]
                assert isinstance(status, dict)
                if value is None:
                    status.pop("privacyStatus")
                else:
                    status["privacyStatus"] = value
                self.client.get_videos.return_value = {"items": [item]}

                video = self.service.get_video("video-1")

                self.assertIs(video.privacy_status, expected)

    def test_availability_mapping_is_conservative(self) -> None:
        cases = (
            ("processed", VideoAvailability.AVAILABLE),
            (None, VideoAvailability.AVAILABLE),
            ("deleted", VideoAvailability.DELETED),
            ("uploaded", VideoAvailability.UNKNOWN),
            ("future-value", VideoAvailability.UNKNOWN),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                item = _videos_resource()
                status = item["status"]
                assert isinstance(status, dict)
                if value is None:
                    status.pop("uploadStatus")
                else:
                    status["uploadStatus"] = value
                self.client.get_videos.return_value = {"items": [item]}

                video = self.service.get_video("video-1")

                self.assertIs(video.availability, expected)

    def test_live_state_and_replay_mapping(self) -> None:
        cases = (
            (
                "live",
                {"actualStartTime": "2026-02-03T04:00:00Z"},
                LiveState.LIVE,
                VideoFormat.UNKNOWN,
            ),
            (
                "upcoming",
                {"scheduledStartTime": "2026-02-04T04:00:00Z"},
                LiveState.UPCOMING,
                VideoFormat.UNKNOWN,
            ),
            (
                "none",
                {
                    "actualStartTime": "2026-02-03T03:00:00Z",
                    "actualEndTime": "2026-02-03T04:00:00Z",
                },
                LiveState.COMPLETE,
                VideoFormat.LIVE_REPLAY,
            ),
            ("none", {}, LiveState.NOT_LIVE, VideoFormat.STANDARD),
            (
                "live",
                {
                    "actualStartTime": "2026-02-03T03:00:00Z",
                    "actualEndTime": "2026-02-03T04:00:00Z",
                },
                LiveState.UNKNOWN,
                VideoFormat.UNKNOWN,
            ),
            (None, {}, LiveState.UNKNOWN, VideoFormat.UNKNOWN),
        )

        for broadcast, live_details, expected_state, expected_format in cases:
            with self.subTest(broadcast=broadcast, live_details=live_details):
                item = _videos_resource()
                snippet = item["snippet"]
                assert isinstance(snippet, dict)
                if broadcast is None:
                    snippet.pop("liveBroadcastContent")
                else:
                    snippet["liveBroadcastContent"] = broadcast
                item["liveStreamingDetails"] = live_details
                self.client.get_videos.return_value = {"items": [item]}

                video = self.service.get_video("video-1")

                self.assertIs(video.live_state, expected_state)
                self.assertIs(video.format, expected_format)

    def test_short_or_missing_duration_never_infers_format(self) -> None:
        for value in ("PT3M", "PT30S", None):
            with self.subTest(value=value):
                item = _videos_resource()
                content_details = item["contentDetails"]
                assert isinstance(content_details, dict)
                if value is None:
                    content_details.pop("duration")
                else:
                    content_details["duration"] = value
                self.client.get_videos.return_value = {"items": [item]}

                video = self.service.get_video("video-1")

                self.assertIs(video.format, VideoFormat.UNKNOWN)

    def test_missing_video_raises_normalized_exception(self) -> None:
        self.client.get_videos.return_value = {"items": []}
        with self.assertRaisesRegex(
            VideoNotFoundError, "YouTube video 'missing' was not found"
        ):
            self.service.get_video("missing")

    def test_get_channel_statistics_preserves_hidden_subscriber_state(self) -> None:
        item = _channel_item(hidden_subscribers=True)
        self.client.get_channels.return_value = {
            "items": [{"id": "channel-1", "statistics": item["statistics"]}]
        }

        statistics = self.service.get_channel_statistics("channel-1")

        self.assertTrue(statistics.subscriber_count_hidden)
        self.assertIsNone(statistics.subscriber_count)

    def test_missing_channel_raises_normalized_exception(self) -> None:
        self.client.get_channels.return_value = {"items": []}
        with self.assertRaises(ChannelNotFoundError):
            self.service.get_channel("missing")

    def test_list_channel_videos_follows_bounded_pagination(self) -> None:
        self.client.get_channels.return_value = {"items": [_channel_item()]}
        first = _video_item("video-1")
        first["id"] = None
        first["contentDetails"] = {"videoId": "video-1"}
        second = _video_item("video-2")
        second["id"] = None
        second["contentDetails"] = {"videoId": "video-2"}
        self.client.list_playlist_items.side_effect = [
            {
                "items": [first],
                "pageInfo": {"totalResults": 2, "resultsPerPage": 1},
                "nextPageToken": "page-2",
            },
            {
                "items": [second],
                "pageInfo": {"totalResults": 2, "resultsPerPage": 1},
                "prevPageToken": "page-1",
            },
        ]

        result = self.service.list_channel_videos("channel-1", max_pages=2, page_size=1)

        self.assertEqual([item.id for item in result.items], ["video-1", "video-2"])
        self.assertEqual(result.page_info.results_per_page, 2)
        self.assertIsNone(result.next_page_token)
        self.client.list_playlist_items.assert_has_calls(
            [
                call(playlist_id="uploads-1", max_results=1, page_token=None),
                call(playlist_id="uploads-1", max_results=1, page_token="page-2"),
            ]
        )

    def test_list_channel_videos_stops_at_max_pages_and_returns_token(self) -> None:
        self.client.get_channels.return_value = {"items": [_channel_item()]}
        item = _video_item("video-1")
        item["id"] = None
        item["contentDetails"] = {"videoId": "video-1"}
        self.client.list_playlist_items.return_value = {
            "items": [item],
            "pageInfo": {"totalResults": 3, "resultsPerPage": 1},
            "nextPageToken": "remaining-page",
        }

        result = self.service.list_channel_videos("channel-1", max_pages=1)

        self.assertEqual(result.next_page_token, "remaining-page")
        self.client.list_playlist_items.assert_called_once()

    def test_malformed_payload_is_normalized(self) -> None:
        self.client.search.return_value = {
            "items": [{"id": {"videoId": "video-1"}, "snippet": {}}],
            "pageInfo": {},
        }
        with self.assertRaisesRegex(YouTubeAPIError, "video channel id"):
            self.service.search_videos("engineering")


if __name__ == "__main__":
    unittest.main()
