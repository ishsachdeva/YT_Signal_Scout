"""Tests for the policy-free subscriber-relative signal evidence projection."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from pydantic import ValidationError

from app.services.analytics.models import MetricType, SubscriberRelativeAnalytics
from app.services.analytics.qualification import (
    QualificationFailureReason,
    SubscriberRelativeAnalysisResult,
    SubscriberRelativeQualification,
    SubscriberState,
)
from app.services.signals.evidence import (
    EvidenceAvailability,
    EvidenceFact,
    EvidenceUnit,
    MetricEvidence,
)
from app.services.signals.evidence_builder import SignalEvidenceBuilder
from app.services.youtube.models import (
    AcquisitionSource,
    PaginationProvenance,
    PaginationStatus,
    VideoAcquisitionProvenance,
)

_EVALUATED_AT = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _provenance(*, requested: int = 5, enriched: int = 5):
    return VideoAcquisitionProvenance(
        source=AcquisitionSource.UPLOADS_PLAYLIST,
        source_channel_id="channel-1",
        discovery_request_capacity=max(requested, 1),
        discovered_position_count=requested,
        discovered_unique_video_count=requested,
        enrichment_requested_unique_count=requested,
        enriched_unique_video_count=enriched,
        enriched_output_position_count=enriched,
        omitted_unique_video_count=requested - enriched,
        pagination=PaginationProvenance(
            status=PaginationStatus.COMPLETE,
            pages_fetched=1,
            page_size_requested=max(requested, 1),
            page_limit=1,
            next_page_token_present=False,
        ),
    )


def _analysis(
    *,
    failures: tuple[QualificationFailureReason, ...] = (),
    subscriber_state: SubscriberState = SubscriberState.AVAILABLE_POSITIVE,
    resolution_rate: float | None = 1.0,
    median_vsr: float | None = 2.5,
    provenance: VideoAcquisitionProvenance | None = None,
) -> SubscriberRelativeAnalysisResult:
    return SubscriberRelativeAnalysisResult(
        qualification=SubscriberRelativeQualification(
            qualified=not failures,
            failures=failures,
            provenance=provenance or _provenance(),
            requested_id_resolution_rate=resolution_rate,
            eligible_standard_video_count=5,
            subscriber_state=subscriber_state,
            evaluated_at=_EVALUATED_AT,
        ),
        analytics=SubscriberRelativeAnalytics(
            eligible_standard_video_count=5,
            median_standard_video_vsr=median_vsr,
        ),
    )


class SignalEvidenceBuilderTests(TestCase):
    def setUp(self) -> None:
        self.builder = SignalEvidenceBuilder()

    def test_qualified_analysis_builds_complete_typed_bundle(self) -> None:
        analysis = _analysis()

        bundle = self.builder.build(analysis)

        self.assertTrue(bundle.qualification.value)
        self.assertEqual(bundle.qualification.failures, ())
        self.assertEqual(bundle.qualification.policy_version, 1)
        self.assertIs(
            bundle.eligible_sample.metric,
            MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
        )
        self.assertEqual(bundle.eligible_sample.value, 5)
        self.assertIs(bundle.eligible_sample.unit, EvidenceUnit.COUNT)
        self.assertIs(
            bundle.subscriber.value, SubscriberState.AVAILABLE_POSITIVE
        )
        self.assertEqual(bundle.requested_id_resolution.value, 1.0)
        self.assertEqual(bundle.median_standard_video_vsr.value, 2.5)

    def test_unqualified_analysis_preserves_accumulated_failures(self) -> None:
        failures = (
            QualificationFailureReason.ACQUISITION_TRUNCATED,
            QualificationFailureReason.SUBSCRIBER_COUNT_HIDDEN,
            QualificationFailureReason.INSUFFICIENT_ELIGIBLE_STANDARD_VIDEOS,
        )
        analysis = _analysis(
            failures=failures,
            subscriber_state=SubscriberState.HIDDEN,
            median_vsr=None,
        )

        bundle = self.builder.build(analysis)

        self.assertFalse(bundle.qualification.value)
        self.assertEqual(bundle.qualification.failures, failures)
        self.assertIs(bundle.subscriber.value, SubscriberState.HIDDEN)

    def test_unavailable_metric_values_are_explicit_and_not_fabricated(self) -> None:
        analysis = _analysis(
            resolution_rate=None,
            median_vsr=None,
            provenance=_provenance(requested=0, enriched=0),
        )

        bundle = self.builder.build(analysis)

        self.assertIsNone(bundle.requested_id_resolution.value)
        self.assertIs(
            bundle.requested_id_resolution.availability,
            EvidenceAvailability.UNAVAILABLE,
        )
        self.assertIsNone(bundle.median_standard_video_vsr.value)
        self.assertIs(
            bundle.median_standard_video_vsr.availability,
            EvidenceAvailability.UNAVAILABLE,
        )

    def test_builder_is_deterministic_and_does_not_modify_analysis(self) -> None:
        analysis = _analysis()
        before = analysis.model_dump()

        first = self.builder.build(analysis)
        second = self.builder.build(analysis)

        self.assertEqual(first, second)
        self.assertEqual(analysis.model_dump(), before)
        self.assertEqual(first.model_validate_json(first.model_dump_json()), first)

    def test_bundle_reuses_one_context_and_original_provenance_reference(self) -> None:
        analysis = _analysis()
        bundle = self.builder.build(analysis)
        contexts = (
            bundle.qualification.context,
            bundle.eligible_sample.context,
            bundle.subscriber.context,
            bundle.requested_id_resolution.context,
            bundle.median_standard_video_vsr.context,
        )

        self.assertTrue(all(context is contexts[0] for context in contexts))
        self.assertIs(
            contexts[0].provenance,
            analysis.qualification.provenance,
        )
        self.assertEqual(contexts[0].evaluated_at, _EVALUATED_AT)

    def test_bundle_and_nested_evidence_are_immutable(self) -> None:
        bundle = self.builder.build(_analysis())
        with self.assertRaises(ValidationError):
            bundle.eligible_sample = bundle.eligible_sample
        with self.assertRaises(ValidationError):
            bundle.eligible_sample.value = 6

    def test_metric_evidence_rejects_availability_that_contradicts_value(self) -> None:
        context = self.builder.build(_analysis()).eligible_sample.context
        with self.assertRaisesRegex(ValidationError, "availability"):
            MetricEvidence[int](
                metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                value=5,
                unit=EvidenceUnit.COUNT,
                availability=EvidenceAvailability.UNAVAILABLE,
                context=context,
            )


if __name__ == "__main__":
    import unittest

    unittest.main()
