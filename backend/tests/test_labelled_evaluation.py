"""Tests for deterministic non-aggregating labelled evaluation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.services.backtesting import (
    EvaluationCanonicalizer,
    EvaluationConfiguration,
    EvaluationDefinition,
    EvaluationOutcome,
    EvaluationRequest,
    EvaluationValidationError,
    EvaluationDigestMismatchError,
    GroundTruthLabel,
    LabelledEvaluationService,
    ObservationPrediction,
    PredictedOutcome,
    StudyExecutionService,
)
from tests.test_governed_study_execution import _request as _study_request


def _request(
    predicted_outcome: PredictedOutcome = PredictedOutcome.POSITIVE,
) -> EvaluationRequest:
    study_request = _study_request()
    execution = StudyExecutionService().execute(study_request)
    configuration = EvaluationConfiguration(
        configuration_id="labelled-evaluation-configuration-v1",
        version=1,
        study_execution_id=execution.metadata.execution_id,
        dataset_id=study_request.inputs.dataset.dataset.dataset_id,
        dataset_version=study_request.inputs.dataset.dataset.version,
        label_set_id=study_request.inputs.ground_truth_labels.label_set.label_set_id,
        label_set_version=study_request.inputs.ground_truth_labels.label_set.version,
        prediction_vocabulary_version=1,
    )
    definition = EvaluationDefinition(
        evaluation_id="labelled-evaluation-v1",
        version=1,
        title="Observation-level labelled evaluation",
        objective="Compare supplied predictions with governed truth without aggregation.",
        configuration_id=configuration.configuration_id,
        configuration_version=configuration.version,
        created_at=datetime(2026, 7, 24, 14, tzinfo=UTC),
    )
    return EvaluationRequest(
        evaluated_at=datetime(2026, 7, 24, 15, tzinfo=UTC),
        definition=definition,
        configuration=configuration,
        study_execution=execution,
        dataset=study_request.inputs.dataset,
        ground_truth_labels=study_request.inputs.ground_truth_labels,
        predictions=(
            ObservationPrediction(
                prediction_id="prediction-1",
                observation_id="observation-1",
                channel_id="channel-1",
                predicted_outcome=predicted_outcome,
            ),
        ),
    )


def test_evaluation_is_immutable_deterministic_and_observation_level_only() -> None:
    request = _request()
    service = LabelledEvaluationService()

    first = service.evaluate(request)
    second = service.evaluate(request)

    assert first == second
    assert first.observations[0].outcome is EvaluationOutcome.TRUE_POSITIVE
    assert not hasattr(first, "totals")
    assert not hasattr(first, "metrics")
    assert EvaluationCanonicalizer.serialize_result(first) == (
        EvaluationCanonicalizer.serialize_result(second)
    )
    with pytest.raises(ValidationError):
        first.observations[0].outcome = EvaluationOutcome.FALSE_POSITIVE


@pytest.mark.parametrize(
    ("prediction", "truth", "expected"),
    (
        (PredictedOutcome.POSITIVE, GroundTruthLabel.POSITIVE, EvaluationOutcome.TRUE_POSITIVE),
        (PredictedOutcome.NEGATIVE, GroundTruthLabel.NEGATIVE, EvaluationOutcome.TRUE_NEGATIVE),
        (PredictedOutcome.POSITIVE, GroundTruthLabel.NEGATIVE, EvaluationOutcome.FALSE_POSITIVE),
        (PredictedOutcome.NEGATIVE, GroundTruthLabel.POSITIVE, EvaluationOutcome.FALSE_NEGATIVE),
        (PredictedOutcome.UNKNOWN, GroundTruthLabel.POSITIVE, EvaluationOutcome.UNKNOWN),
        (PredictedOutcome.POSITIVE, GroundTruthLabel.BORDERLINE, EvaluationOutcome.UNKNOWN),
        (PredictedOutcome.POSITIVE, GroundTruthLabel.UNKNOWN, EvaluationOutcome.UNKNOWN),
        (PredictedOutcome.NOT_EVALUATED, GroundTruthLabel.POSITIVE, EvaluationOutcome.NOT_EVALUATED),
    ),
)
def test_closed_factual_outcome_mapping(
    prediction: PredictedOutcome,
    truth: GroundTruthLabel,
    expected: EvaluationOutcome,
) -> None:
    assert LabelledEvaluationService._outcome(prediction, truth) is expected


def test_unknown_fields_and_prediction_vocabulary_are_rejected() -> None:
    prediction = _request().predictions[0].model_dump(mode="python")
    prediction["predicted_outcome"] = "maybe"
    with pytest.raises(ValidationError):
        ObservationPrediction.model_validate(prediction)

    values = _request().model_dump(mode="python")
    values["precision"] = 1.0
    with pytest.raises(ValidationError):
        EvaluationRequest.model_validate(values)


def test_observation_and_configuration_mismatches_fail_fast() -> None:
    request = _request()
    prediction = request.predictions[0].model_copy(
        update={"observation_id": "unknown-observation"}
    )
    mismatch = request.model_copy(update={"predictions": (prediction,)})
    with pytest.raises(EvaluationValidationError, match="match dataset observations"):
        LabelledEvaluationService().evaluate(mismatch)

    configuration = request.configuration.model_copy(
        update={"dataset_version": request.configuration.dataset_version + 1}
    )
    mismatch = request.model_copy(update={"configuration": configuration})
    with pytest.raises(EvaluationValidationError, match="governed-input mismatch"):
        LabelledEvaluationService().evaluate(mismatch)


def test_duplicate_evaluation_identity_is_rejected() -> None:
    request = _request()
    definition = request.definition.model_copy(
        update={"evaluation_id": request.configuration.configuration_id}
    )
    duplicate = request.model_copy(update={"definition": definition})
    with pytest.raises(EvaluationValidationError, match="identities must be unique"):
        LabelledEvaluationService().evaluate(duplicate)


def test_duplicate_predictions_and_digest_tampering_are_rejected() -> None:
    request = _request()
    duplicate = request.model_copy(
        update={"predictions": (request.predictions[0], request.predictions[0])}
    )
    with pytest.raises(EvaluationValidationError, match="duplicate prediction identity"):
        LabelledEvaluationService().evaluate(duplicate)

    result = LabelledEvaluationService().evaluate(request)
    altered = result.model_copy(
        update={
            "observations": (
                result.observations[0].model_copy(
                    update={"outcome": EvaluationOutcome.FALSE_POSITIVE}
                ),
            )
        }
    )
    with pytest.raises(EvaluationDigestMismatchError):
        EvaluationCanonicalizer.serialize_result(altered)
