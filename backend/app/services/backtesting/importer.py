"""Strict deterministic import of governed historical research JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from app.services.backtesting.exceptions import (
    HistoricalDatasetDuplicateError,
    HistoricalDatasetReadError,
    HistoricalDatasetSyntaxError,
    HistoricalDatasetValidationError,
    UnsupportedHistoricalDatasetSchemaError,
)
from app.services.backtesting.import_models import (
    HISTORICAL_DATASET_SCHEMA_VERSION,
    HistoricalDatasetImportResult,
    HistoricalDatasetManifest,
)
from app.services.backtesting.models import (
    SubscriberRelativeBacktestDataset,
    SubscriberRelativeBacktestObservation,
)


class _HistoricalDatasetDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest: HistoricalDatasetManifest
    observations: tuple[SubscriberRelativeBacktestObservation, ...]


class HistoricalDatasetImporter:
    """Convert one strict schema-versioned JSON document into research contracts."""

    def import_file(self, path: str | Path) -> HistoricalDatasetImportResult:
        """Read and import one local historical dataset file."""
        resolved_path = Path(path)
        try:
            payload = resolved_path.read_bytes()
        except OSError as exception:
            raise HistoricalDatasetReadError(
                f"could not read historical dataset file: {resolved_path}"
            ) from exception
        return self.import_json(payload)

    def import_json(
        self,
        payload: str | bytes | bytearray,
    ) -> HistoricalDatasetImportResult:
        """Strictly validate JSON and return a canonically ordered dataset."""
        parsed = self._parse_json(payload)
        self._validate_schema_version(parsed)
        try:
            document = _HistoricalDatasetDocument.model_validate_json(
                payload,
                strict=True,
                extra="forbid",
            )
        except ValidationError as exception:
            raise HistoricalDatasetValidationError(
                self._validation_issues(exception)
            ) from exception

        observations = tuple(
            sorted(document.observations, key=lambda item: item.observation_id)
        )
        self._validate_unique_observations(observations)
        dataset = SubscriberRelativeBacktestDataset(
            dataset_id=document.manifest.dataset_id,
            version=document.manifest.dataset_version,
            observations=observations,
        )
        return HistoricalDatasetImportResult(
            manifest=document.manifest,
            dataset=dataset,
        )

    @staticmethod
    def _parse_json(payload: str | bytes | bytearray) -> Any:
        try:
            return json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exception:
            line = getattr(exception, "lineno", 1)
            column = getattr(exception, "colno", 1)
            raise HistoricalDatasetSyntaxError(
                f"historical dataset is not valid JSON at line {line}, column {column}"
            ) from exception

    @staticmethod
    def _validate_schema_version(parsed: Any) -> None:
        if not isinstance(parsed, dict):
            raise HistoricalDatasetValidationError(("document must be a JSON object",))
        manifest = parsed.get("manifest")
        if not isinstance(manifest, dict):
            raise HistoricalDatasetValidationError(("manifest must be a JSON object",))
        version = manifest.get("schema_version")
        if version is None:
            raise HistoricalDatasetValidationError(
                ("manifest.schema_version is required",)
            )
        if type(version) is not int:
            raise HistoricalDatasetValidationError(
                ("manifest.schema_version must be an integer",)
            )
        if version != HISTORICAL_DATASET_SCHEMA_VERSION:
            raise UnsupportedHistoricalDatasetSchemaError(
                f"unsupported historical dataset schema version: {version}"
            )

    @staticmethod
    def _validate_unique_observations(
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
    ) -> None:
        observation_ids = tuple(item.observation_id for item in observations)
        duplicate_ids = tuple(
            sorted(
                identifier
                for identifier in set(observation_ids)
                if observation_ids.count(identifier) > 1
            )
        )
        if duplicate_ids:
            raise HistoricalDatasetDuplicateError(
                ("duplicate observation IDs: " + ", ".join(duplicate_ids),)
            )

        snapshots = tuple((item.channel_id, item.observed_at) for item in observations)
        duplicate_snapshots = tuple(
            sorted(
                snapshot
                for snapshot in set(snapshots)
                if snapshots.count(snapshot) > 1
            )
        )
        if duplicate_snapshots:
            formatted = ", ".join(
                f"{channel_id}@{observed_at.isoformat()}"
                for channel_id, observed_at in duplicate_snapshots
            )
            raise HistoricalDatasetDuplicateError(
                ("duplicate channel snapshots: " + formatted,)
            )

    @staticmethod
    def _validation_issues(exception: ValidationError) -> tuple[str, ...]:
        issues: list[str] = []
        for error in exception.errors(include_url=False, include_input=False):
            location = ".".join(str(part) for part in error["loc"])
            issues.append(f"{location}: {error['msg']} [{error['type']}]")
        return tuple(issues)
