"""Tests for governed deterministic statistical evaluation."""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.services.backtesting import (
    EvaluationAggregationCanonicalizer,
    EvaluationAggregationService,
    EvaluationAggregationSummary,
    LabelContentDigest,
    StatisticalEvaluationCanonicalizer,
    StatisticalEvaluationConfiguration,
    StatisticalEvaluationDefinition,
    StatisticalEvaluationDigestMismatchError,
    StatisticalEvaluationRequest,
    StatisticalEvaluationService,
    StatisticalEvaluationValidationError,
)
from tests.test_evaluation_aggregation import _request as _aggregation_request


def _aggregation_result(
    *, tp: int = 50, tn: int = 40, fp: int = 10, fn: int = 5
):
    source = EvaluationAggregationService().aggregate(_aggregation_request())
    unknown = 3
    not_evaluated = 2
    binary = tp + tn + fp + fn
    summary = EvaluationAggregationSummary(
        true_positive_count=tp,
        true_negative_count=tn,
        false_positive_count=fp,
        false_negative_count=fn,
        unknown_count=unknown,
        not_evaluated_count=not_evaluated,
        total_evaluated=binary + unknown,
        total_observations=binary + unknown + not_evaluated,
    )
    digest = EvaluationAggregationCanonicalizer.calculate_result_digest(
        source.metadata, summary, source.manifest
    )
    return source.model_copy(
        update={
            "summary": summary,
            "manifest": source.manifest.model_copy(
                update={
                    "result_digest": LabelContentDigest(
                        algorithm="sha256", value=digest
                    )
                }
            ),
        }
    )


def _request(aggregation=None) -> StatisticalEvaluationRequest:
    source = aggregation or _aggregation_result()
    configuration = StatisticalEvaluationConfiguration(
        configuration_id="statistical-configuration-v1",
        version=1,
        aggregation_id=source.metadata.aggregation_id,
        aggregation_version=source.metadata.aggregation_version,
        aggregation_schema_version=source.manifest.schema_version,
        confidence_level="0.95",
        wilson_z="1.959963984540054",
    )
    definition = StatisticalEvaluationDefinition(
        statistical_evaluation_id="statistical-evaluation-v1",
        version=1,
        title="Governed statistical evaluation",
        objective="Calculate approved mathematical statistics without interpretation.",
        configuration_id=configuration.configuration_id,
        configuration_version=configuration.version,
        created_at=datetime(2026, 7, 24, 18, tzinfo=UTC),
    )
    return StatisticalEvaluationRequest(
        evaluated_at=datetime(2026, 7, 24, 19, tzinfo=UTC),
        definition=definition,
        configuration=configuration,
        aggregation_result=source,
    )


def _wilson(estimate: float, sample_size: int) -> tuple[float, float]:
    z = 1.959963984540054
    denominator = 1 + z * z / sample_size
    center = (estimate + z * z / (2 * sample_size)) / denominator
    half_width = z * math.sqrt(
        (estimate * (1 - estimate) + z * z / (4 * sample_size)) / sample_size
    ) / denominator
    return max(0, center - half_width), min(1, center + half_width)


def test_required_metrics_are_mathematically_correct_and_deterministic() -> None:
    request = _request()
    service = StatisticalEvaluationService()
    first = service.evaluate(request)
    second = service.evaluate(request)
    summary = first.summary

    assert first == second
    assert summary.accuracy == pytest.approx(90 / 105)
    assert summary.precision == pytest.approx(50 / 60)
    assert summary.recall == pytest.approx(50 / 55)
    assert summary.sensitivity == summary.recall
    assert summary.specificity == pytest.approx(40 / 50)
    assert summary.negative_predictive_value == pytest.approx(40 / 45)
    assert summary.false_positive_rate == pytest.approx(10 / 50)
    assert summary.false_negative_rate == pytest.approx(5 / 55)
    assert summary.balanced_accuracy == pytest.approx(((50 / 55) + (40 / 50)) / 2)
    assert summary.f1_score == pytest.approx(100 / 115)
    assert summary.matthews_correlation_coefficient == pytest.approx(
        (50 * 40 - 10 * 5) / math.sqrt(60 * 55 * 50 * 45)
    )
    assert not hasattr(summary, "recommendation")
    assert not hasattr(summary, "threshold")
    assert StatisticalEvaluationCanonicalizer.serialize_result(first) == (
        StatisticalEvaluationCanonicalizer.serialize_result(second)
    )
    with pytest.raises(ValidationError):
        summary.accuracy = 0.5


def test_wilson_intervals_use_configured_formula_and_denominators() -> None:
    summary = StatisticalEvaluationService().evaluate(_request()).summary
    cases = (
        (summary.accuracy_interval, summary.accuracy, 105),
        (summary.precision_interval, summary.precision, 60),
        (summary.recall_interval, summary.recall, 55),
        (summary.specificity_interval, summary.specificity, 50),
        (summary.balanced_accuracy_interval, summary.balanced_accuracy, 105),
    )
    for interval, estimate, sample_size in cases:
        lower, upper = _wilson(estimate, sample_size)
        assert interval.sample_size == sample_size
        assert interval.lower_bound == pytest.approx(lower)
        assert interval.upper_bound == pytest.approx(upper)


def test_undefined_domains_fail_instead_of_returning_partial_metrics() -> None:
    aggregation = _aggregation_result(tp=0, tn=0, fp=0, fn=0)
    with pytest.raises(StatisticalEvaluationValidationError, match="undefined"):
        StatisticalEvaluationService().evaluate(_request(aggregation))


def test_identity_version_unknown_fields_and_invalid_counts_are_rejected() -> None:
    request = _request()
    values = request.model_dump(mode="python")
    values["ranking"] = 1
    with pytest.raises(ValidationError):
        StatisticalEvaluationRequest.model_validate(values)

    configuration = request.configuration.model_copy(
        update={"aggregation_version": request.configuration.aggregation_version + 1}
    )
    mismatch = request.model_copy(update={"configuration": configuration})
    with pytest.raises(StatisticalEvaluationValidationError, match="identity mismatch"):
        StatisticalEvaluationService().evaluate(mismatch)

    definition = request.definition.model_copy(
        update={"statistical_evaluation_id": request.configuration.configuration_id}
    )
    duplicate = request.model_copy(update={"definition": definition})
    with pytest.raises(StatisticalEvaluationValidationError, match="identities must be unique"):
        StatisticalEvaluationService().evaluate(duplicate)

    forged_summary = request.aggregation_result.summary.model_copy(
        update={"true_positive_count": -1}
    )
    forged = request.aggregation_result.model_copy(update={"summary": forged_summary})
    with pytest.raises(StatisticalEvaluationValidationError, match="non-negative integers"):
        StatisticalEvaluationService().evaluate(
            request.model_copy(update={"aggregation_result": forged})
        )


def test_source_and_result_digest_tampering_are_rejected() -> None:
    request = _request()
    source = request.aggregation_result
    altered_summary = source.summary.model_copy(update={"unknown_count": 4})
    altered_source = source.model_copy(update={"summary": altered_summary})
    with pytest.raises(StatisticalEvaluationValidationError, match="total mismatch|digest"):
        StatisticalEvaluationService().evaluate(
            request.model_copy(update={"aggregation_result": altered_source})
        )

    result = StatisticalEvaluationService().evaluate(request)
    altered_result = result.model_copy(
        update={
            "summary": result.summary.model_copy(update={"accuracy": 0.5})
        }
    )
    with pytest.raises(StatisticalEvaluationDigestMismatchError):
        StatisticalEvaluationCanonicalizer.serialize_result(altered_result)


def test_structurally_valid_stale_source_digest_and_naive_time_are_rejected() -> None:
    request = _request()
    source = request.aggregation_result
    summary = source.summary.model_copy(
        update={
            "true_positive_count": source.summary.true_positive_count + 1,
            "total_evaluated": source.summary.total_evaluated + 1,
            "total_observations": source.summary.total_observations + 1,
        }
    )
    stale = source.model_copy(update={"summary": summary})
    with pytest.raises(StatisticalEvaluationValidationError, match="digest"):
        StatisticalEvaluationService().evaluate(
            request.model_copy(update={"aggregation_result": stale})
        )

    values = request.model_dump(mode="python")
    values["evaluated_at"] = datetime(2026, 7, 24, 19)
    with pytest.raises(ValidationError, match="timezone-aware"):
        StatisticalEvaluationRequest.model_validate(values)
