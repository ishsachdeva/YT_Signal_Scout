"""Tests for deterministic counts-only evaluation aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.services.backtesting import (
    EvaluationAggregationCanonicalizer,
    EvaluationAggregationConfiguration,
    EvaluationAggregationDefinition,
    EvaluationAggregationDigestMismatchError,
    EvaluationAggregationRequest,
    EvaluationAggregationService,
    EvaluationAggregationSummary,
    EvaluationAggregationValidationError,
    EvaluationCanonicalizer,
    EvaluationOutcome,
    LabelContentDigest,
    LabelledEvaluationService,
)
from tests.test_labelled_evaluation import _request as _evaluation_request


def _source_result():
    return LabelledEvaluationService().evaluate(_evaluation_request())


def _request(source=None) -> EvaluationAggregationRequest:
    evaluation = source or _source_result()
    configuration = EvaluationAggregationConfiguration(
        configuration_id="evaluation-aggregation-configuration-v1",
        version=1,
        evaluation_id=evaluation.metadata.evaluation_id,
        evaluation_version=evaluation.metadata.evaluation_version,
        evaluation_schema_version=evaluation.manifest.schema_version,
        expected_observation_count=len(evaluation.observations),
    )
    definition = EvaluationAggregationDefinition(
        aggregation_id="evaluation-aggregation-v1",
        version=1,
        title="Counts-only labelled evaluation aggregation",
        objective="Count immutable observation outcomes without derived metrics.",
        configuration_id=configuration.configuration_id,
        configuration_version=configuration.version,
        created_at=datetime(2026, 7, 24, 16, tzinfo=UTC),
    )
    return EvaluationAggregationRequest(
        aggregated_at=datetime(2026, 7, 24, 17, tzinfo=UTC),
        definition=definition,
        configuration=configuration,
        evaluation_result=evaluation,
    )


def _all_outcomes_result():
    source = _source_result()
    template = source.observations[0]
    outcomes = tuple(EvaluationOutcome)
    observations = tuple(
        template.model_copy(
            update={
                "observation_id": f"observation-{index}",
                "channel_id": f"channel-{index}",
                "prediction_id": f"prediction-{index}",
                "outcome": outcome,
            }
        )
        for index, outcome in enumerate(outcomes, start=1)
    )
    digest = EvaluationCanonicalizer.calculate_result_digest(
        source.metadata, observations, source.manifest
    )
    return source.model_copy(
        update={
            "observations": observations,
            "manifest": source.manifest.model_copy(
                update={
                    "result_digest": LabelContentDigest(
                        algorithm="sha256", value=digest
                    )
                }
            ),
        }
    )


def test_aggregation_counts_every_outcome_without_metrics() -> None:
    request = _request(_all_outcomes_result())
    service = EvaluationAggregationService()

    first = service.aggregate(request)
    second = service.aggregate(request)

    assert first == second
    assert first.summary == EvaluationAggregationSummary(
        true_positive_count=1,
        true_negative_count=1,
        false_positive_count=1,
        false_negative_count=1,
        unknown_count=1,
        not_evaluated_count=1,
        total_evaluated=5,
        total_observations=6,
    )
    assert not hasattr(first.summary, "precision")
    assert not hasattr(first.summary, "percentage")
    assert EvaluationAggregationCanonicalizer.serialize_result(first) == (
        EvaluationAggregationCanonicalizer.serialize_result(second)
    )
    with pytest.raises(ValidationError):
        first.summary.total_observations = 7


def test_summary_invariants_reject_inconsistent_totals() -> None:
    values = EvaluationAggregationService().aggregate(_request()).summary.model_dump()
    values["total_evaluated"] += 1
    with pytest.raises(ValidationError, match="total evaluated"):
        EvaluationAggregationSummary.model_validate(values)


def test_observation_count_and_duplicate_outcomes_are_rejected() -> None:
    request = _request()
    configuration = request.configuration.model_copy(
        update={"expected_observation_count": 2}
    )
    mismatch = request.model_copy(update={"configuration": configuration})
    with pytest.raises(EvaluationAggregationValidationError, match="count mismatch"):
        EvaluationAggregationService().aggregate(mismatch)

    source = request.evaluation_result
    duplicate = source.model_copy(
        update={"observations": (source.observations[0], source.observations[0])}
    )
    configuration = request.configuration.model_copy(
        update={"expected_observation_count": 2}
    )
    duplicate_request = request.model_copy(
        update={"configuration": configuration, "evaluation_result": duplicate}
    )
    with pytest.raises(EvaluationAggregationValidationError, match="duplicate observation"):
        EvaluationAggregationService().aggregate(duplicate_request)


def test_unknown_fields_identity_reuse_and_source_digest_tampering_are_rejected() -> None:
    request = _request()
    values = request.model_dump(mode="python")
    values["accuracy"] = 1.0
    with pytest.raises(ValidationError):
        EvaluationAggregationRequest.model_validate(values)

    definition = request.definition.model_copy(
        update={"aggregation_id": request.configuration.configuration_id}
    )
    duplicate = request.model_copy(update={"definition": definition})
    with pytest.raises(EvaluationAggregationValidationError, match="identities must be unique"):
        EvaluationAggregationService().aggregate(duplicate)

    source = request.evaluation_result
    altered = source.model_copy(
        update={
            "observations": (
                source.observations[0].model_copy(
                    update={"outcome": EvaluationOutcome.FALSE_POSITIVE}
                ),
            )
        }
    )
    tampered = request.model_copy(update={"evaluation_result": altered})
    with pytest.raises(EvaluationAggregationValidationError, match="digest"):
        EvaluationAggregationService().aggregate(tampered)

    forged_observation = source.observations[0].model_copy(
        update={"outcome": "unsupported"}
    )
    forged = source.model_copy(update={"observations": (forged_observation,)})
    forged_request = request.model_copy(update={"evaluation_result": forged})
    with pytest.raises(EvaluationAggregationValidationError, match="unknown evaluation outcome"):
        EvaluationAggregationService().aggregate(forged_request)


def test_aggregation_result_digest_detects_changed_counts() -> None:
    result = EvaluationAggregationService().aggregate(_request())
    summary = result.summary.model_copy(
        update={
            "true_positive_count": 0,
            "unknown_count": 1,
        }
    )
    altered = result.model_copy(update={"summary": summary})
    with pytest.raises(EvaluationAggregationDigestMismatchError):
        EvaluationAggregationCanonicalizer.serialize_result(altered)
