from __future__ import annotations

import unittest
from datetime import UTC, datetime
from typing import cast

from app.services.analytics.models import (
    CalculatedChannelAnalytics,
    ChannelAnalytics,
    MetricType,
    OutlierResult,
)
from app.services.signals.engine import SignalEngine
from app.services.signals.exceptions import (
    DuplicateSignalRuleError,
    InvalidSignalRuleOutputError,
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
from app.services.youtube.models import Channel


def _analytics() -> CalculatedChannelAnalytics:
    generated_at = datetime(2026, 7, 22, tzinfo=UTC)
    return CalculatedChannelAnalytics(
        source_dataset=ChannelAnalytics(
            channel=Channel(id="channel-1", title="Channel"),
            videos=[],
            generated_at=generated_at,
        ),
        channel_age=365,
        upload_frequency=2.0,
        average_views=1000.0,
        median_views=900.0,
        views_per_day=50.0,
        view_distribution=0.4,
        upload_consistency=0.8,
        view_outlier=OutlierResult(
            highest_video_id=None,
            highest_z_score=0.0,
            lowest_video_id=None,
            lowest_z_score=0.0,
        ),
        view_growth_rate=0.1,
        view_engagement_rate=None,
    )


def _signal(name: str, rule_id: RuleId, version: int = 1) -> Signal:
    return Signal(
        signal_type=SignalType(name),
        polarity=SignalPolarity.INFORMATIONAL,
        reason_code=ReasonCode(f"{name}.reason"),
        rule_id=rule_id,
        rule_version=version,
        evidence=(
            SignalEvidence(
                metric=MetricType.AVERAGE_VIEWS,
                observed_value=1000.0,
                source_channel_id="channel-1",
                source_generated_at=datetime(2026, 7, 22, tzinfo=UTC),
            ),
        ),
    )


class RecordingRule:
    def __init__(
        self,
        rule_id: str,
        outputs: tuple[Signal, ...],
        execution_log: list[str],
        version: int = 1,
    ) -> None:
        self._rule_id = RuleId(rule_id)
        self._outputs = outputs
        self._version = version
        self._execution_log = execution_log
        self.received_analytics: list[CalculatedChannelAnalytics] = []

    @property
    def rule_id(self) -> RuleId:
        return self._rule_id

    @property
    def rule_version(self) -> int:
        return self._version

    def evaluate(
        self, analytics: CalculatedChannelAnalytics
    ) -> tuple[Signal, ...]:
        self._execution_log.append(self.rule_id.root)
        self.received_analytics.append(analytics)
        return self._outputs


class FailingRule(RecordingRule):
    def __init__(self, rule_id: str, error: Exception, log: list[str]) -> None:
        super().__init__(rule_id, (), log)
        self._error = error

    def evaluate(
        self, analytics: CalculatedChannelAnalytics
    ) -> tuple[Signal, ...]:
        self._execution_log.append(self.rule_id.root)
        self.received_analytics.append(analytics)
        raise self._error


class ListReturningRule(RecordingRule):
    def evaluate(  # type: ignore[override]
        self, analytics: CalculatedChannelAnalytics
    ) -> list[Signal]:
        return list(self._outputs)


class NonSignalReturningRule(RecordingRule):
    def evaluate(  # type: ignore[override]
        self, analytics: CalculatedChannelAnalytics
    ) -> tuple[object, ...]:
        return (object(),)


class SignalRuleContractTests(unittest.TestCase):
    def test_structural_contract_accepts_a_minimal_rule(self) -> None:
        rule = RecordingRule("test.rule", (), [])

        self.assertIsInstance(rule, SignalRule)
        self.assertEqual(rule.evaluate(_analytics()), ())

    def test_zero_one_and_multiple_signal_outputs_are_supported(self) -> None:
        log: list[str] = []
        rule_id = RuleId("test.rule")
        rules = (
            RecordingRule("test.zero", (), log),
            RecordingRule("test.one", (_signal("test.one", rule_id),), log),
            RecordingRule(
                "test.many",
                (_signal("test.first", rule_id), _signal("test.second", rule_id)),
                log,
            ),
        )

        self.assertEqual([len(rule.evaluate(_analytics())) for rule in rules], [0, 1, 2])


class SignalEngineTests(unittest.TestCase):
    def test_empty_engine_returns_immutable_empty_collection(self) -> None:
        self.assertEqual(SignalEngine(()).evaluate(_analytics()), ())

    def test_rules_execute_once_and_output_order_is_preserved(self) -> None:
        log: list[str] = []
        first_id = RuleId("test.first_rule")
        second_id = RuleId("test.second_rule")
        first = RecordingRule(
            first_id.root,
            (_signal("test.a", first_id), _signal("test.b", first_id)),
            log,
        )
        silent = RecordingRule("test.silent_rule", (), log)
        second = RecordingRule(
            second_id.root,
            (_signal("test.a", second_id),),
            log,
        )

        signals = SignalEngine((first, silent, second)).evaluate(_analytics())

        self.assertEqual(
            log,
            ["test.first_rule", "test.silent_rule", "test.second_rule"],
        )
        self.assertEqual(
            [signal.signal_type.root for signal in signals],
            ["test.a", "test.b", "test.a"],
        )
        self.assertIsInstance(signals, tuple)

    def test_each_rule_receives_the_same_analytics_instance(self) -> None:
        log: list[str] = []
        first = RecordingRule("test.first", (), log)
        second = RecordingRule("test.second", (), log)
        analytics = _analytics()

        SignalEngine((first, second)).evaluate(analytics)

        self.assertIs(first.received_analytics[0], analytics)
        self.assertIs(second.received_analytics[0], analytics)

    def test_constructor_snapshots_the_caller_owned_sequence(self) -> None:
        log: list[str] = []
        rules = [RecordingRule("test.first", (), log)]
        engine = SignalEngine(rules)
        rules.append(RecordingRule("test.second", (), log))

        engine.evaluate(_analytics())

        self.assertEqual(log, ["test.first"])

    def test_duplicate_rule_identity_is_rejected_before_execution(self) -> None:
        log: list[str] = []

        with self.assertRaisesRegex(
            DuplicateSignalRuleError,
            "duplicate signal rule registered: 'test.rule'",
        ):
            SignalEngine(
                (
                    RecordingRule("test.rule", (), log),
                    RecordingRule("test.rule", (), log),
                )
            )

        self.assertEqual(log, [])

    def test_rule_failure_propagates_unchanged_and_stops_execution(self) -> None:
        log: list[str] = []
        error = RuntimeError("rule failed")
        engine = SignalEngine(
            (
                RecordingRule("test.first", (), log),
                FailingRule("test.failing", error, log),
                RecordingRule("test.last", (), log),
            )
        )

        with self.assertRaises(RuntimeError) as raised:
            engine.evaluate(_analytics())

        self.assertIs(raised.exception, error)
        self.assertEqual(log, ["test.first", "test.failing"])

    def test_non_tuple_rule_output_is_rejected(self) -> None:
        rule_id = RuleId("test.rule")
        engine = SignalEngine(
            (
                cast(
                    SignalRule,
                    ListReturningRule(
                        rule_id.root,
                        (_signal("test.signal", rule_id),),
                        [],
                    ),
                ),
            )
        )

        with self.assertRaisesRegex(
            InvalidSignalRuleOutputError,
            "signal rule 'test.rule' must return a tuple",
        ):
            engine.evaluate(_analytics())

    def test_mismatched_signal_provenance_is_rejected(self) -> None:
        emitted_rule_id = RuleId("test.other_rule")
        engine = SignalEngine(
            (
                RecordingRule(
                    "test.rule",
                    (_signal("test.signal", emitted_rule_id),),
                    [],
                ),
            )
        )

        with self.assertRaisesRegex(
            InvalidSignalRuleOutputError,
            "signal rule 'test.rule' returned mismatched provenance",
        ):
            engine.evaluate(_analytics())

    def test_non_signal_rule_output_is_rejected(self) -> None:
        engine = SignalEngine(
            (cast(SignalRule, NonSignalReturningRule("test.rule", (), [])),)
        )

        with self.assertRaisesRegex(
            InvalidSignalRuleOutputError,
            "signal rule 'test.rule' returned a non-Signal value",
        ):
            engine.evaluate(_analytics())

    def test_engine_is_stateless_and_deterministic_across_executions(self) -> None:
        log: list[str] = []
        rule_id = RuleId("test.rule")
        engine = SignalEngine(
            (RecordingRule("test.rule", (_signal("test.signal", rule_id),), log),)
        )
        analytics = _analytics()

        first = engine.evaluate(analytics)
        second = engine.evaluate(analytics)

        self.assertEqual(first, second)
        self.assertEqual(log, ["test.rule", "test.rule"])


if __name__ == "__main__":
    unittest.main()
