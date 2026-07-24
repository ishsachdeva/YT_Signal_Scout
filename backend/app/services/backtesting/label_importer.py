"""Strict deterministic import of governed ground-truth label JSON."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from app.services.backtesting.exceptions import (
    GroundTruthLabelDigestMismatchError,
    GroundTruthLabelDuplicateError,
    GroundTruthLabelReadError,
    GroundTruthLabelSyntaxError,
    GroundTruthLabelValidationError,
    UnsupportedGroundTruthLabelSchemaError,
)
from app.services.backtesting.label_models import (
    GROUND_TRUTH_LABEL_SCHEMA_VERSION,
    GroundTruthLabelArtifact,
    GroundTruthLabelImportResult,
    GroundTruthLabelSet,
    GroundTruthLabelSetManifest,
)


class _GroundTruthLabelDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest: GroundTruthLabelSetManifest
    artifacts: tuple[GroundTruthLabelArtifact, ...]


class GroundTruthLabelImporter:
    """Load one strict label document without executing research."""

    def import_file(self, path: str | Path) -> GroundTruthLabelImportResult:
        """Read and import one local ground-truth label file."""
        resolved_path = Path(path)
        try:
            payload = resolved_path.read_bytes()
        except OSError as exception:
            raise GroundTruthLabelReadError(
                f"could not read ground-truth label file: {resolved_path}"
            ) from exception
        return self.import_json(payload)

    def import_json(self, payload: str | bytes | bytearray) -> GroundTruthLabelImportResult:
        """Strictly validate and canonically order one label set."""
        parsed = self._parse_json(payload)
        self._validate_schema_version(parsed)
        try:
            document = _GroundTruthLabelDocument.model_validate_json(
                payload,
                strict=True,
                extra="forbid",
            )
        except ValidationError as exception:
            raise GroundTruthLabelValidationError(
                self._validation_issues(exception)
            ) from exception

        artifacts = tuple(
            sorted(
                (
                    artifact.model_copy(
                        update={
                            "independent_reviews": tuple(
                                sorted(
                                    artifact.independent_reviews,
                                    key=lambda review: review.review_id,
                                )
                            )
                        }
                    )
                    for artifact in document.artifacts
                ),
                key=lambda artifact: (artifact.observation_id, artifact.artifact_id),
            )
        )
        self._validate_artifacts(document.manifest, artifacts)
        GroundTruthLabelCanonicalizer.validate_digest(document.manifest, artifacts)
        label_set = GroundTruthLabelSet(
            label_set_id=document.manifest.label_set_id,
            version=document.manifest.label_set_version,
            dataset_id=document.manifest.dataset_id,
            dataset_version=document.manifest.dataset_version,
            artifacts=artifacts,
        )
        return GroundTruthLabelImportResult(
            manifest=document.manifest,
            label_set=label_set,
        )

    @staticmethod
    def _parse_json(payload: str | bytes | bytearray) -> Any:
        try:
            return json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exception:
            line = getattr(exception, "lineno", 1)
            column = getattr(exception, "colno", 1)
            raise GroundTruthLabelSyntaxError(
                f"ground-truth labels are not valid JSON at line {line}, column {column}"
            ) from exception

    @staticmethod
    def _validate_schema_version(parsed: Any) -> None:
        if not isinstance(parsed, dict):
            raise GroundTruthLabelValidationError(("document must be a JSON object",))
        manifest = parsed.get("manifest")
        if not isinstance(manifest, dict):
            raise GroundTruthLabelValidationError(("manifest must be a JSON object",))
        version = manifest.get("schema_version")
        if version is None:
            raise GroundTruthLabelValidationError(("manifest.schema_version is required",))
        if type(version) is not int:
            raise GroundTruthLabelValidationError(
                ("manifest.schema_version must be an integer",)
            )
        if version != GROUND_TRUTH_LABEL_SCHEMA_VERSION:
            raise UnsupportedGroundTruthLabelSchemaError(
                f"unsupported ground-truth label schema version: {version}"
            )

    @staticmethod
    def _validate_artifacts(
        manifest: GroundTruthLabelSetManifest,
        artifacts: tuple[GroundTruthLabelArtifact, ...],
    ) -> None:
        if not artifacts:
            raise GroundTruthLabelValidationError(("label set requires artifacts",))
        identity_fields = {
            "artifact IDs": tuple(item.artifact_id for item in artifacts),
            "observation IDs": tuple(item.observation_id for item in artifacts),
            "channel IDs": tuple(item.channel_id for item in artifacts),
        }
        for name, values in identity_fields.items():
            duplicates = tuple(
                sorted(value for value in set(values) if values.count(value) > 1)
            )
            if duplicates:
                raise GroundTruthLabelDuplicateError(
                    (f"duplicate {name}: " + ", ".join(duplicates),)
                )

        reference = artifacts[0].evidence
        for artifact in artifacts:
            if (
                artifact.label_set_id != manifest.label_set_id
                or artifact.label_set_version != manifest.label_set_version
            ):
                raise GroundTruthLabelValidationError(
                    (f"artifact label-set binding mismatch: {artifact.artifact_id}",)
                )
            if (
                artifact.dataset_id != manifest.dataset_id
                or artifact.dataset_version != manifest.dataset_version
            ):
                raise GroundTruthLabelValidationError(
                    (f"artifact dataset binding mismatch: {artifact.artifact_id}",)
                )
            if (
                artifact.evidence.evidence_pack_definition_id
                != reference.evidence_pack_definition_id
                or artifact.evidence.evidence_pack_definition_version
                != reference.evidence_pack_definition_version
                or artifact.evidence.rubric_id != reference.rubric_id
                or artifact.evidence.rubric_version != reference.rubric_version
                or artifact.evidence.rubric_digest != reference.rubric_digest
            ):
                raise GroundTruthLabelValidationError(
                    ("label artifacts must share evidence-pack and rubric versions",)
                )
            review_times = tuple(
                review.reviewed_at for review in artifact.independent_reviews
            )
            decision_times = review_times + (
                ()
                if artifact.adjudication is None
                else (artifact.adjudication.adjudicated_at,)
            )
            if max(decision_times) > manifest.created_at:
                raise GroundTruthLabelValidationError(
                    (f"label decision occurs after set creation: {artifact.artifact_id}",)
                )

    @staticmethod
    def _validation_issues(exception: ValidationError) -> tuple[str, ...]:
        issues: list[str] = []
        for error in exception.errors(include_url=False, include_input=False):
            location = ".".join(str(part) for part in error["loc"])
            issues.append(f"{location}: {error['msg']} [{error['type']}]")
        return tuple(issues)


class GroundTruthLabelCanonicalizer:
    """Canonical serialization and SHA-256 integrity for label sets."""

    @staticmethod
    def canonical_digest_payload(
        manifest: GroundTruthLabelSetManifest,
        artifacts: tuple[GroundTruthLabelArtifact, ...],
    ) -> bytes:
        """Serialize digest-covered label facts independent of supplied order."""
        ordered_artifacts = tuple(
            sorted(artifacts, key=lambda item: (item.observation_id, item.artifact_id))
        )
        document = {
            "manifest": manifest.model_dump(mode="json", exclude={"digest"}),
            "artifacts": tuple(
                {
                    **artifact.model_dump(mode="json", exclude={"independent_reviews"}),
                    "independent_reviews": tuple(
                        review.model_dump(mode="json")
                        for review in sorted(
                            artifact.independent_reviews,
                            key=lambda review: review.review_id,
                        )
                    ),
                }
                for artifact in ordered_artifacts
            ),
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
        manifest: GroundTruthLabelSetManifest,
        artifacts: tuple[GroundTruthLabelArtifact, ...],
    ) -> str:
        """Return the canonical lowercase SHA-256 label-set digest."""
        return sha256(cls.canonical_digest_payload(manifest, artifacts)).hexdigest()

    @classmethod
    def validate_digest(
        cls,
        manifest: GroundTruthLabelSetManifest,
        artifacts: tuple[GroundTruthLabelArtifact, ...],
    ) -> None:
        """Reject label content that differs from its declared digest."""
        if cls.calculate_digest(manifest, artifacts) != manifest.digest.value:
            raise GroundTruthLabelDigestMismatchError(
                ("manifest digest does not match canonical ground-truth labels",)
            )

    @classmethod
    def serialize_import_result(cls, result: GroundTruthLabelImportResult) -> bytes:
        """Serialize one validated label import result to canonical JSON."""
        cls.validate_digest(result.manifest, result.label_set.artifacts)
        ordered_artifacts = tuple(
            sorted(
                result.label_set.artifacts,
                key=lambda item: (item.observation_id, item.artifact_id),
            )
        )
        document = {
            "manifest": result.manifest.model_dump(mode="json"),
            "artifacts": tuple(
                {
                    **artifact.model_dump(mode="json", exclude={"independent_reviews"}),
                    "independent_reviews": tuple(
                        review.model_dump(mode="json")
                        for review in sorted(
                            artifact.independent_reviews,
                            key=lambda review: review.review_id,
                        )
                    ),
                }
                for artifact in ordered_artifacts
            ),
        }
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
