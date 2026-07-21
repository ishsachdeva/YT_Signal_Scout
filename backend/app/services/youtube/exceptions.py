"""Normalized failures raised by the YouTube acquisition layer."""


class YouTubeAPIError(Exception):
    """Base class for YouTube API and response failures."""


class QuotaExceededError(YouTubeAPIError):
    """The configured YouTube project has exhausted an API quota."""


class AuthenticationError(YouTubeAPIError):
    """The configured YouTube API credential was rejected."""


class YouTubeTimeoutError(YouTubeAPIError):
    """A YouTube request timed out after its retry policy was exhausted."""


class ChannelNotFoundError(YouTubeAPIError):
    """A requested YouTube channel does not exist or is unavailable."""


class VideoNotFoundError(YouTubeAPIError):
    """A requested YouTube video does not exist or is unavailable."""
