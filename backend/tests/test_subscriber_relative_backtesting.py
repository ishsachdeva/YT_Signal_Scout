"""Tests for deterministic offline subscriber-band median-VSR backtesting."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest import TestCase

from pydantic import ValidationError

from app.application import create_application
from app.core.config import Settings
from app.services.analytics.models import SubscriberRelativeAnalytics
from app.services.analytics.qualification import (
    QualificationFailureReason,
    SubscriberRelativeAnalysisResult,
    SubscriberRelativeQualification,
    SubscriberState,
)
from app.services.backtesting import (
    BacktestExclusionReason,
    BacktestValidationError,
    ComparisonOperator,
    MedianStandardVideoVsrThresholdBacktester,
    MedianVsrThresholdCandidate,
    MedianVsrThresholdSet,
    SubscriberBandDefinition,
    SubscriberBandSet,
    SubscriberRelativeBacktestDataset,
    SubscriberRelativeBacktestObservation,
    ThresholdBacktestReport,
)
from app.services.youtube.models import (
    AcquisitionSource,
    PaginationProvenance,
    PaginationStatus,
    VideoAcquisitionProvenance,
)

_NOW = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _analysis(
    *,
    channel_id: str = "channel-1",
    observed_at: datetime = _NOW,
    median_vsr: float | None = 1.0,
    failures: tuple[QualificationFailureReason, ...] = (),
    subscriber_state: SubscriberState = SubscriberState.AVAILABLE_POSITIVE,
) -> SubscriberRelativeAnalysisResult:
    provenance = VideoAcquisitionProvenance(
        source=AcquisitionSource.UPLOADS_PLAYLIST,
        source_channel_id=channel_id,
        discovery_request_capacity=5,
        discovered_position_count=5,
        discovered_unique_video_count=5,
        enrichment_requested_unique_count=5,
        enriched_unique_video_count=5,
        enriched_output_position_count=5,
        omitted_unique_video_count=0,
        pagination=PaginationProvenance(
            status=PaginationStatus.COMPLETE,
            pages_fetched=1,
            page_size_requested=5,
            page_limit=1,
            next_page_token_present=False,
        ),
    )
    return SubscriberRelativeAnalysisResult(
        qualification=SubscriberRelativeQualification(
            qualified=not failures,
            failures=failures,
            provenance=provenance,
            requested_id_resolution_rate=1.0,
            eligible_standard_video_count=5,
            subscriber_state=subscriber_state,
            evaluated_at=observed_at,
        ),
        analytics=SubscriberRelativeAnalytics(
            eligible_standard_video_count=5,
            median_standard_video_vsr=median_vsr,
        ),
    )


def _observation(
    observation_id: str,
    *,
    channel_id: str | None = None,
    subscriber_count: int = 500,
    median_vsr: float | None = 1.0,
    failures: tuple[QualificationFailureReason, ...] = (),
    observed_at: datetime = _NOW,
) -> SubscriberRelativeBacktestObservation:
    resolved_channel_id = channel_id or f"channel-{observation_id}"
    return SubscriberRelativeBacktestObservation(
        observation_id=observation_id,
        channel_id=resolved_channel_id,
        observed_at=observed_at,
        subscriber_count=subscriber_count,
        analysis=_analysis(
            channel_id=resolved_channel_id,
            observed_at=observed_at,
            median_vsr=median_vsr,
            failures=failures,
        ),
    )


def _dataset(*observations: SubscriberRelativeBacktestObservation):
    return SubscriberRelativeBacktestDataset(
        dataset_id="research-dataset-v1",
        version=1,
        observations=observations,
    )


def _bands() -> SubscriberBandSet:
    return SubscriberBandSet(
        band_set_id="research-band-set-v1",
        version=1,
        bands=(
            SubscriberBandDefinition(
                band_id="fixture-small", lower_bound=1, upper_bound=1_000
            ),
            SubscriberBandDefinition(
                band_id="fixture-large", lower_bound=1_000, upper_bound=None
            ),
        ),
    )


def _thresholds() -> MedianVsrThresholdSet:
    return MedianVsrThresholdSet(
        threshold_set_id="research-threshold-set-v1",
        version=1,
        candidates=(
            MedianVsrThresholdCandidate(
                candidate_id="candidate-1",
                threshold=1.0,
                operator=ComparisonOperator.GREATER_THAN,
            ),
            MedianVsrThresholdCandidate(
                candidate_id="candidate-2",
                threshold=1.0,
                operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            ),
        ),
    )


class SubscriberBandConfigurationTests(TestCase):
    def test_contiguous_boundaries_and_unbounded_final_band_assign_once(self) -> None:
        bands = _bands()
        self.assertEqual(bands.assign(999).band_id, "fixture-small")
        self.assertEqual(bands.assign(1_000).band_id, "fixture-large")
        self.assertEqual(bands.assign(10_000_000).band_id, "fixture-large")

    def test_overlapping_bands_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "overlap"):
            SubscriberBandSet(
                band_set_id="research-band-set-v1",
                version=1,
                bands=(
                    SubscriberBandDefinition(
                        band_id="fixture-a", lower_bound=1, upper_bound=100
                    ),
                    SubscriberBandDefinition(
                        band_id="fixture-b", lower_bound=99, upper_bound=None
                    ),
                ),
            )

    def test_duplicate_ids_invalid_bounds_and_nonfinal_unbounded_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unique"):
            SubscriberBandSet(
                band_set_id="research-band-set-v1",
                version=1,
                bands=(
                    SubscriberBandDefinition(
                        band_id="fixture-a", lower_bound=1, upper_bound=100
                    ),
                    SubscriberBandDefinition(
                        band_id="fixture-a", lower_bound=100, upper_bound=None
                    ),
                ),
            )
        with self.assertRaisesRegex(ValidationError, "must exceed"):
            SubscriberBandDefinition(
                band_id="fixture-a", lower_bound=100, upper_bound=100
            )
        with self.assertRaisesRegex(ValidationError, "final"):
            SubscriberBandSet(
                band_set_id="research-band-set-v1",
                version=1,
                bands=(
                    SubscriberBandDefinition(
                        band_id="fixture-a", lower_bound=1, upper_bound=None
                    ),
                    SubscriberBandDefinition(
                        band_id="fixture-b", lower_bound=100, upper_bound=None
                    ),
                ),
            )

    def test_gaps_are_rejected_unless_explicitly_supported(self) -> None:
        configured = (
            SubscriberBandDefinition(
                band_id="fixture-a", lower_bound=1, upper_bound=100
            ),
            SubscriberBandDefinition(
                band_id="fixture-b", lower_bound=200, upper_bound=None
            ),
        )
        with self.assertRaisesRegex(ValidationError, "gaps"):
            SubscriberBandSet(
                band_set_id="research-band-set-v1",
                version=1,
                bands=configured,
            )
        bands = SubscriberBandSet(
            band_set_id="research-band-set-v1",
            version=1,
            bands=configured,
            allow_gaps=True,
        )
        self.assertIsNone(bands.assign(150))

        for incomplete in (
            (
                SubscriberBandDefinition(
                    band_id="fixture-a", lower_bound=2, upper_bound=None
                ),
            ),
            (
                SubscriberBandDefinition(
                    band_id="fixture-a", lower_bound=1, upper_bound=100
                ),
            ),
        ):
            with self.subTest(incomplete=incomplete), self.assertRaisesRegex(
                ValidationError, "gaps"
            ):
                SubscriberBandSet(
                    band_set_id="research-band-set-v1",
                    version=1,
                    bands=incomplete,
                )


class ThresholdConfigurationTests(TestCase):
    def test_candidate_order_and_exact_boundary_operators_are_preserved(self) -> None:
        thresholds = _thresholds()
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in thresholds.candidates),
            ("candidate-1", "candidate-2"),
        )
        self.assertFalse(thresholds.candidates[0].matches(1.0))
        self.assertTrue(thresholds.candidates[1].matches(1.0))

    def test_duplicate_candidate_ids_and_invalid_values_are_rejected(self) -> None:
        candidate = MedianVsrThresholdCandidate(
            candidate_id="candidate-1",
            threshold=1.0,
            operator=ComparisonOperator.GREATER_THAN,
        )
        with self.assertRaisesRegex(ValidationError, "unique"):
            MedianVsrThresholdSet(
                threshold_set_id="research-threshold-set-v1",
                version=1,
                candidates=(candidate, candidate),
            )
        for value in (-1.0, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                MedianVsrThresholdCandidate(
                    candidate_id="candidate-invalid",
                    threshold=value,
                    operator=ComparisonOperator.GREATER_THAN,
                )
        with self.assertRaises(ValidationError):
            MedianVsrThresholdCandidate(
                candidate_id="candidate-invalid",
                threshold=1.0,
                operator="approximately",
            )


class BacktestObservationValidationTests(TestCase):
    def test_observation_is_immutable(self) -> None:
        observation = _observation("observation-1")
        with self.assertRaises(ValidationError):
            observation.subscriber_count = 600

    def test_naive_timestamp_and_nonpositive_subscriber_count_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "timezone-aware"):
            _observation("observation-1", observed_at=datetime(2026, 7, 22, 12))
        for count in (0, -1):
            with self.subTest(count=count), self.assertRaises(ValidationError):
                _observation("observation-1", subscriber_count=count)

    def test_contradictory_subscriber_state_and_timestamp_mismatch_are_rejected(self) -> None:
        analysis = _analysis(subscriber_state=SubscriberState.HIDDEN)
        with self.assertRaisesRegex(ValidationError, "available-positive"):
            SubscriberRelativeBacktestObservation(
                observation_id="observation-1",
                channel_id="channel-1",
                observed_at=_NOW,
                subscriber_count=100,
                analysis=analysis,
            )
        with self.assertRaisesRegex(ValidationError, "timestamp must match"):
            SubscriberRelativeBacktestObservation(
                observation_id="observation-1",
                channel_id="channel-1",
                observed_at=_NOW + timedelta(seconds=1),
                subscriber_count=100,
                analysis=_analysis(),
            )

    def test_mismatched_provenance_channel_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "provenance channel"):
            SubscriberRelativeBacktestObservation(
                observation_id="observation-1",
                channel_id="channel-other",
                observed_at=_NOW,
                subscriber_count=100,
                analysis=_analysis(channel_id="channel-1"),
            )

    def test_duplicate_identity_and_snapshot_are_typed_structural_errors(self) -> None:
        backtester = MedianStandardVideoVsrThresholdBacktester()
        observation = _observation("observation-1", channel_id="channel-1")
        duplicate_id = observation.model_copy(
            update={"channel_id": "channel-2", "analysis": _analysis(channel_id="channel-2")}
        )
        with self.assertRaisesRegex(BacktestValidationError, "IDs must be unique"):
            backtester.analyze(
                _dataset(observation, duplicate_id), _bands(), _thresholds(), _NOW
            )
        duplicate_snapshot = _observation("observation-2", channel_id="channel-1")
        with self.assertRaisesRegex(BacktestValidationError, "timestamp pairs"):
            backtester.analyze(
                _dataset(observation, duplicate_snapshot),
                _bands(),
                _thresholds(),
                _NOW,
            )


class MedianVsrThresholdBacktesterTests(TestCase):
    def setUp(self) -> None:
        self.backtester = MedianStandardVideoVsrThresholdBacktester()

    def test_coverage_exclusions_and_failures_remain_factual_and_typed(self) -> None:
        failures = (
            QualificationFailureReason.ACQUISITION_TRUNCATED,
            QualificationFailureReason.INSUFFICIENT_ELIGIBLE_STANDARD_VIDEOS,
        )
        report = self.backtester.analyze(
            _dataset(
                _observation("observation-1", median_vsr=2.0),
                _observation("observation-2", median_vsr=None),
                _observation("observation-3", median_vsr=3.0, failures=failures),
            ),
            _bands(),
            _thresholds(),
            _NOW,
        )

        self.assertEqual(report.global_coverage.total_observations, 3)
        self.assertEqual(report.global_coverage.qualified_observations, 2)
        self.assertEqual(report.global_coverage.unqualified_observations, 1)
        self.assertEqual(report.global_coverage.qualified_percentage, 2 / 3)
        self.assertEqual(report.global_coverage.median_vsr_available_count, 2)
        self.assertEqual(report.global_coverage.threshold_eligible_count, 1)
        self.assertEqual(
            tuple(exclusion.reason for exclusion in report.exclusions),
            (
                BacktestExclusionReason.MEDIAN_VSR_UNAVAILABLE,
                BacktestExclusionReason.UNQUALIFIED_ANALYSIS,
            ),
        )
        self.assertEqual(report.exclusions[1].qualification_failures, failures)
        self.assertEqual(
            tuple(item.failure for item in report.qualification_failure_counts),
            failures,
        )

    def test_distribution_statistics_cover_empty_one_odd_even_and_precision(self) -> None:
        report = self.backtester.analyze(
            _dataset(
                _observation("observation-1", median_vsr=1.0000000001),
                _observation("observation-2", median_vsr=2.0),
                _observation("observation-3", median_vsr=4.0),
                _observation("observation-4", median_vsr=8.0),
            ),
            _bands(),
            _thresholds(),
            _NOW,
        )
        distribution = report.band_results[0].distribution
        self.assertEqual(distribution.eligible_observation_count, 4)
        self.assertEqual(distribution.minimum, 1.0000000001)
        self.assertEqual(distribution.maximum, 8.0)
        self.assertEqual(distribution.arithmetic_mean, (1.0000000001 + 2 + 4 + 8) / 4)
        self.assertEqual(distribution.median, 3.0)
        empty = report.band_results[1].distribution
        self.assertEqual(empty.eligible_observation_count, 0)
        self.assertIsNone(empty.minimum)
        self.assertIsNone(empty.arithmetic_mean)

        odd = self.backtester.analyze(
            _dataset(
                _observation("observation-1", median_vsr=1.0),
                _observation("observation-2", median_vsr=9.0),
                _observation("observation-3", median_vsr=3.0),
            ),
            _bands(),
            _thresholds(),
            _NOW,
        )
        self.assertEqual(odd.band_results[0].distribution.median, 3.0)

        one = self.backtester.analyze(
            _dataset(_observation("observation-1", median_vsr=7.0)),
            _bands(),
            _thresholds(),
            _NOW,
        )
        self.assertEqual(one.band_results[0].distribution.arithmetic_mean, 7.0)
        self.assertEqual(one.band_results[0].distribution.median, 7.0)

    def test_threshold_results_cover_none_all_mixed_and_exact_boundary(self) -> None:
        report = self.backtester.analyze(
            _dataset(
                _observation("observation-1", median_vsr=0.5),
                _observation("observation-2", median_vsr=1.0),
                _observation("observation-3", median_vsr=2.0),
            ),
            _bands(),
            _thresholds(),
            _NOW,
        )
        greater, inclusive = report.band_results[0].threshold_results
        self.assertEqual((greater.hit_count, greater.non_hit_count), (1, 2))
        self.assertEqual(greater.hit_rate, 1 / 3)
        self.assertEqual((inclusive.hit_count, inclusive.non_hit_count), (2, 1))
        self.assertEqual(inclusive.hit_rate, 2 / 3)
        empty_results = report.band_results[1].threshold_results
        self.assertTrue(all(result.hit_count == 0 for result in empty_results))
        self.assertTrue(all(result.hit_rate is None for result in empty_results))

    def test_threshold_results_support_all_hits_and_no_hits(self) -> None:
        thresholds = MedianVsrThresholdSet(
            threshold_set_id="research-threshold-set-v1",
            version=1,
            candidates=(
                MedianVsrThresholdCandidate(
                    candidate_id="candidate-all",
                    threshold=0.0,
                    operator=ComparisonOperator.GREATER_THAN,
                ),
                MedianVsrThresholdCandidate(
                    candidate_id="candidate-none",
                    threshold=10.0,
                    operator=ComparisonOperator.GREATER_THAN,
                ),
            ),
        )
        report = self.backtester.analyze(
            _dataset(
                _observation("observation-1", median_vsr=1.0),
                _observation("observation-2", median_vsr=2.0),
            ),
            _bands(),
            thresholds,
            _NOW,
        )
        all_hits, no_hits = report.band_results[0].threshold_results
        self.assertEqual((all_hits.hit_count, all_hits.hit_rate), (2, 1.0))
        self.assertEqual((no_hits.hit_count, no_hits.hit_rate), (0, 0.0))

    def test_multiple_bands_and_candidate_order_are_preserved(self) -> None:
        report = self.backtester.analyze(
            _dataset(
                _observation("observation-1", subscriber_count=999, median_vsr=2.0),
                _observation("observation-2", subscriber_count=1_000, median_vsr=0.5),
            ),
            _bands(),
            _thresholds(),
            _NOW,
        )
        self.assertEqual(
            tuple(result.band_id for result in report.band_results),
            ("fixture-small", "fixture-large"),
        )
        self.assertEqual(
            tuple(
                result.candidate_id
                for result in report.band_results[0].threshold_results
            ),
            ("candidate-1", "candidate-2"),
        )

    def test_no_matching_band_is_a_normal_exclusion(self) -> None:
        bands = SubscriberBandSet(
            band_set_id="research-band-set-v1",
            version=1,
            bands=(
                SubscriberBandDefinition(
                    band_id="fixture-band", lower_bound=100, upper_bound=None
                ),
            ),
            allow_gaps=True,
        )
        report = self.backtester.analyze(
            _dataset(_observation("observation-1", subscriber_count=50)),
            bands,
            _thresholds(),
            _NOW,
        )
        self.assertEqual(
            report.exclusions[0].reason,
            BacktestExclusionReason.NO_MATCHING_SUBSCRIBER_BAND,
        )
        self.assertEqual(report.global_coverage.threshold_eligible_count, 0)

    def test_empty_dataset_has_explicit_unavailable_rates_and_statistics(self) -> None:
        report = self.backtester.analyze(
            _dataset(), _bands(), _thresholds(), _NOW
        )
        self.assertIsNone(report.global_coverage.qualified_percentage)
        self.assertTrue(
            all(
                result.distribution.minimum is None
                for result in report.band_results
            )
        )
        self.assertTrue(
            all(
                threshold.hit_rate is None
                for band in report.band_results
                for threshold in band.threshold_results
            )
        )

    def test_naive_report_generation_time_is_a_structural_error(self) -> None:
        with self.assertRaisesRegex(BacktestValidationError, "timezone-aware"):
            self.backtester.analyze(
                _dataset(),
                _bands(),
                _thresholds(),
                datetime(2026, 7, 22, 12),
            )

    def test_reordered_inputs_are_equal_inputs_unchanged_and_report_serializes(self) -> None:
        first_observation = _observation("observation-1", median_vsr=1.0)
        second_observation = _observation("observation-2", median_vsr=3.0)
        source = _dataset(second_observation, first_observation)
        before = source.model_dump()

        first = self.backtester.analyze(source, _bands(), _thresholds(), _NOW)
        second = self.backtester.analyze(
            _dataset(first_observation, second_observation),
            _bands(),
            _thresholds(),
            _NOW,
        )

        self.assertEqual(first, second)
        self.assertEqual(source.model_dump(), before)
        self.assertEqual(
            ThresholdBacktestReport.model_validate_json(first.model_dump_json()),
            first,
        )

    def test_backtester_is_not_registered_in_production_application(self) -> None:
        application = create_application(
            Settings(environment="test", log_level="CRITICAL")
        )
        self.assertFalse(hasattr(application.state, "threshold_backtester"))
        report = self.backtester.analyze(
            _dataset(_observation("observation-1")),
            _bands(),
            _thresholds(),
            _NOW,
        )
        self.assertIsInstance(report, ThresholdBacktestReport)


if __name__ == "__main__":
    import unittest

    unittest.main()
