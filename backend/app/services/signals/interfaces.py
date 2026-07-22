"""Contracts for independently testable business signal rules."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.services.analytics.models import CalculatedChannelAnalytics
from app.services.signals.models import RuleId, Signal


@runtime_checkable
class SignalRule(Protocol):
    """A deterministic policy that interprets a complete analytics snapshot."""

    @property
    def rule_id(self) -> RuleId: ...

    @property
    def rule_version(self) -> int: ...

    def evaluate(
        self, analytics: CalculatedChannelAnalytics
    ) -> tuple[Signal, ...]: ...
