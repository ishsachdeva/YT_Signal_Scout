from __future__ import annotations

import json
import socket
import unittest
from unittest.mock import MagicMock, patch

import httplib2
from googleapiclient.errors import HttpError

from app.services.youtube.client import YouTubeClient
from app.services.youtube.exceptions import (
    AuthenticationError,
    QuotaExceededError,
    YouTubeAPIError,
    YouTubeTimeoutError,
)


class YouTubeClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resource = MagicMock()
        self.request = MagicMock()
        self.resource.search.return_value.list.return_value = self.request
        self.request.execute.return_value = {
            "items": [],
            "pageInfo": {"totalResults": 0, "resultsPerPage": 0},
        }
        self.client = YouTubeClient(
            api_key="test-key", max_retries=4, page_size=20, resource=self.resource
        )

    def test_successful_search_executes_with_retry_policy_and_filters(self) -> None:
        result = self.client.search(
            query="python",
            resource_type="channel",
            max_results=10,
            page_token="next",
            region_code="IN",
            relevance_language="hi",
        )

        self.assertEqual(result["items"], [])
        self.resource.search.return_value.list.assert_called_once_with(
            part="id,snippet",
            q="python",
            type="channel",
            maxResults=10,
            pageToken="next",
            regionCode="IN",
            relevanceLanguage="hi",
        )
        self.request.execute.assert_called_once_with(num_retries=4)

    def test_optional_search_filters_are_omitted(self) -> None:
        self.client.search(query="python", resource_type="video", max_results=20)
        parameters = self.resource.search.return_value.list.call_args.kwargs
        self.assertNotIn("pageToken", parameters)
        self.assertNotIn("regionCode", parameters)

    def test_get_videos_uses_videos_list_endpoint(self) -> None:
        self.resource.videos.return_value.list.return_value = self.request

        result = self.client.get_videos(
            ["video-1"], parts=("snippet", "statistics", "contentDetails")
        )

        self.assertEqual(result["items"], [])
        self.resource.videos.return_value.list.assert_called_once_with(
            part="snippet,statistics,contentDetails", id="video-1", maxResults=1
        )
        self.request.execute.assert_called_once_with(num_retries=4)

    def test_get_videos_requires_between_one_and_fifty_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 50"):
            self.client.get_videos([], parts=("snippet",))

    def test_timeout_is_normalized(self) -> None:
        self.request.execute.side_effect = socket.timeout("private transport detail")
        with self.assertRaises(YouTubeTimeoutError) as raised:
            self.client.search(query="python", resource_type="video", max_results=20)
        self.assertNotIn("private transport detail", str(raised.exception))

    def test_quota_error_is_normalized(self) -> None:
        self.request.execute.side_effect = self._http_error(403, "quotaExceeded")
        with self.assertRaises(QuotaExceededError):
            self.client.search(query="python", resource_type="video", max_results=20)

    def test_authentication_error_is_normalized(self) -> None:
        self.request.execute.side_effect = self._http_error(400, "keyInvalid")
        with self.assertRaises(AuthenticationError):
            self.client.search(query="python", resource_type="video", max_results=20)

    def test_unknown_http_error_is_normalized_without_upstream_body(self) -> None:
        self.request.execute.side_effect = self._http_error(500, "backendError")
        with self.assertRaisesRegex(YouTubeAPIError, "status 500") as raised:
            self.client.search(query="python", resource_type="video", max_results=20)
        self.assertNotIn("backendError", str(raised.exception))

    def test_page_size_is_bounded(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 50"):
            self.client.search(query="python", resource_type="video", max_results=51)

    @patch("app.services.youtube.client.httplib2.Http")
    @patch("app.services.youtube.client.build")
    def test_timeout_and_api_key_are_used_when_building_resource(
        self, build_mock: MagicMock, http_mock: MagicMock
    ) -> None:
        built_resource = MagicMock()
        build_mock.return_value = built_resource
        transport = MagicMock()
        http_mock.return_value = transport

        client = YouTubeClient(api_key="configured-key", timeout=7.5)

        http_mock.assert_called_once_with(timeout=7.5)
        build_mock.assert_called_once_with(
            "youtube",
            "v3",
            developerKey="configured-key",
            http=transport,
            cache_discovery=False,
        )
        self.assertIs(client._resource, built_resource)

    def test_api_key_is_required_without_injected_resource(self) -> None:
        with self.assertRaises(AuthenticationError):
            YouTubeClient(api_key="")

    @staticmethod
    def _http_error(status: int, reason: str) -> HttpError:
        response = httplib2.Response({"status": str(status)})
        content = json.dumps({"error": {"errors": [{"reason": reason}]}}).encode()
        return HttpError(response, content)


if __name__ == "__main__":
    unittest.main()
