"""Application entry point for subscriber-relative analytics."""

from __future__ import annotations

from datetime import datetime

from app.services.analytics.eligibility import EligibleVideoClassifier
from app.services.analytics.models import ChannelAnalytics, SubscriberRelativeAnalytics
from app.services.analytics.subscriber_relative_orchestrator import (
    SubscriberRelativeAnalyticsOrchestrator,
)
from app.services.analytics.subscriber_relative_result_assembler import (
    SubscriberRelativeResultAssembler,
)


class SubscriberRelativeAnalyticsService:
    """Connect the approved subscriber-relative analytics pipeline stages."""

    def __init__(
        self,
        classifier: EligibleVideoClassifier,
        orchestrator: SubscriberRelativeAnalyticsOrchestrator,
        result_assembler: SubscriberRelativeResultAssembler,
    ) -> None:
        self._classifier = classifier
        self._orchestrator = orchestrator
        self._result_assembler = result_assembler

    def calculate(
        self,
        source_dataset: ChannelAnalytics,
        subscriber_count: int | None,
        evaluation_time: datetime,
    ) -> SubscriberRelativeAnalytics:
        """Return fully assembled subscriber-relative analytics."""
        classification = self._classifier.classify(
            source_dataset,
            evaluation_time,
        )
        metric_results = self._orchestrator.calculate_all(
            classification,
            subscriber_count,
        )
        return self._result_assembler.assemble(metric_results)
