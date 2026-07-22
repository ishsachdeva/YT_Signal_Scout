from __future__ import annotations

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, call

from app.services.youtube.client import YouTubeClient
from app.services.youtube.exceptions import (
    ChannelNotFoundError,
    VideoNotFoundError,
    YouTubeAPIError,
)
from app.services.youtube.models import Channel, Video
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
