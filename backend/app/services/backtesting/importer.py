"""Strict deterministic import of governed historical research JSON."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from app.services.backtesting.exceptions import (
    HistoricalDatasetDuplicateError,
    HistoricalDatasetDigestMismatchError,
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
        self._validate_observation_cutoff(document.manifest, observations)
        HistoricalDatasetCanonicalizer.validate_digest(document.manifest, observations)
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
    def _validate_observation_cutoff(
        manifest: HistoricalDatasetManifest,
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
    ) -> None:
        after_cutoff = tuple(
            item.observation_id
            for item in observations
            if item.observed_at > manifest.provenance.observation_cutoff
        )
        if after_cutoff:
            raise HistoricalDatasetValidationError(
                ("observations after manifest observation cutoff: " + ", ".join(after_cutoff),)
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


class HistoricalDatasetCanonicalizer:
    """Canonical serialization and SHA-256 verification for dataset documents."""

    @staticmethod
    def canonical_digest_payload(
        manifest: HistoricalDatasetManifest,
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
    ) -> bytes:
        """Serialize digest-covered content independently of input JSON formatting."""
        ordered = tuple(sorted(observations, key=lambda item: item.observation_id))
        document = {
            "manifest": manifest.model_dump(mode="json", exclude={"digest"}),
            "observations": tuple(item.model_dump(mode="json") for item in ordered),
        }
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(
        cls,
        manifest: HistoricalDatasetManifest,
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
    ) -> str:
        """Return the lowercase SHA-256 digest of canonical covered content."""
        return sha256(cls.canonical_digest_payload(manifest, observations)).hexdigest()

    @classmethod
    def validate_digest(
        cls,
        manifest: HistoricalDatasetManifest,
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
    ) -> None:
        """Fail clearly when declared and calculated digests differ."""
        calculated = cls.calculate_digest(manifest, observations)
        if calculated != manifest.digest.value:
            raise HistoricalDatasetDigestMismatchError(
                ("manifest digest does not match canonical dataset content",)
            )

    @staticmethod
    def serialize_import_result(result: HistoricalDatasetImportResult) -> bytes:
        """Serialize one validated import result as canonical schema-versioned JSON."""
        HistoricalDatasetCanonicalizer.validate_digest(
            result.manifest,
            result.dataset.observations,
        )
        document = {
            "manifest": result.manifest.model_dump(mode="json"),
            "observations": tuple(
                item.model_dump(mode="json") for item in result.dataset.observations
            ),
        }
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
