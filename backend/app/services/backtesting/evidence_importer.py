"""Strict import and canonical serialization for reviewer evidence packs."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.services.backtesting.evidence_models import (
    EVIDENCE_PACK_SCHEMA_VERSION,
    EvidenceFactDefinition,
    EvidenceItem,
    EvidenceItemDefinition,
    EvidencePack,
    EvidencePackDefinition,
    EvidencePackDocument,
    EvidencePackImportResult,
)
from app.services.backtesting.exceptions import (
    EvidencePackDigestMismatchError,
    EvidencePackReadError,
    EvidencePackSyntaxError,
    EvidencePackValidationError,
    UnsupportedEvidencePackSchemaError,
)


class EvidencePackImporter:
    """Load one strict evidence definition and concrete pack without generation."""

    def import_file(self, path: str | Path) -> EvidencePackImportResult:
        """Read and import one local evidence-pack document."""
        resolved_path = Path(path)
        try:
            payload = resolved_path.read_bytes()
        except OSError as exception:
            raise EvidencePackReadError(
                f"could not read evidence-pack file: {resolved_path}"
            ) from exception
        return self.import_json(payload)

    def import_json(self, payload: str | bytes | bytearray) -> EvidencePackImportResult:
        """Strictly validate one immutable evidence-pack document."""
        parsed = self._parse_json(payload)
        self._validate_schema_version(parsed)
        try:
            document = EvidencePackDocument.model_validate_json(
                payload,
                strict=True,
                extra="forbid",
            )
        except ValidationError as exception:
            raise EvidencePackValidationError(
                self._validation_issues(exception)
            ) from exception

        EvidencePackCanonicalizer.validate_definition_digest(document.definition)
        EvidencePackCanonicalizer.validate_pack_digest(document.pack)
        self._validate_pack_content(document.definition, document.pack)
        return EvidencePackImportResult(document=document)

    @staticmethod
    def _validate_pack_content(
        definition: EvidencePackDefinition,
        pack: EvidencePack,
    ) -> None:
        definitions = {
            item.item_id: item for item in definition.item_definitions
        }
        expected_items = tuple(definitions)
        actual_items = tuple(item.item_id for item in pack.items)
        unknown = tuple(item_id for item_id in actual_items if item_id not in definitions)
        if unknown:
            raise EvidencePackValidationError(
                ("unknown evidence items: " + ", ".join(unknown),)
            )
        expected_present_order = tuple(
            item_id for item_id in expected_items if item_id in actual_items
        )
        if actual_items != expected_present_order:
            raise EvidencePackValidationError(
                ("evidence items must follow definition order",)
            )
        missing = tuple(
            item.item_id
            for item in definition.item_definitions
            if item.required and item.item_id not in actual_items
        )
        if missing:
            raise EvidencePackValidationError(
                ("missing required evidence items: " + ", ".join(missing),)
            )
        for item in pack.items:
            EvidencePackImporter._validate_item(definitions[item.item_id], item)

    @staticmethod
    def _validate_item(
        definition: EvidenceItemDefinition,
        item: EvidenceItem,
    ) -> None:
        definitions = {fact.fact_name: fact for fact in definition.fact_definitions}
        present_names = {fact.fact_name for fact in item.facts}
        unknown = tuple(sorted(present_names - definitions.keys()))
        if unknown:
            raise EvidencePackValidationError(
                ("unknown evidence facts: " + ", ".join(unknown),)
            )
        missing = tuple(
            fact.fact_name
            for fact in definition.fact_definitions
            if fact.required and fact.fact_name not in present_names
        )
        if missing:
            raise EvidencePackValidationError(
                ("missing required evidence facts: " + ", ".join(missing),)
            )
        for fact in item.facts:
            fact_definition: EvidenceFactDefinition = definitions[fact.fact_name]
            if fact.value_type is not fact_definition.value_type:
                raise EvidencePackValidationError(
                    (f"evidence fact type mismatch: {fact.fact_name}",)
                )
            if fact.semantic_unit != fact_definition.semantic_unit:
                raise EvidencePackValidationError(
                    (f"evidence fact unit mismatch: {fact.fact_name}",)
                )
            if not fact_definition.repeatable and fact.subject_id is not None:
                raise EvidencePackValidationError(
                    (f"non-repeatable evidence fact has subject: {fact.fact_name}",)
                )
            if fact_definition.repeatable and fact.subject_id is None:
                raise EvidencePackValidationError(
                    (f"repeatable evidence fact requires subject: {fact.fact_name}",)
                )

    @staticmethod
    def _parse_json(payload: str | bytes | bytearray) -> Any:
        try:
            return json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exception:
            line = getattr(exception, "lineno", 1)
            column = getattr(exception, "colno", 1)
            raise EvidencePackSyntaxError(
                f"evidence pack is not valid JSON at line {line}, column {column}"
            ) from exception

    @staticmethod
    def _validate_schema_version(parsed: Any) -> None:
        if not isinstance(parsed, dict):
            raise EvidencePackValidationError(("document must be a JSON object",))
        version = parsed.get("schema_version")
        if version is None:
            raise EvidencePackValidationError(("schema_version is required",))
        if type(version) is not int:
            raise EvidencePackValidationError(("schema_version must be an integer",))
        if version != EVIDENCE_PACK_SCHEMA_VERSION:
            raise UnsupportedEvidencePackSchemaError(
                f"unsupported evidence-pack schema version: {version}"
            )

    @staticmethod
    def _validation_issues(exception: ValidationError) -> tuple[str, ...]:
        return tuple(
            f"{'.'.join(str(part) for part in error['loc'])}: "
            f"{error['msg']} [{error['type']}]"
            for error in exception.errors(include_url=False, include_input=False)
        )


class EvidencePackCanonicalizer:
    """Canonical SHA-256 identities and serialization for evidence contracts."""

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
    def calculate_definition_digest(cls, definition: EvidencePackDefinition) -> str:
        """Hash the complete ordered definition except its digest field."""
        value = definition.model_dump(mode="json", exclude={"digest"})
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def calculate_pack_digest(cls, pack: EvidencePack) -> str:
        """Hash the complete definition-bound pack except its digest field."""
        value = pack.model_dump(mode="json", exclude={"digest"})
        return sha256(cls._json_bytes(value)).hexdigest()

    @classmethod
    def validate_definition_digest(cls, definition: EvidencePackDefinition) -> None:
        if cls.calculate_definition_digest(definition) != definition.digest.value:
            raise EvidencePackDigestMismatchError(
                ("evidence-pack definition digest does not match canonical content",)
            )

    @classmethod
    def validate_pack_digest(cls, pack: EvidencePack) -> None:
        if cls.calculate_pack_digest(pack) != pack.digest.value:
            raise EvidencePackDigestMismatchError(
                ("evidence-pack digest does not match canonical content",)
            )

    @classmethod
    def serialize_import_result(cls, result: EvidencePackImportResult) -> bytes:
        """Return canonical JSON for one validated evidence import result."""
        cls.validate_definition_digest(result.document.definition)
        cls.validate_pack_digest(result.document.pack)
        return cls._json_bytes(result.document.model_dump(mode="json"))
