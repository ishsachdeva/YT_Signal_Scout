"""Deterministic offline analytical backtesting contracts."""

from app.services.backtesting.exceptions import (
    BacktestValidationError,
    HistoricalDatasetDuplicateError,
    HistoricalDatasetImportError,
    HistoricalDatasetReadError,
    HistoricalDatasetSyntaxError,
    HistoricalDatasetValidationError,
    UnsupportedHistoricalDatasetSchemaError,
)
from app.services.backtesting.import_models import (
    HISTORICAL_DATASET_SCHEMA_VERSION,
    HistoricalDatasetImportResult,
    HistoricalDatasetManifest,
)
from app.services.backtesting.importer import HistoricalDatasetImporter
from app.services.backtesting.models import (
    BacktestExclusion,
    BacktestExclusionReason,
    ComparisonOperator,
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
from app.services.backtesting.service import (
    MedianStandardVideoVsrThresholdBacktester,
)
from app.services.backtesting.validation import BacktestDatasetValidator

__all__ = [
    "BacktestDatasetValidator",
    "BacktestExclusion",
    "BacktestExclusionReason",
    "BacktestValidationError",
    "ComparisonOperator",
    "DistributionSummary",
    "HISTORICAL_DATASET_SCHEMA_VERSION",
    "HistoricalDatasetDuplicateError",
    "HistoricalDatasetImportError",
    "HistoricalDatasetImporter",
    "HistoricalDatasetImportResult",
    "HistoricalDatasetManifest",
    "HistoricalDatasetReadError",
    "HistoricalDatasetSyntaxError",
    "HistoricalDatasetValidationError",
    "MedianStandardVideoVsrThresholdBacktester",
    "MedianVsrThresholdCandidate",
    "MedianVsrThresholdSet",
    "QualificationFailureCount",
    "QualificationCoverageSummary",
    "SubscriberBandBacktestResult",
    "SubscriberBandDefinition",
    "SubscriberBandSet",
    "SubscriberRelativeBacktestDataset",
    "SubscriberRelativeBacktestObservation",
    "ThresholdBacktestReport",
    "ThresholdEvaluationResult",
    "UnsupportedHistoricalDatasetSchemaError",
]
