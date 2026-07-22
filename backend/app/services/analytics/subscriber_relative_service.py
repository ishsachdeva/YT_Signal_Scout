"""Application entry point for subscriber-relative analytics."""

from __future__ import annotations

from datetime import datetime

from app.services.analytics.eligibility import EligibleVideoClassifier
from app.services.analytics.models import ChannelAnalytics
from app.services.analytics.qualification import (
    SubscriberRelativeAnalysisResult,
    SubscriberRelativeQualificationService,
    SubscriberState,
)
from app.services.analytics.subscriber_relative_orchestrator import (
    SubscriberRelativeAnalyticsOrchestrator,
)
from app.services.analytics.subscriber_relative_result_assembler import (
    SubscriberRelativeResultAssembler,
)
from app.services.youtube.models import Channel, VideoAcquisitionResult


class SubscriberRelativeAnalyticsService:
    """Connect the approved subscriber-relative analytics pipeline stages."""

    def __init__(
        self,
        classifier: EligibleVideoClassifier,
        qualification_service: SubscriberRelativeQualificationService,
        orchestrator: SubscriberRelativeAnalyticsOrchestrator,
        result_assembler: SubscriberRelativeResultAssembler,
    ) -> None:
        self._classifier = classifier
        self._qualification_service = qualification_service
        self._orchestrator = orchestrator
        self._result_assembler = result_assembler

    def analyze(
        self,
        channel: Channel,
        acquisition: VideoAcquisitionResult,
        evaluation_time: datetime,
    ) -> SubscriberRelativeAnalysisResult:
        """Return qualification and factual analytics from one acquisition."""
        source_dataset = ChannelAnalytics(
            channel=channel,
            videos=list(acquisition.unique_canonical_videos),
            generated_at=evaluation_time,
        )
        classification = self._classifier.classify(
            source_dataset,
            evaluation_time,
        )
        qualification = self._qualification_service.qualify(
            acquisition.provenance,
            classification,
            channel,
            evaluation_time,
        )
        subscriber_count = (
            channel.statistics.subscriber_count
            if qualification.subscriber_state is SubscriberState.AVAILABLE_POSITIVE
            and channel.statistics is not None
            else None
        )
        metric_results = self._orchestrator.calculate_all(
            classification,
            subscriber_count,
        )
        analytics = self._result_assembler.assemble(metric_results)
        return SubscriberRelativeAnalysisResult(
            qualification=qualification,
            analytics=analytics,
        )
