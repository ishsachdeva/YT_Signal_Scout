"""Canonical SHA-256 integrity for observation-level evaluations."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from app.services.backtesting.exceptions import EvaluationDigestMismatchError
from app.services.backtesting.labelled_evaluation_models import (
    EvaluationManifest,
    EvaluationMetadata,
    EvaluationResult,
    ObservationEvaluation,
    ObservationPrediction,
)


class EvaluationCanonicalizer:
    """Produce stable JSON for predictions and immutable evaluation results."""

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
    def calculate_predictions_digest(
        cls, predictions: tuple[ObservationPrediction, ...]
    ) -> str:
        return sha256(
            cls._json_bytes(tuple(item.model_dump(mode="json") for item in predictions))
        ).hexdigest()

    @classmethod
    def calculate_result_digest(
        cls,
        metadata: EvaluationMetadata,
        observations: tuple[ObservationEvaluation, ...],
        manifest: EvaluationManifest,
    ) -> str:
        value = {
            "metadata": metadata.model_dump(mode="json"),
            "observations": tuple(item.model_dump(mode="json") for item in observations),
            "manifest": manifest.model_dump(mode="json", exclude={"result_digest"}),
        }
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def validate_result_digest(cls, result: EvaluationResult) -> None:
        expected = cls.calculate_result_digest(
            result.metadata, result.observations, result.manifest
        )
        if expected != result.manifest.result_digest.value:
            raise EvaluationDigestMismatchError(
                ("evaluation result digest does not match canonical content",)
            )

    @classmethod
    def serialize_result(cls, result: EvaluationResult) -> bytes:
        cls.validate_result_digest(result)
        return cls._json_bytes(result.model_dump(mode="json"))

