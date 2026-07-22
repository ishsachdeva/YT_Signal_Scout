"""Immutable domain models for deterministic business signals."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel, StrictFloat, StrictInt

from app.services.analytics.models import MetricType

MachineIdentifier = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$", min_length=1, max_length=100),
]
EvidenceValue = StrictInt | StrictFloat | None


class SignalType(RootModel[MachineIdentifier]):
    """Stable machine identity for a signal without a speculative taxonomy."""

    model_config = ConfigDict(frozen=True)


class RuleId(RootModel[MachineIdentifier]):
    """Stable business identity for a signal rule."""

    model_config = ConfigDict(frozen=True)


class ReasonCode(RootModel[MachineIdentifier]):
    """Stable machine-readable explanation code emitted by a rule."""

    model_config = ConfigDict(frozen=True)


class SignalPolarity(str, Enum):
    """Whether a signal is favorable, unfavorable, or informational."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    INFORMATIONAL = "informational"


class SignalEvidence(BaseModel):
    """One typed metric observation supporting a signal."""

    model_config = ConfigDict(frozen=True)

    metric: MetricType
    observed_value: EvidenceValue
    source_channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    source_generated_at: datetime


class Signal(BaseModel):
    """A deterministic, machine-readable interpretation of analytics evidence."""

    model_config = ConfigDict(frozen=True)

    signal_type: SignalType
    polarity: SignalPolarity
    reason_code: ReasonCode
    rule_id: RuleId
    rule_version: Annotated[int, Field(ge=1)]
    evidence: Annotated[tuple[SignalEvidence, ...], Field(min_length=1)]
