"""Immutable labelling-rubric contracts for ground-truth decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.label_models import GroundTruthLabel, LabelContentDigest
from app.services.backtesting.models import ResearchIdentifier

LABELLING_RUBRIC_SCHEMA_VERSION = 1
RubricText = Annotated[str, Field(min_length=1, max_length=4_000)]
RubricVersion = Annotated[int, Field(ge=1)]


class RubricCriterion(BaseModel):
    """One ordered qualitative question grounded in defined evidence items."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    criterion_id: ResearchIdentifier
    description: RubricText
    required: bool
    evidence_item_ids: Annotated[tuple[ResearchIdentifier, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_evidence_ids(self) -> RubricCriterion:
        if len(set(self.evidence_item_ids)) != len(self.evidence_item_ids):
            raise ValueError("rubric criterion evidence-item IDs must be unique")
        return self


class RubricReasonCode(BaseModel):
    """One closed reason available for specified protocol labels."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reason_code: ResearchIdentifier
    allowed_labels: Annotated[tuple[GroundTruthLabel, ...], Field(min_length=1)]
    description: RubricText

    @model_validator(mode="after")
    def validate_labels(self) -> RubricReasonCode:
        if len(set(self.allowed_labels)) != len(self.allowed_labels):
            raise ValueError("rubric reason-code labels must be unique")
        return self


class RubricDecisionRule(BaseModel):
    """Human-readable, non-executing guidance for one closed label state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: ResearchIdentifier
    label: GroundTruthLabel
    description: RubricText
    permitted_reason_codes: Annotated[
        tuple[ResearchIdentifier, ...],
        Field(min_length=1),
    ]

    @model_validator(mode="after")
    def validate_reasons(self) -> RubricDecisionRule:
        if len(set(self.permitted_reason_codes)) != len(self.permitted_reason_codes):
            raise ValueError("rubric decision-rule reason codes must be unique")
        return self


class RubricDefinition(BaseModel):
    """Versioned criteria and decision vocabulary for independent labelling."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rubric_id: ResearchIdentifier
    version: RubricVersion
    name: Annotated[str, Field(min_length=1, max_length=200)]
    purpose: RubricText
    created_at: datetime
    evidence_pack_definition_id: ResearchIdentifier
    evidence_pack_definition_version: int = Field(ge=1)
    evidence_pack_definition_digest: LabelContentDigest
    criteria: Annotated[tuple[RubricCriterion, ...], Field(min_length=1)]
    allowed_decision_states: Annotated[
        tuple[GroundTruthLabel, ...],
        Field(min_length=4, max_length=4),
    ]
    reason_codes: Annotated[tuple[RubricReasonCode, ...], Field(min_length=1)]
    decision_rules: Annotated[tuple[RubricDecisionRule, ...], Field(min_length=4)]
    digest: LabelContentDigest

    @model_validator(mode="after")
    def validate_definition(self) -> RubricDefinition:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("rubric creation timestamp must be timezone-aware")
        if self.allowed_decision_states != tuple(GroundTruthLabel):
            raise ValueError("rubric must permit every protocol label in enum order")
        collections = (
            ("criterion", tuple(item.criterion_id for item in self.criteria)),
            ("reason-code", tuple(item.reason_code for item in self.reason_codes)),
            ("decision-rule", tuple(item.rule_id for item in self.decision_rules)),
        )
        for name, identities in collections:
            if len(set(identities)) != len(identities):
                raise ValueError(f"rubric {name} identities must be unique")
        rule_labels = tuple(rule.label for rule in self.decision_rules)
        if rule_labels != tuple(GroundTruthLabel):
            raise ValueError("rubric requires one decision rule per protocol label in enum order")
        reasons = {reason.reason_code: reason for reason in self.reason_codes}
        for rule in self.decision_rules:
            for reason_code in rule.permitted_reason_codes:
                reason = reasons.get(reason_code)
                if reason is None:
                    raise ValueError("rubric decision rule references unknown reason code")
                if rule.label not in reason.allowed_labels:
                    raise ValueError("rubric reason code does not permit decision-rule label")
        return self


class RubricDocument(BaseModel):
    """Strict schema wrapper for one complete rubric definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    rubric: RubricDefinition


class RubricImportResult(BaseModel):
    """Strictly validated immutable rubric document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: RubricDocument
