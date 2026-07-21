"""Low-level, injectable YouTube Data API client."""

from __future__ import annotations

import json
import socket
from collections.abc import Mapping
from typing import Any, Protocol, cast

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.youtube.exceptions import (
    AuthenticationError,
    QuotaExceededError,
    YouTubeAPIError,
    YouTubeTimeoutError,
)

JsonObject = dict[str, Any]


class ExecutableRequest(Protocol):
    """Minimal request behavior used by the client."""

    def execute(self, *, num_retries: int = 0) -> Mapping[str, Any]: ...


class YouTubeResource(Protocol):
    """Minimal injected google-api-python-client resource behavior."""

    def search(self) -> Any: ...

    def channels(self) -> Any: ...

    def videos(self) -> Any: ...

    def playlistItems(self) -> Any: ...


class YouTubeClient:
    """Execute authenticated YouTube requests and normalize transport failures."""

    def __init__(
        self,
        *,
        api_key: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        page_size: int = 25,
        resource: YouTubeResource | None = None,
    ) -> None:
        if not api_key.strip() and resource is None:
            raise AuthenticationError("A YouTube API key is required")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if max_retries < 0:
            raise ValueError("max_retries must be zero or greater")
        if not 1 <= page_size <= 50:
            raise ValueError("page_size must be between 1 and 50")

        self._max_retries = max_retries
        self.page_size = page_size
        self._resource = resource or cast(
            YouTubeResource,
            build(
                "youtube",
                "v3",
                developerKey=api_key,
                http=httplib2.Http(timeout=timeout),
                cache_discovery=False,
            ),
        )

    def search(
        self,
        *,
        query: str,
        resource_type: str,
        max_results: int,
        page_token: str | None = None,
        region_code: str | None = None,
        relevance_language: str | None = None,
    ) -> JsonObject:
        """Execute one page of a channel or video search."""
        if resource_type not in {"channel", "video"}:
            raise ValueError("resource_type must be 'channel' or 'video'")
        parameters: JsonObject = {
            "part": "id,snippet",
            "q": query,
            "type": resource_type,
            "maxResults": self._validated_page_size(max_results),
        }
        self._add_optional(
            parameters,
            pageToken=page_token,
            regionCode=region_code,
            relevanceLanguage=relevance_language,
        )
        return self._execute(self._resource.search().list(**parameters))

    def get_channels(self, channel_ids: list[str], *, parts: tuple[str, ...]) -> JsonObject:
        """Retrieve requested resource parts for up to 50 channel IDs."""
        if not 1 <= len(channel_ids) <= 50:
            raise ValueError("channel_ids must contain between 1 and 50 IDs")
        request = self._resource.channels().list(
            part=",".join(parts), id=",".join(channel_ids), maxResults=len(channel_ids)
        )
        return self._execute(request)

    def get_videos(self, video_ids: list[str], *, parts: tuple[str, ...]) -> JsonObject:
        """Retrieve requested resource parts for up to 50 video IDs."""
        if not 1 <= len(video_ids) <= 50:
            raise ValueError("video_ids must contain between 1 and 50 IDs")
        request = self._resource.videos().list(
            part=",".join(parts), id=",".join(video_ids), maxResults=len(video_ids)
        )
        return self._execute(request)

    def list_playlist_items(
        self,
        *,
        playlist_id: str,
        max_results: int,
        page_token: str | None = None,
    ) -> JsonObject:
        """Execute one page of an uploads-playlist request."""
        parameters: JsonObject = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": self._validated_page_size(max_results),
        }
        self._add_optional(parameters, pageToken=page_token)
        return self._execute(self._resource.playlistItems().list(**parameters))

    def _execute(self, request: ExecutableRequest) -> JsonObject:
        try:
            return dict(request.execute(num_retries=self._max_retries))
        except HttpError as exception:
            raise self._normalize_http_error(exception) from exception
        except (TimeoutError, socket.timeout) as exception:
            raise YouTubeTimeoutError("The YouTube API request timed out") from exception
        except OSError as exception:
            raise YouTubeAPIError("The YouTube API request failed") from exception

    @staticmethod
    def _normalize_http_error(exception: HttpError) -> YouTubeAPIError:
        status = getattr(exception.resp, "status", None)
        reason = YouTubeClient._error_reason(exception)
        if reason in {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"}:
            return QuotaExceededError("The YouTube API quota has been exceeded")
        if status == 401 or reason in {
            "accessNotConfigured",
            "authError",
            "keyInvalid",
            "ipRefererBlocked",
        }:
            return AuthenticationError("YouTube API authentication failed")
        return YouTubeAPIError(f"YouTube API request failed with status {status or 'unknown'}")

    @staticmethod
    def _error_reason(exception: HttpError) -> str | None:
        try:
            payload = json.loads(exception.content.decode("utf-8"))
            errors = payload.get("error", {}).get("errors", [])
            return str(errors[0]["reason"]) if errors else None
        except (AttributeError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _add_optional(parameters: JsonObject, **values: str | None) -> None:
        parameters.update({key: value for key, value in values.items() if value is not None})

    @staticmethod
    def _validated_page_size(value: int) -> int:
        if not 1 <= value <= 50:
            raise ValueError("max_results must be between 1 and 50")
        return value
