"""Canonical integrity for governed statistical evaluation."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from app.services.backtesting.exceptions import StatisticalEvaluationDigestMismatchError
from app.services.backtesting.statistical_evaluation_models import (
    StatisticalEvaluationManifest,
    StatisticalEvaluationMetadata,
    StatisticalEvaluationResult,
    StatisticalEvaluationSummary,
)


class StatisticalEvaluationCanonicalizer:
    """Produce stable UTF-8 JSON and validate statistical result integrity."""

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
    def calculate_result_digest(
        cls,
        metadata: StatisticalEvaluationMetadata,
        summary: StatisticalEvaluationSummary,
        manifest: StatisticalEvaluationManifest,
    ) -> str:
        value = {
            "metadata": metadata.model_dump(mode="json"),
            "summary": summary.model_dump(mode="json"),
            "manifest": manifest.model_dump(mode="json", exclude={"result_digest"}),
        }
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def validate_result_digest(cls, result: StatisticalEvaluationResult) -> None:
        expected = cls.calculate_result_digest(
            result.metadata, result.summary, result.manifest
        )
        if expected != result.manifest.result_digest.value:
            raise StatisticalEvaluationDigestMismatchError(
                ("statistical evaluation digest does not match canonical content",)
            )

    @classmethod
    def serialize_result(cls, result: StatisticalEvaluationResult) -> bytes:
        cls.validate_result_digest(result)
        return cls._json_bytes(result.model_dump(mode="json"))

