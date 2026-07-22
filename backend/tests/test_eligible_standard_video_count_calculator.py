"""Tests for the eligible standard-video count calculator."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from app.services.analytics.calculators.video.eligible_standard_video_count import (
    EligibleStandardVideoCountCalculator,
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


def _video(identifier: str) -> Video:
    return Video(id=identifier, channel_id="channel-1", title=identifier)


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


class EligibleStandardVideoCountCalculatorTests(TestCase):
    """Verify pure counting of a precomputed standard-video basis."""

    def setUp(self) -> None:
        self.calculator = EligibleStandardVideoCountCalculator()

    def test_zero_eligible_standard_videos(self) -> None:
        result = self.calculator.calculate(_classification())

        self.assertEqual(result.value, 0)

    def test_one_eligible_standard_video(self) -> None:
        result = self.calculator.calculate(
            _classification(standard_videos=(_video("standard-1"),))
        )

        self.assertEqual(result.value, 1)

    def test_multiple_eligible_standard_videos(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(
                    _video("standard-1"),
                    _video("standard-2"),
                    _video("standard-3"),
                )
            )
        )

        self.assertEqual(result.value, 3)

    def test_shorts_do_not_affect_count(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(_video("standard"),),
                shorts=(_video("short-1"), _video("short-2")),
            )
        )

        self.assertEqual(result.value, 1)

    def test_livestream_replays_do_not_affect_count(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(_video("standard"),),
                livestream_replays=(_video("replay-1"), _video("replay-2")),
            )
        )

        self.assertEqual(result.value, 1)

    def test_exclusions_do_not_affect_count(self) -> None:
        result = self.calculator.calculate(
            _classification(
                standard_videos=(_video("standard"),),
                exclusions=(
                    VideoExclusion(
                        video_id="excluded",
                        reason=VideoExclusionReason.UNKNOWN_FORMAT,
                    ),
                ),
            )
        )

        self.assertEqual(result.value, 1)

    def test_only_excluded_videos_returns_zero(self) -> None:
        result = self.calculator.calculate(
            _classification(
                exclusions=(
                    VideoExclusion(
                        video_id="excluded",
                        reason=VideoExclusionReason.UNAVAILABLE,
                    ),
                )
            )
        )

        self.assertEqual(result.value, 0)

    def test_metric_identity_and_value_type(self) -> None:
        result = self.calculator.calculate(
            _classification(standard_videos=(_video("standard"),))
        )

        self.assertIs(
            self.calculator.metric,
            MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
        )
        self.assertIs(result.metric, self.calculator.metric)
        self.assertIs(type(result.value), int)

    def test_output_equals_standard_metric_result(self) -> None:
        classification = _classification(
            standard_videos=(_video("standard-1"), _video("standard-2"))
        )

        result = self.calculator.calculate(classification)

        self.assertEqual(
            result,
            MetricResult[int](
                metric=MetricType.ELIGIBLE_STANDARD_VIDEO_COUNT,
                value=2,
            ),
        )

    def test_repeated_execution_is_deterministic(self) -> None:
        classification = _classification(
            standard_videos=(_video("standard-1"), _video("standard-2"))
        )

        first = self.calculator.calculate(classification)
        second = self.calculator.calculate(classification)

        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_input_remains_unchanged(self) -> None:
        classification = _classification(
            standard_videos=(_video("standard-1"), _video("standard-2")),
            shorts=(_video("short"),),
            livestream_replays=(_video("replay"),),
            exclusions=(
                VideoExclusion(
                    video_id="excluded",
                    reason=VideoExclusionReason.UNKNOWN_FORMAT,
                ),
            ),
        )
        original = classification.model_copy(deep=True)

        self.calculator.calculate(classification)

        self.assertEqual(classification, original)

    def test_none_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsValidationError,
            "eligible video classification is required",
        ):
            self.calculator.calculate(None)  # type: ignore[arg-type]

    def test_incorrect_input_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            AnalyticsValidationError,
            "must be EligibleVideoClassification",
        ):
            self.calculator.calculate(object())  # type: ignore[arg-type]

    def test_malformed_standard_video_basis_is_rejected(self) -> None:
        malformed = EligibleVideoClassification.model_construct(
            eligible_standard_videos=[_video("standard")],
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
            self.calculator.calculate(malformed)
