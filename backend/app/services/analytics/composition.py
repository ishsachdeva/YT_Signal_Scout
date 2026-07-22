"""Composition of production analytics dependencies."""

from app.services.analytics.calculators.video.eligible_standard_video_count import (
    EligibleStandardVideoCountCalculator,
)
from app.services.analytics.calculators.video.median_standard_video_vsr import (
    MedianStandardVideoVsrCalculator,
)
from app.services.analytics.eligibility import EligibleVideoClassifier
from app.services.analytics.subscriber_relative_orchestrator import (
    SubscriberRelativeAnalyticsOrchestrator,
)
from app.services.analytics.subscriber_relative_result_assembler import (
    SubscriberRelativeResultAssembler,
)
from app.services.analytics.subscriber_relative_service import (
    SubscriberRelativeAnalyticsService,
)


def build_subscriber_relative_analytics_service() -> (
    SubscriberRelativeAnalyticsService
):
    """Construct the production subscriber-relative analytics pipeline."""
    orchestrator = SubscriberRelativeAnalyticsOrchestrator(
        EligibleStandardVideoCountCalculator(),
        MedianStandardVideoVsrCalculator(),
    )
    return SubscriberRelativeAnalyticsService(
        classifier=EligibleVideoClassifier(),
        orchestrator=orchestrator,
        result_assembler=SubscriberRelativeResultAssembler(),
    )
