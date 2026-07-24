"""Pure deterministic counting of immutable observation outcomes."""

from __future__ import annotations

from collections import Counter

from app.services.backtesting.evaluation_aggregation_canonicalizer import (
    EvaluationAggregationCanonicalizer,
)
from app.services.backtesting.evaluation_aggregation_models import (
    EVALUATION_AGGREGATION_SCHEMA_VERSION,
    EvaluationAggregationManifest,
    EvaluationAggregationMetadata,
    EvaluationAggregationRequest,
    EvaluationAggregationResult,
    EvaluationAggregationSummary,
)
from app.services.backtesting.exceptions import (
    EvaluationAggregationDigestMismatchError,
    EvaluationAggregationValidationError,
    EvaluationDigestMismatchError,
)
from app.services.backtesting.label_models import LabelContentDigest
from app.services.backtesting.labelled_evaluation_canonicalizer import (
    EvaluationCanonicalizer,
)
from app.services.backtesting.labelled_evaluation_models import EvaluationOutcome


class EvaluationAggregationValidator:
    """Reject mismatched, incomplete, duplicated, unordered, or corrupt input."""

    def validate(self, request: EvaluationAggregationRequest) -> None:
        if not isinstance(request, EvaluationAggregationRequest):
            self._fail("typed evaluation aggregation request is required")
        definition = request.definition
        configuration = request.configuration
        evaluation = request.evaluation_result

        if (definition.configuration_id, definition.configuration_version) != (
            configuration.configuration_id,
            configuration.version,
        ):
            self._fail("aggregation definition configuration mismatch")
        if (configuration.evaluation_id, configuration.evaluation_version) != (
            evaluation.metadata.evaluation_id,
            evaluation.metadata.evaluation_version,
        ):
            self._fail("aggregation evaluation-result mismatch")
        if configuration.evaluation_schema_version != evaluation.manifest.schema_version:
            self._fail("aggregation evaluation schema-version mismatch")

        observations = evaluation.observations
        if len(observations) != configuration.expected_observation_count:
            self._fail("aggregation observation-count mismatch")
        if any(not isinstance(item.outcome, EvaluationOutcome) for item in observations):
            self._fail("unknown evaluation outcome vocabulary")
        observation_ids = tuple(item.observation_id for item in observations)
        if len(set(observation_ids)) != len(observation_ids):
            self._fail("duplicate observation outcome")
        if observation_ids != tuple(sorted(observation_ids)):
            self._fail("evaluation observations must be canonically ordered")

        identities = (
            definition.aggregation_id,
            configuration.configuration_id,
            evaluation.metadata.evaluation_id,
        )
        if len(set(identities)) != len(identities):
            self._fail("aggregation identities must be unique")
        try:
            EvaluationCanonicalizer.validate_result_digest(evaluation)
        except EvaluationDigestMismatchError as exc:
            raise EvaluationAggregationDigestMismatchError((str(exc),)) from exc

    @staticmethod
    def _fail(issue: str) -> None:
        raise EvaluationAggregationValidationError((issue,))


class EvaluationAggregationService:
    """Count outcome categories once without deriving any metric."""

    def __init__(
        self, validator: EvaluationAggregationValidator | None = None
    ) -> None:
        self._validator = validator or EvaluationAggregationValidator()

    def aggregate(
        self, request: EvaluationAggregationRequest
    ) -> EvaluationAggregationResult:
        self._validator.validate(request)
        counts = Counter(item.outcome for item in request.evaluation_result.observations)
        summary = EvaluationAggregationSummary(
            true_positive_count=counts[EvaluationOutcome.TRUE_POSITIVE],
            true_negative_count=counts[EvaluationOutcome.TRUE_NEGATIVE],
            false_positive_count=counts[EvaluationOutcome.FALSE_POSITIVE],
            false_negative_count=counts[EvaluationOutcome.FALSE_NEGATIVE],
            unknown_count=counts[EvaluationOutcome.UNKNOWN],
            not_evaluated_count=counts[EvaluationOutcome.NOT_EVALUATED],
            total_evaluated=sum(
                count
                for outcome, count in counts.items()
                if outcome is not EvaluationOutcome.NOT_EVALUATED
            ),
            total_observations=len(request.evaluation_result.observations),
        )
        definition = request.definition
        configuration = request.configuration
        metadata = EvaluationAggregationMetadata(
            aggregation_id=definition.aggregation_id,
            aggregation_version=definition.version,
            aggregated_at=request.aggregated_at,
            configuration_id=configuration.configuration_id,
            configuration_version=configuration.version,
            evaluation_id=configuration.evaluation_id,
            evaluation_version=configuration.evaluation_version,
        )
        provisional_manifest = EvaluationAggregationManifest(
            schema_version=EVALUATION_AGGREGATION_SCHEMA_VERSION,
            evaluation_result_digest=request.evaluation_result.manifest.result_digest,
            result_digest=LabelContentDigest(algorithm="sha256", value="0" * 64),
        )
        digest = EvaluationAggregationCanonicalizer.calculate_result_digest(
            metadata, summary, provisional_manifest
        )
        return EvaluationAggregationResult(
            metadata=metadata,
            summary=summary,
            manifest=provisional_manifest.model_copy(
                update={
                    "result_digest": LabelContentDigest(
                        algorithm="sha256", value=digest
                    )
                }
            ),
        )
