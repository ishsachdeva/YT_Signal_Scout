"""Deterministic offline median standard-video VSR threshold analysis."""

from __future__ import annotations

from datetime import datetime
from statistics import fmean, median

from app.services.analytics.qualification import QualificationFailureReason
from app.services.backtesting.models import (
    BacktestExclusion,
    BacktestExclusionReason,
    DistributionSummary,
    MedianVsrThresholdCandidate,
    MedianVsrThresholdSet,
    QualificationFailureCount,
    QualificationCoverageSummary,
    SubscriberBandBacktestResult,
    SubscriberBandDefinition,
    SubscriberBandSet,
    SubscriberRelativeBacktestDataset,
    SubscriberRelativeBacktestObservation,
    ThresholdBacktestReport,
    ThresholdEvaluationResult,
)
from app.services.backtesting.validation import BacktestDatasetValidator


class MedianStandardVideoVsrThresholdBacktester:
    """Produce factual subscriber-band threshold results without selecting policy."""

    def __init__(self, validator: BacktestDatasetValidator | None = None) -> None:
        self._validator = validator or BacktestDatasetValidator()

    def analyze(
        self,
        dataset: SubscriberRelativeBacktestDataset,
        band_set: SubscriberBandSet,
        threshold_set: MedianVsrThresholdSet,
        generated_at: datetime,
    ) -> ThresholdBacktestReport:
        """Validate and analyze one immutable historical research cohort."""
        self._validator.validate(dataset, band_set, threshold_set, generated_at)
        observations = tuple(
            sorted(dataset.observations, key=lambda item: item.observation_id)
        )
        assigned: dict[str, list[SubscriberRelativeBacktestObservation]] = {
            band.band_id: [] for band in band_set.bands
        }
        eligible_values: dict[str, list[float]] = {
            band.band_id: [] for band in band_set.bands
        }
        exclusions: list[BacktestExclusion] = []

        for observation in observations:
            band = band_set.assign(observation.subscriber_count)
            if band is not None:
                assigned[band.band_id].append(observation)
            exclusion = self._exclusion(observation, band)
            if exclusion is not None:
                exclusions.append(exclusion)
                continue
            median_vsr = observation.analysis.analytics.median_standard_video_vsr
            if median_vsr is None or band is None:
                raise AssertionError("eligible observation must have a band and median VSR")
            eligible_values[band.band_id].append(median_vsr)

        globally_eligible = sum(len(values) for values in eligible_values.values())
        return ThresholdBacktestReport(
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
            band_set_id=band_set.band_set_id,
            band_set_version=band_set.version,
            threshold_set_id=threshold_set.threshold_set_id,
            threshold_set_version=threshold_set.version,
            generated_at=generated_at,
            source_observation_count=len(observations),
            global_coverage=self._coverage(
                observations,
                threshold_eligible_count=globally_eligible,
            ),
            qualification_failure_counts=self._failure_counts(observations),
            band_results=tuple(
                self._band_result(
                    band,
                    tuple(assigned[band.band_id]),
                    tuple(eligible_values[band.band_id]),
                    band_set,
                    threshold_set,
                )
                for band in band_set.bands
            ),
            exclusions=tuple(exclusions),
        )

    @staticmethod
    def _exclusion(
        observation: SubscriberRelativeBacktestObservation,
        band: SubscriberBandDefinition | None,
    ) -> BacktestExclusion | None:
        qualification = observation.analysis.qualification
        if not qualification.qualified:
            reason = BacktestExclusionReason.UNQUALIFIED_ANALYSIS
        elif observation.analysis.analytics.median_standard_video_vsr is None:
            reason = BacktestExclusionReason.MEDIAN_VSR_UNAVAILABLE
        elif band is None:
            reason = BacktestExclusionReason.NO_MATCHING_SUBSCRIBER_BAND
        else:
            return None
        return BacktestExclusion(
            observation_id=observation.observation_id,
            channel_id=observation.channel_id,
            reason=reason,
            qualification_failures=qualification.failures,
        )

    @staticmethod
    def _coverage(
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
        *,
        threshold_eligible_count: int,
    ) -> QualificationCoverageSummary:
        total = len(observations)
        qualified = sum(
            observation.analysis.qualification.qualified
            for observation in observations
        )
        available = sum(
            observation.analysis.analytics.median_standard_video_vsr is not None
            for observation in observations
        )
        return QualificationCoverageSummary(
            total_observations=total,
            qualified_observations=qualified,
            unqualified_observations=total - qualified,
            qualified_percentage=None if total == 0 else qualified / total,
            median_vsr_available_count=available,
            median_vsr_unavailable_count=total - available,
            threshold_eligible_count=threshold_eligible_count,
            threshold_excluded_count=total - threshold_eligible_count,
        )

    @staticmethod
    def _failure_counts(
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
    ) -> tuple[QualificationFailureCount, ...]:
        return tuple(
            QualificationFailureCount(
                failure=failure,
                count=sum(
                    failure in observation.analysis.qualification.failures
                    for observation in observations
                ),
            )
            for failure in QualificationFailureReason
            if any(
                failure in observation.analysis.qualification.failures
                for observation in observations
            )
        )

    def _band_result(
        self,
        band: SubscriberBandDefinition,
        observations: tuple[SubscriberRelativeBacktestObservation, ...],
        values: tuple[float, ...],
        band_set: SubscriberBandSet,
        threshold_set: MedianVsrThresholdSet,
    ) -> SubscriberBandBacktestResult:
        return SubscriberBandBacktestResult(
            band_id=band.band_id,
            coverage=self._coverage(
                observations,
                threshold_eligible_count=len(values),
            ),
            distribution=self._distribution(values),
            threshold_results=tuple(
                self._threshold_result(
                    band,
                    candidate,
                    values,
                    len(observations) - len(values),
                    band_set.version,
                    threshold_set.version,
                )
                for candidate in threshold_set.candidates
            ),
        )

    @staticmethod
    def _distribution(values: tuple[float, ...]) -> DistributionSummary:
        if not values:
            return DistributionSummary(
                eligible_observation_count=0,
                minimum=None,
                maximum=None,
                arithmetic_mean=None,
                median=None,
            )
        ordered = tuple(sorted(values))
        return DistributionSummary(
            eligible_observation_count=len(ordered),
            minimum=ordered[0],
            maximum=ordered[-1],
            arithmetic_mean=fmean(ordered),
            median=median(ordered),
        )

    @staticmethod
    def _threshold_result(
        band: SubscriberBandDefinition,
        candidate: MedianVsrThresholdCandidate,
        values: tuple[float, ...],
        excluded_count: int,
        band_set_version: int,
        threshold_set_version: int,
    ) -> ThresholdEvaluationResult:
        hit_count = sum(candidate.matches(value) for value in values)
        eligible_count = len(values)
        return ThresholdEvaluationResult(
            band_id=band.band_id,
            candidate_id=candidate.candidate_id,
            threshold=candidate.threshold,
            operator=candidate.operator,
            band_set_version=band_set_version,
            threshold_set_version=threshold_set_version,
            eligible_observation_count=eligible_count,
            hit_count=hit_count,
            non_hit_count=eligible_count - hit_count,
            excluded_count=excluded_count,
            hit_rate=None if eligible_count == 0 else hit_count / eligible_count,
        )
