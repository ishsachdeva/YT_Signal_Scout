"""Typed models produced by the analytics framework."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.services.youtube.models import Channel, Video


class ChannelAnalytics(BaseModel):
    """The complete raw analytics dataset for one channel."""

    model_config = ConfigDict(frozen=True)

    channel: Channel
    videos: list[Video]
    video_count: int = Field(ge=0)
    generated_at: datetime
