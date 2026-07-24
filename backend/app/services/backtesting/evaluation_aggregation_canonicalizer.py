"""Canonical integrity for counts-only evaluation aggregation."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from app.services.backtesting.evaluation_aggregation_models import (
    EvaluationAggregationManifest,
    EvaluationAggregationMetadata,
    EvaluationAggregationResult,
    EvaluationAggregationSummary,
)
from app.services.backtesting.exceptions import EvaluationAggregationDigestMismatchError


class EvaluationAggregationCanonicalizer:
    """Produce stable UTF-8 JSON and validate aggregation integrity."""

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
        metadata: EvaluationAggregationMetadata,
        summary: EvaluationAggregationSummary,
        manifest: EvaluationAggregationManifest,
    ) -> str:
        value = {
            "metadata": metadata.model_dump(mode="json"),
            "summary": summary.model_dump(mode="json"),
            "manifest": manifest.model_dump(mode="json", exclude={"result_digest"}),
        }
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def validate_result_digest(cls, result: EvaluationAggregationResult) -> None:
        expected = cls.calculate_result_digest(
            result.metadata, result.summary, result.manifest
        )
        if expected != result.manifest.result_digest.value:
            raise EvaluationAggregationDigestMismatchError(
                ("evaluation aggregation digest does not match canonical content",)
            )

    @classmethod
    def serialize_result(cls, result: EvaluationAggregationResult) -> bytes:
        cls.validate_result_digest(result)
        return cls._json_bytes(result.model_dump(mode="json"))

