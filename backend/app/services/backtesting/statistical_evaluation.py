"""Pure deterministic statistics over one immutable aggregation result."""

from __future__ import annotations

from decimal import Decimal, localcontext

from app.services.backtesting.evaluation_aggregation_canonicalizer import (
    EvaluationAggregationCanonicalizer,
)
from app.services.backtesting.exceptions import StatisticalEvaluationValidationError
from app.services.backtesting.label_models import LabelContentDigest
from app.services.backtesting.statistical_evaluation_canonicalizer import (
    StatisticalEvaluationCanonicalizer,
)
from app.services.backtesting.statistical_evaluation_models import (
    STATISTICAL_EVALUATION_SCHEMA_VERSION,
    StatisticalEvaluationManifest,
    StatisticalEvaluationMetadata,
    StatisticalEvaluationRequest,
    StatisticalEvaluationResult,
    StatisticalEvaluationSummary,
    WilsonScoreInterval,
)


class StatisticalEvaluationValidator:
    """Reject mismatched, corrupt, impossible, or mathematically undefined input."""

    def validate(self, request: StatisticalEvaluationRequest) -> None:
        if not isinstance(request, StatisticalEvaluationRequest):
            self._fail("typed statistical evaluation request is required")
        definition = request.definition
        configuration = request.configuration
        aggregation = request.aggregation_result
        summary = aggregation.summary

        if (definition.configuration_id, definition.configuration_version) != (
            configuration.configuration_id,
            configuration.version,
        ):
            self._fail("statistical definition configuration mismatch")
        if (configuration.aggregation_id, configuration.aggregation_version) != (
            aggregation.metadata.aggregation_id,
            aggregation.metadata.aggregation_version,
        ):
            self._fail("statistical aggregation identity mismatch")
        if configuration.aggregation_schema_version != aggregation.manifest.schema_version:
            self._fail("statistical aggregation schema-version mismatch")

        count_names = (
            "true_positive_count",
            "true_negative_count",
            "false_positive_count",
            "false_negative_count",
            "unknown_count",
            "not_evaluated_count",
            "total_evaluated",
            "total_observations",
        )
        counts = tuple(getattr(summary, name) for name in count_names)
        if any(type(value) is not int or value < 0 for value in counts):
            self._fail("statistical counts must be non-negative integers")
        tp, tn, fp, fn, unknown, not_evaluated, total_evaluated, total = counts
        if total_evaluated != tp + tn + fp + fn + unknown:
            self._fail("statistical evaluated total mismatch")
        if total != total_evaluated + not_evaluated:
            self._fail("statistical observation total mismatch")

        denominators = {
            "accuracy": tp + tn + fp + fn,
            "precision": tp + fp,
            "recall": tp + fn,
            "specificity": tn + fp,
            "negative predictive value": tn + fn,
            "F1": 2 * tp + fp + fn,
        }
        undefined = tuple(name for name, value in denominators.items() if value == 0)
        if undefined:
            self._fail("undefined statistical domains: " + ", ".join(undefined))
        mcc_factors = (tp + fp, tp + fn, tn + fp, tn + fn)
        if any(value == 0 for value in mcc_factors):
            self._fail("undefined statistical domain: MCC")

        identities = (
            definition.statistical_evaluation_id,
            configuration.configuration_id,
            aggregation.metadata.aggregation_id,
        )
        if len(set(identities)) != len(identities):
            self._fail("statistical identities must be unique")
        try:
            EvaluationAggregationCanonicalizer.validate_result_digest(aggregation)
        except Exception as exc:
            raise StatisticalEvaluationValidationError((str(exc),)) from exc

    @staticmethod
    def _fail(issue: str) -> None:
        raise StatisticalEvaluationValidationError((issue,))


class StatisticalEvaluationService:
    """Calculate the approved metric set once without interpretation."""

    def __init__(self, validator: StatisticalEvaluationValidator | None = None) -> None:
        self._validator = validator or StatisticalEvaluationValidator()

    def evaluate(self, request: StatisticalEvaluationRequest) -> StatisticalEvaluationResult:
        self._validator.validate(request)
        counts = request.aggregation_result.summary
        with localcontext() as context:
            context.prec = 50
            tp = Decimal(counts.true_positive_count)
            tn = Decimal(counts.true_negative_count)
            fp = Decimal(counts.false_positive_count)
            fn = Decimal(counts.false_negative_count)
            binary = tp + tn + fp + fn
            accuracy = (tp + tn) / binary
            precision = tp / (tp + fp)
            recall = tp / (tp + fn)
            specificity = tn / (tn + fp)
            negative_predictive_value = tn / (tn + fn)
            false_positive_rate = fp / (fp + tn)
            false_negative_rate = fn / (fn + tp)
            balanced_accuracy = (recall + specificity) / Decimal(2)
            f1_score = (Decimal(2) * tp) / (Decimal(2) * tp + fp + fn)
            mcc = (tp * tn - fp * fn) / (
                (tp + fp).sqrt()
                * (tp + fn).sqrt()
                * (tn + fp).sqrt()
                * (tn + fn).sqrt()
            )

            accuracy_value = float(accuracy)
            precision_value = float(precision)
            recall_value = float(recall)
            specificity_value = float(specificity)
            balanced_accuracy_value = float(balanced_accuracy)
            summary = StatisticalEvaluationSummary(
                accuracy=accuracy_value,
                precision=precision_value,
                recall=recall_value,
                sensitivity=recall_value,
                specificity=specificity_value,
                negative_predictive_value=float(negative_predictive_value),
                false_positive_rate=float(false_positive_rate),
                false_negative_rate=float(false_negative_rate),
                balanced_accuracy=balanced_accuracy_value,
                f1_score=float(f1_score),
                matthews_correlation_coefficient=float(mcc),
                accuracy_interval=self._wilson(accuracy, int(binary), accuracy_value),
                precision_interval=self._wilson(
                    precision, int(tp + fp), precision_value
                ),
                recall_interval=self._wilson(recall, int(tp + fn), recall_value),
                specificity_interval=self._wilson(
                    specificity, int(tn + fp), specificity_value
                ),
                balanced_accuracy_interval=self._wilson(
                    balanced_accuracy, int(binary), balanced_accuracy_value
                ),
            )

        definition = request.definition
        configuration = request.configuration
        metadata = StatisticalEvaluationMetadata(
            statistical_evaluation_id=definition.statistical_evaluation_id,
            statistical_evaluation_version=definition.version,
            evaluated_at=request.evaluated_at,
            configuration_id=configuration.configuration_id,
            configuration_version=configuration.version,
            aggregation_id=configuration.aggregation_id,
            aggregation_version=configuration.aggregation_version,
        )
        provisional_manifest = StatisticalEvaluationManifest(
            schema_version=STATISTICAL_EVALUATION_SCHEMA_VERSION,
            aggregation_result_digest=request.aggregation_result.manifest.result_digest,
            result_digest=LabelContentDigest(algorithm="sha256", value="0" * 64),
        )
        digest = StatisticalEvaluationCanonicalizer.calculate_result_digest(
            metadata, summary, provisional_manifest
        )
        return StatisticalEvaluationResult(
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

    @staticmethod
    def _wilson(
        estimate: Decimal, sample_size: int, estimate_value: float
    ) -> WilsonScoreInterval:
        n = Decimal(sample_size)
        z = Decimal("1.959963984540054")
        z_squared = z * z
        denominator = Decimal(1) + z_squared / n
        center = (estimate + z_squared / (Decimal(2) * n)) / denominator
        half_width = z * (
            (estimate * (Decimal(1) - estimate) + z_squared / (Decimal(4) * n))
            / n
        ).sqrt() / denominator
        lower = max(Decimal(0), center - half_width)
        upper = min(Decimal(1), center + half_width)
        return WilsonScoreInterval(
            estimate=estimate_value,
            lower_bound=float(lower),
            upper_bound=float(upper),
            sample_size=sample_size,
        )

