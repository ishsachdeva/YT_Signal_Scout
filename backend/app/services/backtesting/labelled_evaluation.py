"""Pure observation-level comparison of predictions with governed truth."""

from __future__ import annotations

from app.services.backtesting.exceptions import (
    EvaluationDigestMismatchError,
    EvaluationValidationError,
    GroundTruthLabelDigestMismatchError,
    HistoricalDatasetDigestMismatchError,
    StudyExecutionDigestMismatchError,
)
from app.services.backtesting.importer import HistoricalDatasetCanonicalizer
from app.services.backtesting.label_importer import GroundTruthLabelCanonicalizer
from app.services.backtesting.label_models import GroundTruthLabel, LabelContentDigest
from app.services.backtesting.labelled_evaluation_canonicalizer import (
    EvaluationCanonicalizer,
)
from app.services.backtesting.labelled_evaluation_models import (
    LABELLED_EVALUATION_SCHEMA_VERSION,
    EvaluationManifest,
    EvaluationMetadata,
    EvaluationOutcome,
    EvaluationRequest,
    EvaluationResult,
    ObservationEvaluation,
    PredictedOutcome,
)
from app.services.backtesting.study_execution_canonicalizer import (
    StudyExecutionCanonicalizer,
)


class EvaluationValidator:
    """Validate exact cohort, governed bindings, ordering, versions, and integrity."""

    def validate(self, request: EvaluationRequest) -> None:
        if not isinstance(request, EvaluationRequest):
            self._fail("typed evaluation request is required")

        definition = request.definition
        configuration = request.configuration
        execution = request.study_execution
        dataset = request.dataset
        labels = request.ground_truth_labels

        if (definition.configuration_id, definition.configuration_version) != (
            configuration.configuration_id,
            configuration.version,
        ):
            self._fail("evaluation definition configuration mismatch")

        configured = (
            configuration.study_execution_id,
            configuration.dataset_id,
            configuration.dataset_version,
            configuration.label_set_id,
            configuration.label_set_version,
        )
        supplied = (
            execution.metadata.execution_id,
            dataset.dataset.dataset_id,
            dataset.dataset.version,
            labels.label_set.label_set_id,
            labels.label_set.version,
        )
        if configured != supplied:
            self._fail("evaluation configuration governed-input mismatch")
        if (labels.label_set.dataset_id, labels.label_set.dataset_version) != (
            dataset.dataset.dataset_id,
            dataset.dataset.version,
        ):
            self._fail("ground-truth dataset mismatch")
        if (execution.context.dataset_id, execution.context.dataset_version) != (
            dataset.dataset.dataset_id,
            dataset.dataset.version,
        ):
            self._fail("study execution dataset mismatch")
        if (execution.context.label_set_id, execution.context.label_set_version) != (
            labels.label_set.label_set_id,
            labels.label_set.version,
        ):
            self._fail("study execution ground-truth mismatch")
        if execution.manifest.dataset_digest.value != dataset.manifest.digest.value:
            self._fail("study execution dataset digest mismatch")
        if (
            execution.manifest.ground_truth_label_digest.value
            != labels.manifest.digest.value
        ):
            self._fail("study execution ground-truth digest mismatch")

        observations = dataset.dataset.observations
        observation_ids = tuple(item.observation_id for item in observations)
        if len(set(observation_ids)) != len(observation_ids):
            self._fail("duplicate dataset observation identity")
        if observation_ids != tuple(sorted(observation_ids)):
            self._fail("dataset observations must be canonically ordered")

        predictions = request.predictions
        prediction_ids = tuple(item.prediction_id for item in predictions)
        predicted_observation_ids = tuple(item.observation_id for item in predictions)
        if len(set(prediction_ids)) != len(prediction_ids):
            self._fail("duplicate prediction identity")
        if len(set(predicted_observation_ids)) != len(predicted_observation_ids):
            self._fail("duplicate predicted observation identity")
        if predicted_observation_ids != observation_ids:
            self._fail("predictions must match dataset observations in canonical order")

        artifacts = labels.label_set.artifacts
        if (
            execution.context.observation_count != len(observations)
            or execution.context.label_count != len(artifacts)
        ):
            self._fail("study execution cohort count mismatch")
        labelled_observation_ids = tuple(item.observation_id for item in artifacts)
        if labelled_observation_ids != observation_ids:
            self._fail("ground-truth labels must match dataset observations in canonical order")

        identities = (
            definition.evaluation_id,
            configuration.configuration_id,
            execution.metadata.execution_id,
        )
        if len(set(identities)) != len(identities):
            self._fail("evaluation identities must be unique")

        for observation, prediction, artifact in zip(
            observations, predictions, artifacts, strict=True
        ):
            expected = (observation.observation_id, observation.channel_id)
            if (prediction.observation_id, prediction.channel_id) != expected:
                self._fail("prediction observation mismatch")
            if (artifact.observation_id, artifact.channel_id) != expected:
                self._fail("ground-truth observation mismatch")

        try:
            HistoricalDatasetCanonicalizer.validate_digest(
                dataset.manifest, dataset.dataset.observations
            )
            GroundTruthLabelCanonicalizer.validate_digest(
                labels.manifest, labels.label_set.artifacts
            )
            StudyExecutionCanonicalizer.validate_result_digest(execution)
        except (
            HistoricalDatasetDigestMismatchError,
            GroundTruthLabelDigestMismatchError,
            StudyExecutionDigestMismatchError,
        ) as exc:
            raise EvaluationDigestMismatchError((str(exc),)) from exc

    @staticmethod
    def _fail(issue: str) -> None:
        raise EvaluationValidationError((issue,))


class LabelledEvaluationService:
    """Compare each supplied prediction with truth without aggregation."""

    def __init__(self, validator: EvaluationValidator | None = None) -> None:
        self._validator = validator or EvaluationValidator()

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        self._validator.validate(request)
        artifacts = request.ground_truth_labels.label_set.artifacts
        observations = tuple(
            ObservationEvaluation(
                observation_id=prediction.observation_id,
                channel_id=prediction.channel_id,
                prediction_id=prediction.prediction_id,
                predicted_outcome=prediction.predicted_outcome,
                ground_truth_label=artifact.final_label,
                outcome=self._outcome(prediction.predicted_outcome, artifact.final_label),
            )
            for prediction, artifact in zip(request.predictions, artifacts, strict=True)
        )
        configuration = request.configuration
        metadata = EvaluationMetadata(
            evaluation_id=request.definition.evaluation_id,
            evaluation_version=request.definition.version,
            evaluated_at=request.evaluated_at,
            configuration_id=configuration.configuration_id,
            configuration_version=configuration.version,
            study_execution_id=configuration.study_execution_id,
            dataset_id=configuration.dataset_id,
            dataset_version=configuration.dataset_version,
            label_set_id=configuration.label_set_id,
            label_set_version=configuration.label_set_version,
        )
        provisional_manifest = EvaluationManifest(
            schema_version=LABELLED_EVALUATION_SCHEMA_VERSION,
            study_execution_digest=request.study_execution.manifest.result_digest,
            dataset_digest=LabelContentDigest(
                algorithm="sha256", value=request.dataset.manifest.digest.value
            ),
            ground_truth_label_digest=request.ground_truth_labels.manifest.digest,
            predictions_digest=LabelContentDigest(
                algorithm="sha256",
                value=EvaluationCanonicalizer.calculate_predictions_digest(
                    request.predictions
                ),
            ),
            result_digest=LabelContentDigest(algorithm="sha256", value="0" * 64),
        )
        digest = EvaluationCanonicalizer.calculate_result_digest(
            metadata, observations, provisional_manifest
        )
        return EvaluationResult(
            metadata=metadata,
            observations=observations,
            manifest=provisional_manifest.model_copy(
                update={
                    "result_digest": LabelContentDigest(
                        algorithm="sha256", value=digest
                    )
                }
            ),
        )

    @staticmethod
    def _outcome(
        prediction: PredictedOutcome, truth: GroundTruthLabel
    ) -> EvaluationOutcome:
        if prediction is PredictedOutcome.NOT_EVALUATED:
            return EvaluationOutcome.NOT_EVALUATED
        if prediction is PredictedOutcome.UNKNOWN or truth in (
            GroundTruthLabel.BORDERLINE,
            GroundTruthLabel.UNKNOWN,
        ):
            return EvaluationOutcome.UNKNOWN
        mapping = {
            (PredictedOutcome.POSITIVE, GroundTruthLabel.POSITIVE): EvaluationOutcome.TRUE_POSITIVE,
            (PredictedOutcome.NEGATIVE, GroundTruthLabel.NEGATIVE): EvaluationOutcome.TRUE_NEGATIVE,
            (PredictedOutcome.POSITIVE, GroundTruthLabel.NEGATIVE): EvaluationOutcome.FALSE_POSITIVE,
            (PredictedOutcome.NEGATIVE, GroundTruthLabel.POSITIVE): EvaluationOutcome.FALSE_NEGATIVE,
        }
        return mapping[(prediction, truth)]
