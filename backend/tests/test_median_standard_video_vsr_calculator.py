"""Tests for the median standard-video VSR calculator."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from app.services.analytics.calculators.video.median_standard_video_vsr import (
    MedianStandardVideoVsrCalculator,
)
from app.services.analytics.eligibility import (
    EligibleVideoClassification,
    VideoExclusion,
    VideoExclusionReason,
)
from app.services.analytics.exceptions import AnalyticsValidationError
from app.services.analytics.models import MetricResult, MetricType
from app.services.youtube.models import Video

_EVALUATED_AT = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _video(identifier: str, view_count: int | None) -> Video:
    return Video(
        id=identifier,
        channel_id="channel-1",
        title=identifier,
        view_count=view_count,
    )


def _classification(
    *,
    standard_videos: tuple[Video, ...] = (),
    shorts: tuple[Video, ...] = (),
    livestream_replays: tuple[Video, ...] = (),
    exclusions: tuple[VideoExclusion, ...] = (),
) -> EligibleVideoClassification:
    return EligibleVideoClassification(
        eligible_standard_videos=standard_videos,
        eligible_shorts=shorts,
        eligible_livestream_replays=livestream_replays,
        exclusions=exclusions,
        evaluated_at=_EVALUATED_AT,
    )


class MedianStandardVideoVsrCalculatorTests(TestCase):
    """Verify pure median calculation from a precomputed standard basis."""

    def setUp(self) -> None:
        self.calculator = MedianStandardVideoVsrCalculator()

    def test_empty_eligible_basis_returns_none(self) -> None:
        result = self.calculator.calculate(_classification(), 100)

        self.assertIsNone(result.value)

    def test_one_video(self) -> None:
        result = self.calculator.calculate(
            _classification(standard_videos=(_video("video-1", 250),)),
            100,
        )

        self.assertEqual(result.value, 2.5)

    def test_odd_number_of_videos(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(
                    _video("video-1", 100),
                    _video("video-2", 300),
                    _video("video-3", 200),
                )
            ),
            100,
        )

        self.assertEqual(result.value, 2.0)

    def test_even_number_of_videos(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(
                    _video("video-1", 100),
                    _video("video-2", 400),
                    _video("video-3", 200),
                    _video("video-4", 300),
                )
            ),
            100,
        )

        self.assertEqual(result.value, 2.5)

    def test_identical_vsr_values(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(
                    _video("video-1", 125),
                    _video("video-2", 125),
                    _video("video-3", 125),
                )
            ),
            100,
        )

        self.assertEqual(result.value, 1.25)

    def test_unsorted_inputs_do_not_change_statistical_median(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(
                    _video("video-1", 500),
                    _video("video-2", 100),
                    _video("video-3", 300),
                )
            ),
            100,
        )

        self.assertEqual(result.value, 3.0)

    def test_result_is_not_rounded(self) -> None:
        result = self.calculator.calculate(
            _classification(standard_videos=(_video("video-1", 1),)),
            3,
        )

        self.assertEqual(result.value, 1 / 3)

    def test_non_standard_bases_and_exclusions_are_ignored(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(_video("standard", 200),),
                shorts=(_video("short", 100_000),),
                livestream_replays=(_video("replay", 200_000),),
                exclusions=(
                    VideoExclusion(
                        video_id="excluded",
                        reason=VideoExclusionReason.UNKNOWN_FORMAT,
                    ),
                ),
            ),
            100,
        )

        self.assertEqual(result.value, 2.0)

    def test_zero_subscriber_count_returns_none(self) -> None:
        result = self.calculator.calculate(
            _classification(standard_videos=(_video("video-1", 100),)),
            0,
        )

        self.assertIsNone(result.value)

    def test_missing_subscriber_count_returns_none(self) -> None:
        result = self.calculator.calculate(
            _classification(standard_videos=(_video("video-1", 100),)),
            None,
        )

        self.assertIsNone(result.value)

    def test_invalid_subscriber_count_is_rejected(self) -> None:
        classification = _classification(
            standard_videos=(_video("video-1", 100),)
        )

        for subscriber_count in (-1, 1.5, True):
            with self.subTest(subscriber_count=subscriber_count):
                with self.assertRaises(AnalyticsValidationError):
                    self.calculator.calculate(
                        classification,
                        subscriber_count,  # type: ignore[arg-type]
                    )

    def test_none_and_incorrect_classification_are_rejected(self) -> None:
        for classification in (None, object()):
            with self.subTest(classification=classification):
                with self.assertRaises(AnalyticsValidationError):
                    self.calculator.calculate(
                        classification,  # type: ignore[arg-type]
                        100,
                    )

    def test_malformed_standard_video_basis_is_rejected(self) -> None:
        malformed = EligibleVideoClassification.model_construct(
            eligible_standard_videos=[_video("video-1", 100)],
            eligible_shorts=(),
            eligible_livestream_replays=(),
            exclusions=(),
            evaluated_at=_EVALUATED_AT,
            policy_version=1,
        )

        with self.assertRaisesRegex(
            AnalyticsValidationError,
            "must be a tuple of Video objects",
        ):
            self.calculator.calculate(malformed, 100)

    def test_malformed_video_view_counts_are_rejected(self) -> None:
        cases = (
            _video("missing", None),
            _video("negative", -1),
            _video("boolean", 1).model_copy(update={"view_count": True}),
            _video("decimal", 1).model_copy(update={"view_count": 1.5}),
        )

        for video in cases:
            with self.subTest(video_id=video.id):
                with self.assertRaises(AnalyticsValidationError):
                    self.calculator.calculate(
                        _classification(standard_videos=(video,)),
                        100,
                    )

    def test_metric_identity_and_output_equality(self) -> None:
        classification = _classification(
            standard_videos=(_video("video-1", 100), _video("video-2", 300))
        )

        result = self.calculator.calculate(classification, 100)

        self.assertIs(self.calculator.metric, MetricType.MEDIAN_STANDARD_VIDEO_VSR)
        self.assertEqual(
            result,
            MetricResult[float | None](
                metric=MetricType.MEDIAN_STANDARD_VIDEO_VSR,
                value=2.0,
            ),
        )

    def test_repeated_execution_is_deterministic(self) -> None:
        classification = _classification(
            standard_videos=(_video("video-1", 100), _video("video-2", 300))
        )

        first = self.calculator.calculate(classification, 100)
        second = self.calculator.calculate(classification, 100)

        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_input_remains_unchanged(self) -> None:
        classification = _classification(
            standard_videos=(_video("video-1", 100), _video("video-2", 300)),
            shorts=(_video("short", 500),),
        )
        original = classification.model_copy(deep=True)

        self.calculator.calculate(classification, 100)

        self.assertEqual(classification, original)
