"""Immutable reviewer evidence-pack contracts for ground-truth labelling."""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.label_models import LabelContentDigest, LabelEvidenceReference
from app.services.backtesting.models import ResearchIdentifier

EVIDENCE_PACK_SCHEMA_VERSION = 1
EvidenceText = Annotated[str, Field(min_length=1, max_length=4_000)]
EvidenceReference = LabelEvidenceReference


class EvidenceValueType(StrEnum):
    """Closed primitive fact types supported by evidence snapshots."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    TEXT = "text"
    TIMESTAMP = "timestamp"


class EvidenceFactDefinition(BaseModel):
    """One named typed fact expected inside an evidence item."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_name: ResearchIdentifier
    value_type: EvidenceValueType
    required: bool
    repeatable: bool
    semantic_unit: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]
    description: EvidenceText


class EvidenceItemDefinition(BaseModel):
    """One ordered reviewer-facing group of factual evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: ResearchIdentifier
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: EvidenceText
    required: bool
    fact_definitions: Annotated[
        tuple[EvidenceFactDefinition, ...],
        Field(min_length=1),
    ]

    @model_validator(mode="after")
    def validate_facts(self) -> EvidenceItemDefinition:
        names = tuple(item.fact_name for item in self.fact_definitions)
        if len(set(names)) != len(names):
            raise ValueError("evidence fact-definition names must be unique")
        return self


class EvidencePackDefinition(BaseModel):
    """Versioned ordered schema for one class of reviewer evidence pack."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    definition_id: ResearchIdentifier
    version: int = Field(ge=1)
    name: Annotated[str, Field(min_length=1, max_length=200)]
    purpose: EvidenceText
    created_at: datetime
    item_definitions: Annotated[
        tuple[EvidenceItemDefinition, ...],
        Field(min_length=1),
    ]
    digest: LabelContentDigest

    @model_validator(mode="after")
    def validate_definition(self) -> EvidencePackDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("evidence-pack definition timestamp must be timezone-aware")
        identities = tuple(item.item_id for item in self.item_definitions)
        if len(set(identities)) != len(identities):
            raise ValueError("evidence item-definition IDs must be unique")
        return self


class EvidenceSnapshot(BaseModel):
    """Exact historical observation represented by one immutable evidence pack."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: ResearchIdentifier
    snapshot_version: int = Field(ge=1)
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    observation_id: ResearchIdentifier
    channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    observed_at: datetime

    @model_validator(mode="after")
    def validate_time(self) -> EvidenceSnapshot:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("evidence snapshot timestamp must be timezone-aware")
        return self


class EvidenceFact(BaseModel):
    """One immutable primitive fact, optionally scoped to a repeated subject."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_name: ResearchIdentifier
    subject_id: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]
    value_type: EvidenceValueType
    value: bool | int | float | str | datetime
    semantic_unit: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]

    @model_validator(mode="before")
    @classmethod
    def parse_timestamp_value(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        if value.get("value_type") != EvidenceValueType.TIMESTAMP:
            return value
        raw_value = value.get("value")
        if not isinstance(raw_value, str):
            return value
        try:
            parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            return value
        return {**value, "value": parsed}

    @model_validator(mode="after")
    def validate_value(self) -> EvidenceFact:
        expected: dict[EvidenceValueType, type[Any]] = {
            EvidenceValueType.BOOLEAN: bool,
            EvidenceValueType.INTEGER: int,
            EvidenceValueType.FLOAT: float,
            EvidenceValueType.TEXT: str,
            EvidenceValueType.TIMESTAMP: datetime,
        }
        value_type = type(self.value)
        if value_type is not expected[self.value_type]:
            raise ValueError("evidence fact value must match its declared type exactly")
        if isinstance(self.value, datetime) and (
            self.value.tzinfo is None or self.value.utcoffset() is None
        ):
            raise ValueError("evidence timestamp fact must be timezone-aware")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("evidence float fact must be finite")
        return self


class EvidenceItem(BaseModel):
    """One definition-bound ordered group of snapshot facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: ResearchIdentifier
    facts: Annotated[tuple[EvidenceFact, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_fact_identity(self) -> EvidenceItem:
        identities = tuple((fact.fact_name, fact.subject_id) for fact in self.facts)
        if len(set(identities)) != len(identities):
            raise ValueError("evidence fact name/subject identities must be unique")
        expected = tuple(sorted(identities, key=lambda item: (item[0], item[1] or "")))
        if identities != expected:
            raise ValueError("evidence facts must be canonically ordered")
        return self


class EvidencePack(BaseModel):
    """Immutable definition-bound reviewer evidence for one observation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_pack_id: ResearchIdentifier
    version: int = Field(ge=1)
    definition_id: ResearchIdentifier
    definition_version: int = Field(ge=1)
    definition_digest: LabelContentDigest
    created_at: datetime
    snapshot: EvidenceSnapshot
    items: Annotated[tuple[EvidenceItem, ...], Field(min_length=1)]
    digest: LabelContentDigest

    @model_validator(mode="after")
    def validate_pack(self) -> EvidencePack:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("evidence-pack creation timestamp must be timezone-aware")
        if self.created_at < self.snapshot.observed_at:
            raise ValueError("evidence pack cannot precede its observation")
        identities = tuple(item.item_id for item in self.items)
        if len(set(identities)) != len(identities):
            raise ValueError("evidence item IDs must be unique")
        return self


class EvidencePackDocument(BaseModel):
    """One complete definition and one concrete pack for strict import."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    definition: EvidencePackDefinition
    pack: EvidencePack

    @model_validator(mode="after")
    def validate_binding(self) -> EvidencePackDocument:
        if self.pack.definition_id != self.definition.definition_id:
            raise ValueError("evidence pack and definition IDs must match")
        if self.pack.definition_version != self.definition.version:
            raise ValueError("evidence pack and definition versions must match")
        if self.pack.definition_digest != self.definition.digest:
            raise ValueError("evidence pack must bind the exact definition digest")
        return self


class EvidencePackImportResult(BaseModel):
    """Strictly validated immutable evidence definition and pack."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: EvidencePackDocument
