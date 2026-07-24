"""Canonical serialization for governed study execution artifacts."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from app.services.backtesting.exceptions import StudyExecutionDigestMismatchError
from app.services.backtesting.study_execution_models import (
    StudyExecutionContext,
    StudyExecutionManifest,
    StudyExecutionMetadata,
    StudyExecutionResult,
)


class StudyExecutionCanonicalizer:
    """Produce stable UTF-8 JSON and validate result integrity."""

    @staticmethod
    def _json_bytes(value: Any) -> bytes:
        return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")

    @classmethod
    def calculate_result_digest(cls, metadata: StudyExecutionMetadata, context: StudyExecutionContext, manifest: StudyExecutionManifest) -> str:
        payload = {
            "metadata": metadata.model_dump(mode="json"),
            "context": context.model_dump(mode="json"),
            "manifest": manifest.model_dump(mode="json", exclude={"result_digest"}),
        }
        return sha256(cls._json_bytes(payload)).hexdigest()

    @classmethod
    def validate_result_digest(cls, result: StudyExecutionResult) -> None:
        expected = cls.calculate_result_digest(result.metadata, result.context, result.manifest)
        if expected != result.manifest.result_digest.value:
            raise StudyExecutionDigestMismatchError(("study execution result digest does not match canonical content",))

    @classmethod
    def serialize_result(cls, result: StudyExecutionResult) -> bytes:
        cls.validate_result_digest(result)
        return cls._json_bytes(result.model_dump(mode="json"))

