"""Strict import and canonical serialization for labelling rubrics."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.services.backtesting.exceptions import (
    RubricDigestMismatchError,
    RubricReadError,
    RubricSyntaxError,
    RubricValidationError,
    UnsupportedRubricSchemaError,
)
from app.services.backtesting.rubric_models import (
    LABELLING_RUBRIC_SCHEMA_VERSION,
    RubricDocument,
    RubricImportResult,
)


class RubricImporter:
    """Load one strict rubric without evaluating a label."""

    def import_file(self, path: str | Path) -> RubricImportResult:
        resolved_path = Path(path)
        try:
            payload = resolved_path.read_bytes()
        except OSError as exception:
            raise RubricReadError(
                f"could not read labelling-rubric file: {resolved_path}"
            ) from exception
        return self.import_json(payload)

    def import_json(self, payload: str | bytes | bytearray) -> RubricImportResult:
        parsed = self._parse_json(payload)
        self._validate_schema_version(parsed)
        try:
            document = RubricDocument.model_validate_json(
                payload,
                strict=True,
                extra="forbid",
            )
        except ValidationError as exception:
            raise RubricValidationError(
                self._validation_issues(exception)
            ) from exception
        RubricCanonicalizer.validate_digest(document)
        return RubricImportResult(document=document)

    @staticmethod
    def _parse_json(payload: str | bytes | bytearray) -> Any:
        try:
            return json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exception:
            line = getattr(exception, "lineno", 1)
            column = getattr(exception, "colno", 1)
            raise RubricSyntaxError(
                f"labelling rubric is not valid JSON at line {line}, column {column}"
            ) from exception

    @staticmethod
    def _validate_schema_version(parsed: Any) -> None:
        if not isinstance(parsed, dict):
            raise RubricValidationError(("document must be a JSON object",))
        version = parsed.get("schema_version")
        if version is None:
            raise RubricValidationError(("schema_version is required",))
        if type(version) is not int:
            raise RubricValidationError(("schema_version must be an integer",))
        if version != LABELLING_RUBRIC_SCHEMA_VERSION:
            raise UnsupportedRubricSchemaError(
                f"unsupported labelling-rubric schema version: {version}"
            )

    @staticmethod
    def _validation_issues(exception: ValidationError) -> tuple[str, ...]:
        return tuple(
            f"{'.'.join(str(part) for part in error['loc'])}: "
            f"{error['msg']} [{error['type']}]"
            for error in exception.errors(include_url=False, include_input=False)
        )


class RubricCanonicalizer:
    """Canonical SHA-256 identity and serialization for one rubric."""

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
    def calculate_digest(cls, document: RubricDocument) -> str:
        value = document.model_dump(mode="json")
        rubric = value["rubric"]
        del rubric["digest"]
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def validate_digest(cls, document: RubricDocument) -> None:
        if cls.calculate_digest(document) != document.rubric.digest.value:
            raise RubricDigestMismatchError(
                ("rubric digest does not match canonical content",)
            )

    @classmethod
    def serialize_import_result(cls, result: RubricImportResult) -> bytes:
        cls.validate_digest(result.document)
        return cls._json_bytes(result.document.model_dump(mode="json"))
