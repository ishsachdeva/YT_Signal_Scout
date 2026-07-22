"""Deterministic orchestration for explicitly registered signal rules."""

from __future__ import annotations

from collections.abc import Sequence

from app.services.analytics.models import CalculatedChannelAnalytics
from app.services.signals.exceptions import (
    DuplicateSignalRuleError,
    InvalidSignalRuleOutputError,
)
from app.services.signals.interfaces import SignalRule
from app.services.signals.models import RuleId, Signal


class SignalEngine:
    """Execute signal rules in explicit injection order without interpretation."""

    def __init__(self, rules: Sequence[SignalRule]) -> None:
        self._rules = tuple(rules)
        self._validate_unique_rule_ids()

    def evaluate(
        self, analytics: CalculatedChannelAnalytics
    ) -> tuple[Signal, ...]:
        """Return rule outputs in rule order and each rule's output order."""
        signals: list[Signal] = []
        for rule in self._rules:
            rule_signals = rule.evaluate(analytics)
            self._validate_rule_output(rule, rule_signals)
            signals.extend(rule_signals)
        return tuple(signals)

    def _validate_unique_rule_ids(self) -> None:
        registered_ids: set[RuleId] = set()
        for rule in self._rules:
            if rule.rule_id in registered_ids:
                raise DuplicateSignalRuleError(
                    f"duplicate signal rule registered: '{rule.rule_id.root}'"
                )
            registered_ids.add(rule.rule_id)

    @staticmethod
    def _validate_rule_output(
        rule: SignalRule,
        signals: tuple[Signal, ...],
    ) -> None:
        if not isinstance(signals, tuple):
            raise InvalidSignalRuleOutputError(
                f"signal rule '{rule.rule_id.root}' must return a tuple"
            )
        for signal in signals:
            if not isinstance(signal, Signal):
                raise InvalidSignalRuleOutputError(
                    f"signal rule '{rule.rule_id.root}' returned a non-Signal value"
                )
            if signal.rule_id != rule.rule_id or signal.rule_version != rule.rule_version:
                raise InvalidSignalRuleOutputError(
                    f"signal rule '{rule.rule_id.root}' returned mismatched provenance"
                )
