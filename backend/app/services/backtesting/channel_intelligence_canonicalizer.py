"""Canonical integrity for governed channel intelligence."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from app.services.backtesting.channel_intelligence_models import (
    ChannelIntelligenceManifest,
    ChannelIntelligenceMetadata,
    ChannelIntelligenceResult,
    ChannelIntelligenceSummary,
)
from app.services.backtesting.exceptions import ChannelIntelligenceDigestMismatchError
from app.services.youtube.models import Channel, Video


class ChannelIntelligenceCanonicalizer:
    """Produce stable UTF-8 JSON and validate source/result continuity."""

    @staticmethod
    def _json_bytes(value: Any) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_source_digest(cls, channel: Channel, videos: tuple[Video, ...]) -> str:
        value = {
            "channel": channel.model_dump(mode="json"),
            "videos": [video.model_dump(mode="json") for video in videos],
        }
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def calculate_result_digest(
        cls,
        metadata: ChannelIntelligenceMetadata,
        summary: ChannelIntelligenceSummary,
        manifest: ChannelIntelligenceManifest,
    ) -> str:
        value = {
            "metadata": metadata.model_dump(mode="json"),
            "summary": summary.model_dump(mode="json"),
            "manifest": manifest.model_dump(mode="json", exclude={"result_digest"}),
        }
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def validate_result_digest(cls, result: ChannelIntelligenceResult) -> None:
        expected = cls.calculate_result_digest(result.metadata, result.summary, result.manifest)
        if expected != result.manifest.result_digest.value:
            raise ChannelIntelligenceDigestMismatchError(
                ("channel intelligence digest does not match canonical content",)
            )

    @classmethod
    def serialize_result(cls, result: ChannelIntelligenceResult) -> bytes:
        cls.validate_result_digest(result)
        return cls._json_bytes(result.model_dump(mode="json"))
