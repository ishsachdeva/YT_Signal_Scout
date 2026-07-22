"""Business signal evaluation contracts and orchestration."""

from app.services.signals.engine import SignalEngine
from app.services.signals.evidence import (
    EvidenceAvailability,
    EvidenceFact,
    EvidenceUnit,
    MetricEvidence,
    QualificationEvidence,
    SignalEvidenceBundle,
    SignalEvidenceContext,
)
from app.services.signals.evidence_builder import SignalEvidenceBuilder
from app.services.signals.exceptions import (
    DuplicateSignalRuleError,
    InvalidSignalRuleOutputError,
    SignalError,
)
from app.services.signals.interfaces import SignalRule
from app.services.signals.models import (
    ReasonCode,
    RuleId,
    Signal,
    SignalEvidence,
    SignalPolarity,
    SignalType,
)

__all__ = [
    "DuplicateSignalRuleError",
    "InvalidSignalRuleOutputError",
    "ReasonCode",
    "RuleId",
    "Signal",
    "SignalEngine",
    "EvidenceAvailability",
    "EvidenceFact",
    "EvidenceUnit",
    "MetricEvidence",
    "QualificationEvidence",
    "SignalEvidenceBuilder",
    "SignalEvidenceBundle",
    "SignalEvidenceContext",
    "SignalError",
    "SignalEvidence",
    "SignalPolarity",
    "SignalRule",
    "SignalType",
]
