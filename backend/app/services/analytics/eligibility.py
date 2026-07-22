"""Deterministic Eligible Video Policy v1 classification."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.analytics.models import ChannelAnalytics
from app.services.analytics.validation import validate_eligibility_classification_input
from app.services.youtube.models import (
    LiveState,
    PrivacyStatus,
    Video,
    VideoAvailability,
    VideoFormat,
)

_MINIMUM_VIDEO_AGE = timedelta(hours=24)
_MAXIMUM_VIDEO_AGE = timedelta(days=90)


class VideoExclusionReason(StrEnum):
    """Closed primary reasons for normal Eligible Video Policy v1 exclusions."""

    UNAVAILABLE = "unavailable"
    DELETED = "deleted"
    UNKNOWN_AVAILABILITY = "unknown_availability"
    PRIVATE = "private"
    UNLISTED = "unlisted"
    UNKNOWN_PRIVACY = "unknown_privacy"
    MISSING_PUBLICATION_TIME = "missing_publication_time"
    TOO_YOUNG = "too_young"
    TOO_OLD = "too_old"
    MISSING_VIEW_COUNT = "missing_view_count"
    UPCOMING = "upcoming"
    CURRENTLY_LIVE = "currently_live"
    UNKNOWN_LIVE_STATE = "unknown_live_state"
    UNKNOWN_FORMAT = "unknown_format"
    UNSUPPORTED_FORMAT = "unsupported_format"


_AVAILABILITY_EXCLUSIONS = {
    VideoAvailability.UNAVAILABLE: VideoExclusionReason.UNAVAILABLE,
    VideoAvailability.DELETED: VideoExclusionReason.DELETED,
    VideoAvailability.UNKNOWN: VideoExclusionReason.UNKNOWN_AVAILABILITY,
}

_PRIVACY_EXCLUSIONS = {
    PrivacyStatus.PRIVATE: VideoExclusionReason.PRIVATE,
    PrivacyStatus.UNLISTED: VideoExclusionReason.UNLISTED,
    None: VideoExclusionReason.UNKNOWN_PRIVACY,
}

_LIVE_STATE_EXCLUSIONS = {
    LiveState.UPCOMING: VideoExclusionReason.UPCOMING,
    LiveState.LIVE: VideoExclusionReason.CURRENTLY_LIVE,
    LiveState.UNKNOWN: VideoExclusionReason.UNKNOWN_LIVE_STATE,
}


class VideoExclusion(BaseModel):
    """One deterministic primary exclusion for a canonical video."""

    model_config = ConfigDict(frozen=True)

    video_id: str
    reason: VideoExclusionReason


class EligibleVideoClassification(BaseModel):
    """Immutable format-specific result of Eligible Video Policy v1."""

    model_config = ConfigDict(frozen=True)

    eligible_standard_videos: tuple[Video, ...]
    eligible_shorts: tuple[Video, ...]
    eligible_livestream_replays: tuple[Video, ...]
    exclusions: tuple[VideoExclusion, ...]
    evaluated_at: datetime
    policy_version: Literal[1] = 1


class EligibleVideoClassifier:
    """Classify canonical videos without mutation, I/O, or hidden time input."""

    def classify(
        self,
        source_dataset: ChannelAnalytics,
        evaluation_time: datetime,
    ) -> EligibleVideoClassification:
        """Return source-ordered format bases and deterministic exclusions."""
        validate_eligibility_classification_input(source_dataset, evaluation_time)

        standard_videos: list[Video] = []
        shorts: list[Video] = []
        livestream_replays: list[Video] = []
        exclusions: list[VideoExclusion] = []

        for video in source_dataset.videos:
            reason = self._exclusion_reason(video, evaluation_time)
            if reason is not None:
                exclusions.append(VideoExclusion(video_id=video.id, reason=reason))
            elif video.format is VideoFormat.STANDARD:
                standard_videos.append(video)
            elif video.format is VideoFormat.SHORT:
                shorts.append(video)
            else:
                livestream_replays.append(video)

        return EligibleVideoClassification(
            eligible_standard_videos=tuple(standard_videos),
            eligible_shorts=tuple(shorts),
            eligible_livestream_replays=tuple(livestream_replays),
            exclusions=tuple(exclusions),
            evaluated_at=evaluation_time,
        )

    @staticmethod
    def _exclusion_reason(
        video: Video,
        evaluation_time: datetime,
    ) -> VideoExclusionReason | None:
        if reason := _AVAILABILITY_EXCLUSIONS.get(video.availability):
            return reason

        if reason := _PRIVACY_EXCLUSIONS.get(video.privacy_status):
            return reason

        if video.published_at is None:
            return VideoExclusionReason.MISSING_PUBLICATION_TIME

        video_age = evaluation_time - video.published_at
        if video_age < _MINIMUM_VIDEO_AGE:
            return VideoExclusionReason.TOO_YOUNG
        if video_age > _MAXIMUM_VIDEO_AGE:
            return VideoExclusionReason.TOO_OLD

        if video.view_count is None:
            return VideoExclusionReason.MISSING_VIEW_COUNT

        if reason := _LIVE_STATE_EXCLUSIONS.get(video.live_state):
            return reason

        if video.format is VideoFormat.UNKNOWN:
            return VideoExclusionReason.UNKNOWN_FORMAT

        supported_combination = (
            video.live_state is LiveState.NOT_LIVE
            and video.format in {VideoFormat.STANDARD, VideoFormat.SHORT}
        ) or (
            video.live_state is LiveState.COMPLETE
            and video.format is VideoFormat.LIVE_REPLAY
        )
        if not supported_combination:
            return VideoExclusionReason.UNSUPPORTED_FORMAT

        return None
