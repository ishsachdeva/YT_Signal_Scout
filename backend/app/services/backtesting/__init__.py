"""Deterministic offline analytical backtesting contracts."""

from app.services.backtesting.exceptions import (
    BacktestExecutionConfigurationMismatchError,
    BacktestExecutionDatasetMismatchError,
    BacktestExecutionError,
    BacktestExecutionStructuralError,
    BacktestValidationError,
    HistoricalDatasetDuplicateError,
    HistoricalDatasetImportError,
    HistoricalDatasetReadError,
    HistoricalDatasetSyntaxError,
    HistoricalDatasetValidationError,
    InvalidBacktestExecutionRequestError,
    UnsupportedHistoricalDatasetSchemaError,
)
from app.services.backtesting.execution import BacktestExecutionService
from app.services.backtesting.execution_models import (
    BacktestExecutionConfiguration,
    BacktestExecutionMetadata,
    BacktestExecutionRequest,
    BacktestExecutionResult,
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
from app.services.backtesting.study_models import (
    BacktestStudyArtifact,
    BacktestStudyDecision,
    BacktestStudyDefinition,
    BacktestStudyReview,
    BacktestStudyStatus,
)
from app.services.backtesting.validation import BacktestDatasetValidator

__all__ = [
    "BacktestExecutionConfiguration",
    "BacktestExecutionConfigurationMismatchError",
    "BacktestExecutionDatasetMismatchError",
    "BacktestExecutionError",
    "BacktestExecutionMetadata",
    "BacktestExecutionRequest",
    "BacktestExecutionResult",
    "BacktestExecutionService",
    "BacktestExecutionStructuralError",
    "BacktestStudyArtifact",
    "BacktestStudyDecision",
    "BacktestStudyDefinition",
    "BacktestStudyReview",
    "BacktestStudyStatus",
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
    "InvalidBacktestExecutionRequestError",
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
