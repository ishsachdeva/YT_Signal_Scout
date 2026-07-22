"""Tests for controlled deterministic offline backtest execution."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase
from unittest.mock import Mock

from pydantic import ValidationError

from app.services.analytics.models import SubscriberRelativeAnalytics
from app.services.analytics.qualification import (
    SubscriberRelativeAnalysisResult,
    SubscriberRelativeQualification,
    SubscriberState,
)
from app.services.backtesting import (
    BacktestExecutionConfiguration,
    BacktestExecutionConfigurationMismatchError,
    BacktestExecutionDatasetMismatchError,
    BacktestExecutionRequest,
    BacktestExecutionResult,
    BacktestExecutionService,
    BacktestExecutionStructuralError,
    BacktestValidationError,
    ComparisonOperator,
    HistoricalDatasetImportResult,
    HistoricalDatasetManifest,
    InvalidBacktestExecutionRequestError,
    MedianStandardVideoVsrThresholdBacktester,
    MedianVsrThresholdCandidate,
    MedianVsrThresholdSet,
    SubscriberBandDefinition,
    SubscriberBandSet,
    SubscriberRelativeBacktestDataset,
    SubscriberRelativeBacktestObservation,
)
from app.services.youtube.models import (
    AcquisitionSource,
    PaginationProvenance,
    PaginationStatus,
    VideoAcquisitionProvenance,
)

_NOW = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _imported_dataset() -> HistoricalDatasetImportResult:
    provenance = VideoAcquisitionProvenance(
        source=AcquisitionSource.UPLOADS_PLAYLIST,
        source_channel_id="channel-1",
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
    analysis = SubscriberRelativeAnalysisResult(
        qualification=SubscriberRelativeQualification(
            qualified=True,
            failures=(),
            provenance=provenance,
            requested_id_resolution_rate=1.0,
            eligible_standard_video_count=5,
            subscriber_state=SubscriberState.AVAILABLE_POSITIVE,
            evaluated_at=_NOW,
        ),
        analytics=SubscriberRelativeAnalytics(
            eligible_standard_video_count=5,
            median_standard_video_vsr=1.5,
        ),
    )
    dataset = SubscriberRelativeBacktestDataset(
        dataset_id="research-dataset-v1",
        version=1,
        observations=(
            SubscriberRelativeBacktestObservation(
                observation_id="observation-1",
                channel_id="channel-1",
                observed_at=_NOW,
                subscriber_count=500,
                analysis=analysis,
            ),
        ),
    )
    return HistoricalDatasetImportResult(
        manifest=HistoricalDatasetManifest(
            schema_version=1,
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
        ),
        dataset=dataset,
    )


def _configuration(
    *, dataset_id: str = "research-dataset-v1"
) -> BacktestExecutionConfiguration:
    return BacktestExecutionConfiguration(
        configuration_id="study-v1",
        version=1,
        dataset_id=dataset_id,
        dataset_version=1,
        band_set=SubscriberBandSet(
            band_set_id="bands-v1",
            version=1,
            bands=(SubscriberBandDefinition(band_id="all", lower_bound=1),),
        ),
        threshold_set=MedianVsrThresholdSet(
            threshold_set_id="thresholds-v1",
            version=1,
            candidates=(
                MedianVsrThresholdCandidate(
                    candidate_id="candidate-1",
                    threshold=1.0,
                    operator=ComparisonOperator.GREATER_THAN,
                ),
            ),
        ),
    )


def _request(
    *, configuration: BacktestExecutionConfiguration | None = None
) -> BacktestExecutionRequest:
    return BacktestExecutionRequest(
        execution_id="execution-1",
        executed_at=_NOW,
        imported_dataset=_imported_dataset(),
        configuration=configuration or _configuration(),
    )


class BacktestExecutionServiceTests(TestCase):
    def test_successfully_executes_existing_backtester_and_builds_metadata(self) -> None:
        request = _request()
        result = BacktestExecutionService().execute(request)

        self.assertIsInstance(result, BacktestExecutionResult)
        self.assertEqual(result.report.global_coverage.threshold_eligible_count, 1)
        self.assertEqual(result.metadata.execution_id, "execution-1")
        self.assertEqual(result.metadata.dataset_id, "research-dataset-v1")
        self.assertEqual(result.metadata.configuration_id, "study-v1")
        self.assertEqual(result.metadata.band_set_id, "bands-v1")
        self.assertEqual(result.metadata.threshold_set_id, "thresholds-v1")
        self.assertEqual(result.metadata.executed_at, _NOW)

    def test_repeated_execution_is_equal_and_does_not_mutate_input(self) -> None:
        request = _request()
        before = request.model_dump_json()
        service = BacktestExecutionService()

        first = service.execute(request)
        second = service.execute(request)

        self.assertEqual(first, second)
        self.assertEqual(request.model_dump_json(), before)

    def test_request_and_result_are_immutable(self) -> None:
        request = _request()
        result = BacktestExecutionService().execute(request)

        with self.assertRaises(ValidationError):
            request.execution_id = "changed"
        with self.assertRaises(ValidationError):
            result.metadata.configuration_version = 2

    def test_configuration_bound_to_another_dataset_has_typed_failure(self) -> None:
        request = _request(configuration=_configuration(dataset_id="another-dataset"))

        with self.assertRaises(BacktestExecutionDatasetMismatchError):
            BacktestExecutionService().execute(request)

    def test_invalid_request_has_typed_failure(self) -> None:
        with self.assertRaises(InvalidBacktestExecutionRequestError):
            BacktestExecutionService().execute(None)  # type: ignore[arg-type]

    def test_existing_backtester_is_invoked_once_with_exact_inputs(self) -> None:
        request = _request()
        report = MedianStandardVideoVsrThresholdBacktester().analyze(
            request.imported_dataset.dataset,
            request.configuration.band_set,
            request.configuration.threshold_set,
            request.executed_at,
        )
        backtester = Mock()
        backtester.analyze.return_value = report

        result = BacktestExecutionService(backtester).execute(request)

        backtester.analyze.assert_called_once_with(
            request.imported_dataset.dataset,
            request.configuration.band_set,
            request.configuration.threshold_set,
            request.executed_at,
        )
        self.assertIs(result.report, report)

    def test_backtester_validation_failure_becomes_typed_structural_failure(self) -> None:
        backtester = Mock()
        backtester.analyze.side_effect = BacktestValidationError("invalid structure")

        with self.assertRaises(BacktestExecutionStructuralError):
            BacktestExecutionService(backtester).execute(_request())

    def test_mismatched_report_configuration_has_typed_failure(self) -> None:
        request = _request()
        report = MedianStandardVideoVsrThresholdBacktester().analyze(
            request.imported_dataset.dataset,
            request.configuration.band_set,
            request.configuration.threshold_set,
            request.executed_at,
        ).model_copy(update={"threshold_set_version": 2})
        backtester = Mock()
        backtester.analyze.return_value = report

        with self.assertRaises(BacktestExecutionConfigurationMismatchError):
            BacktestExecutionService(backtester).execute(request)
