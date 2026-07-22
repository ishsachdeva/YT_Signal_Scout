"""Deterministic offline analytical backtesting contracts."""

from app.services.backtesting.exceptions import BacktestValidationError
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
]
