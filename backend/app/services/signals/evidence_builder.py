"""Deterministic projection from qualified analytics into typed evidence."""

from __future__ import annotations

from app.services.analytics.models import MetricType
from app.services.analytics.qualification import SubscriberRelativeAnalysisResult
from app.services.signals.evidence import (
    EvidenceAvailability,
    EvidenceFact,
    EvidenceUnit,
    MetricEvidence,
    QualificationEvidence,
    SignalEvidenceBundle,
    SignalEvidenceContext,
)


class SignalEvidenceBuilder:
    """Expose analysis facts without evaluating signal or threshold policy."""

    def build(
        self,
        analysis: SubscriberRelativeAnalysisResult,
    ) -> SignalEvidenceBundle:
        """Return the complete evidence projection for one analysis result."""
        qualification = analysis.qualification
        analytics = analysis.analytics
        context = SignalEvidenceContext(
            provenance=qualification.provenance,
            evaluated_at=qualification.evaluated_at,
        )
        return SignalEvidenceBundle(
            qualification=QualificationEvidence(
                value=qualification.qualified,
                failures=qualification.failures,
                policy_version=qualification.policy_version,
                context=context,
            ),
            eligible_sample=MetricEvidence[int](
                metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                value=analytics.eligible_standard_video_count,
                unit=EvidenceUnit.COUNT,
                availability=EvidenceAvailability.AVAILABLE,
                context=context,
            ),
            subscriber=MetricEvidence(
                metric=EvidenceFact.SUBSCRIBER_STATE,
                value=qualification.subscriber_state,
                unit=EvidenceUnit.STATE,
                availability=EvidenceAvailability.AVAILABLE,
                context=context,
            ),
            requested_id_resolution=MetricEvidence[float](
                metric=EvidenceFact.REQUESTED_ID_RESOLUTION_RATE,
                value=qualification.requested_id_resolution_rate,
                unit=EvidenceUnit.RATIO,
                availability=self._availability(
                    qualification.requested_id_resolution_rate
                ),
                context=context,
            ),
            median_standard_video_vsr=MetricEvidence[float](
                metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR,
                value=analytics.median_standard_video_vsr,
                unit=EvidenceUnit.RATIO,
                availability=self._availability(analytics.median_standard_video_vsr),
                context=context,
            ),
        )

    @staticmethod
    def _availability(value: object | None) -> EvidenceAvailability:
        return (
            EvidenceAvailability.UNAVAILABLE
            if value is None
            else EvidenceAvailability.AVAILABLE
        )
