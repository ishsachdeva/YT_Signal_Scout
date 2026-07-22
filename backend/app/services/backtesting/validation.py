"""Fail-fast structural validation for offline threshold backtests."""

from __future__ import annotations

from datetime import datetime

from app.services.backtesting.exceptions import BacktestValidationError
from app.services.backtesting.models import (
    MedianVsrThresholdSet,
    SubscriberBandSet,
    SubscriberRelativeBacktestDataset,
)


class BacktestDatasetValidator:
    """Validate cross-observation and invocation invariants once."""

    def validate(
        self,
        dataset: SubscriberRelativeBacktestDataset,
        band_set: SubscriberBandSet,
        threshold_set: MedianVsrThresholdSet,
        generated_at: datetime,
    ) -> None:
        """Raise a typed error for invalid structural input."""
        if not isinstance(dataset, SubscriberRelativeBacktestDataset):
            raise BacktestValidationError("typed backtest dataset is required")
        if not isinstance(band_set, SubscriberBandSet):
            raise BacktestValidationError("typed subscriber band set is required")
        if not isinstance(threshold_set, MedianVsrThresholdSet):
            raise BacktestValidationError("typed threshold set is required")
        if not isinstance(generated_at, datetime):
            raise BacktestValidationError("report generation time must be a datetime")
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise BacktestValidationError("report generation time must be timezone-aware")

        observation_ids = tuple(
            observation.observation_id for observation in dataset.observations
        )
        if len(set(observation_ids)) != len(observation_ids):
            raise BacktestValidationError("backtest observation IDs must be unique")

        snapshots = tuple(
            (observation.channel_id, observation.observed_at)
            for observation in dataset.observations
        )
        if len(set(snapshots)) != len(snapshots):
            raise BacktestValidationError(
                "channel and observation timestamp pairs must be unique"
            )
