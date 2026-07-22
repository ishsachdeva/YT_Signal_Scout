"""Controlled synchronous orchestration for offline threshold backtests."""

from __future__ import annotations

from app.services.backtesting.exceptions import (
    BacktestExecutionConfigurationMismatchError,
    BacktestExecutionDatasetMismatchError,
    BacktestExecutionStructuralError,
    BacktestValidationError,
    InvalidBacktestExecutionRequestError,
)
from app.services.backtesting.execution_models import (
    BacktestExecutionMetadata,
    BacktestExecutionRequest,
    BacktestExecutionResult,
)
from app.services.backtesting.models import ThresholdBacktestReport
from app.services.backtesting.service import MedianStandardVideoVsrThresholdBacktester


class BacktestExecutionService:
    """Validate, execute, and package one deterministic offline backtest."""

    def __init__(
        self,
        backtester: MedianStandardVideoVsrThresholdBacktester | None = None,
    ) -> None:
        self._backtester = backtester or MedianStandardVideoVsrThresholdBacktester()

    def execute(self, request: BacktestExecutionRequest) -> BacktestExecutionResult:
        """Execute an explicitly configured study without selecting policy."""
        if not isinstance(request, BacktestExecutionRequest):
            raise InvalidBacktestExecutionRequestError(
                "typed backtest execution request is required"
            )

        imported = request.imported_dataset
        configuration = request.configuration
        dataset = imported.dataset
        if (
            configuration.dataset_id != dataset.dataset_id
            or configuration.dataset_version != dataset.version
        ):
            raise BacktestExecutionDatasetMismatchError(
                "execution configuration does not target the imported dataset"
            )

        try:
            report = self._backtester.analyze(
                dataset,
                configuration.band_set,
                configuration.threshold_set,
                request.executed_at,
            )
        except BacktestValidationError as exc:
            raise BacktestExecutionStructuralError(
                "backtester rejected the validated execution inputs"
            ) from exc

        if not isinstance(report, ThresholdBacktestReport):
            raise BacktestExecutionStructuralError(
                "backtester returned an invalid report structure"
            )
        self._validate_report(request, report)
        return BacktestExecutionResult(
            metadata=BacktestExecutionMetadata(
                execution_id=request.execution_id,
                executed_at=request.executed_at,
                dataset_id=dataset.dataset_id,
                dataset_version=dataset.version,
                configuration_id=configuration.configuration_id,
                configuration_version=configuration.version,
                band_set_id=configuration.band_set.band_set_id,
                band_set_version=configuration.band_set.version,
                threshold_set_id=configuration.threshold_set.threshold_set_id,
                threshold_set_version=configuration.threshold_set.version,
            ),
            report=report,
        )

    @staticmethod
    def _validate_report(
        request: BacktestExecutionRequest,
        report: ThresholdBacktestReport,
    ) -> None:
        configuration = request.configuration
        dataset = request.imported_dataset.dataset
        if (
            report.dataset_id != dataset.dataset_id
            or report.dataset_version != dataset.version
        ):
            raise BacktestExecutionDatasetMismatchError(
                "backtest report does not match the imported dataset"
            )
        if (
            report.band_set_id != configuration.band_set.band_set_id
            or report.band_set_version != configuration.band_set.version
            or report.threshold_set_id != configuration.threshold_set.threshold_set_id
            or report.threshold_set_version != configuration.threshold_set.version
            or report.generated_at != request.executed_at
        ):
            raise BacktestExecutionConfigurationMismatchError(
                "backtest report does not match the execution configuration"
            )
