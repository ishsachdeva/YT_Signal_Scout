from __future__ import annotations

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from app.services.analytics.models import MetricType
from app.services.signals.models import (
    ReasonCode,
    RuleId,
    Signal,
    SignalEvidence,
    SignalPolarity,
    SignalType,
)


def _evidence() -> SignalEvidence:
    return SignalEvidence(
        metric=MetricType.AVERAGE_VIEWS,
        observed_value=1250.5,
        source_channel_id="channel-1",
        source_generated_at=datetime(2026, 7, 22, tzinfo=UTC),
    )


def _signal() -> Signal:
    return Signal(
        signal_type=SignalType("test.performance_observation"),
        polarity=SignalPolarity.POSITIVE,
        reason_code=ReasonCode("test.average_views_observed"),
        rule_id=RuleId("test.average_views_rule"),
        rule_version=1,
        evidence=(_evidence(),),
    )


class SignalEvidenceTests(unittest.TestCase):
    def test_evidence_retains_numeric_type_and_metric_identity(self) -> None:
        evidence = _evidence()

        self.assertIs(evidence.metric, MetricType.AVERAGE_VIEWS)
        self.assertIsInstance(evidence.observed_value, float)
        self.assertEqual(evidence.observed_value, 1250.5)

    def test_optional_metric_value_is_preserved(self) -> None:
        evidence = SignalEvidence(
            metric=MetricType.VIEW_ENGAGEMENT_RATE,
            observed_value=None,
            source_channel_id="channel-1",
            source_generated_at=datetime(2026, 7, 22, tzinfo=UTC),
        )

        self.assertIsNone(evidence.observed_value)

    def test_boolean_is_not_silently_accepted_as_numeric_evidence(self) -> None:
        with self.assertRaises(ValidationError):
            SignalEvidence(
                metric=MetricType.AVERAGE_VIEWS,
                observed_value=True,  # type: ignore[arg-type]
                source_channel_id="channel-1",
                source_generated_at=datetime(2026, 7, 22, tzinfo=UTC),
            )

    def test_evidence_is_immutable(self) -> None:
        evidence = _evidence()

        with self.assertRaises(ValidationError):
            evidence.observed_value = 2.0

    def test_invalid_metric_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SignalEvidence(
                metric="arbitrary",  # type: ignore[arg-type]
                observed_value=1,
                source_channel_id="channel-1",
                source_generated_at=datetime(2026, 7, 22, tzinfo=UTC),
            )


class SignalModelTests(unittest.TestCase):
    def test_valid_signal_preserves_typed_semantics_and_evidence(self) -> None:
        signal = _signal()

        self.assertEqual(signal.signal_type, SignalType("test.performance_observation"))
        self.assertIs(signal.polarity, SignalPolarity.POSITIVE)
        self.assertEqual(signal.evidence, (_evidence(),))

    def test_equal_values_produce_equal_signals(self) -> None:
        self.assertEqual(_signal(), _signal())

    def test_signal_and_nested_collection_are_immutable(self) -> None:
        signal = _signal()

        with self.assertRaises(ValidationError):
            signal.rule_version = 2
        self.assertIsInstance(signal.evidence, tuple)

    def test_mutable_evidence_input_is_snapshotted_as_tuple(self) -> None:
        evidence = [_evidence()]
        values = _signal().model_dump()
        values["evidence"] = evidence
        signal = Signal.model_validate(values)

        evidence.append(_evidence())

        self.assertEqual(len(signal.evidence), 1)

    def test_invalid_identity_and_version_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SignalType("Human readable identity")
        with self.assertRaises(ValidationError):
            Signal.model_validate(_signal().model_dump() | {"rule_version": 0})

    def test_invalid_enum_value_is_rejected(self) -> None:
        values = _signal().model_dump()
        values["polarity"] = "favorable"

        with self.assertRaises(ValidationError):
            Signal.model_validate(values)

    def test_signal_requires_supporting_evidence(self) -> None:
        values = _signal().model_dump()
        values["evidence"] = ()

        with self.assertRaises(ValidationError):
            Signal.model_validate(values)


if __name__ == "__main__":
    unittest.main()
