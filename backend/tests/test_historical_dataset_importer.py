"""Tests for strict governed historical dataset import."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest import TestCase
from unittest.mock import patch

from pydantic import ValidationError

from app.services.analytics.models import SubscriberRelativeAnalytics
from app.services.analytics.qualification import (
    SubscriberRelativeAnalysisResult,
    SubscriberRelativeQualification,
    SubscriberState,
)
from app.services.backtesting import (
    HistoricalDatasetDuplicateError,
    HistoricalDatasetImporter,
    HistoricalDatasetImportResult,
    HistoricalDatasetManifest,
    HistoricalDatasetReadError,
    HistoricalDatasetSyntaxError,
    HistoricalDatasetValidationError,
    SubscriberRelativeBacktestObservation,
    UnsupportedHistoricalDatasetSchemaError,
)
from app.services.youtube.models import (
    AcquisitionSource,
    PaginationProvenance,
    PaginationStatus,
    VideoAcquisitionProvenance,
)

_OBSERVED_AT = datetime(2026, 7, 22, 12, tzinfo=UTC)


def _observation(
    observation_id: str,
    *,
    channel_id: str | None = None,
    observed_at: datetime = _OBSERVED_AT,
) -> SubscriberRelativeBacktestObservation:
    resolved_channel_id = channel_id or f"channel-{observation_id}"
    provenance = VideoAcquisitionProvenance(
        source=AcquisitionSource.UPLOADS_PLAYLIST,
        source_channel_id=resolved_channel_id,
        discovery_request_capacity=5,
        discovered_position_count=5,
        discovered_unique_video_count=5,
        enrichment_requested_unique_count=5,
        enriched_unique_video_count=5,
        enriched_output_position_count=5,
        omitted_unique_video_count=0,
        pagination=PaginationProvenance(
            status=PaginationStatus.COMPLETE,
            pages_fetched=1,
            page_size_requested=5,
            page_limit=1,
            next_page_token_present=False,
        ),
    )
    analysis = SubscriberRelativeAnalysisResult(
        qualification=SubscriberRelativeQualification(
            qualified=True,
            failures=(),
            provenance=provenance,
            requested_id_resolution_rate=1.0,
            eligible_standard_video_count=5,
            subscriber_state=SubscriberState.AVAILABLE_POSITIVE,
            evaluated_at=observed_at,
        ),
        analytics=SubscriberRelativeAnalytics(
            eligible_standard_video_count=5,
            median_standard_video_vsr=2.5,
        ),
    )
    return SubscriberRelativeBacktestObservation(
        observation_id=observation_id,
        channel_id=resolved_channel_id,
        observed_at=observed_at,
        subscriber_count=500,
        analysis=analysis,
    )


def _document(*observations: SubscriberRelativeBacktestObservation) -> dict[str, object]:
    return {
        "manifest": {
            "schema_version": 1,
            "dataset_id": "research-dataset-v1",
            "dataset_version": 1,
        },
        "observations": [
            observation.model_dump(mode="json") for observation in observations
        ],
    }


def _json(*observations: SubscriberRelativeBacktestObservation) -> str:
    return json.dumps(_document(*observations), separators=(",", ":"), sort_keys=True)


class HistoricalDatasetImporterTests(TestCase):
    def setUp(self) -> None:
        self.importer = HistoricalDatasetImporter()

    def test_valid_json_imports_immutable_manifest_and_dataset(self) -> None:
        result = self.importer.import_json(_json(_observation("observation-1")))

        self.assertIsInstance(result, HistoricalDatasetImportResult)
        self.assertEqual(result.manifest.schema_version, 1)
        self.assertEqual(result.dataset.dataset_id, "research-dataset-v1")
        self.assertEqual(result.dataset.version, 1)
        self.assertEqual(result.dataset.observations[0].observation_id, "observation-1")
        with self.assertRaises(ValidationError):
            result.dataset.version = 2
        with self.assertRaises(ValidationError):
            result.manifest.schema_version = 2

    def test_file_import_uses_the_same_contract(self) -> None:
        payload = _json(_observation("observation-1"))
        with patch(
            "app.services.backtesting.importer.Path.read_bytes",
            return_value=payload.encode("utf-8"),
        ) as read_bytes:
            from_file = self.importer.import_file("historical.json")

        read_bytes.assert_called_once_with()
        self.assertEqual(from_file, self.importer.import_json(payload))

    def test_unreadable_file_has_typed_error(self) -> None:
        with self.assertRaises(HistoricalDatasetReadError):
            self.importer.import_file("missing-historical-dataset.json")

    def test_invalid_json_has_typed_syntax_error(self) -> None:
        with self.assertRaisesRegex(HistoricalDatasetSyntaxError, "line 1, column"):
            self.importer.import_json('{"manifest":')

    def test_unknown_schema_version_is_rejected_separately(self) -> None:
        document = _document()
        manifest = document["manifest"]
        assert isinstance(manifest, dict)
        manifest["schema_version"] = 2

        with self.assertRaisesRegex(
            UnsupportedHistoricalDatasetSchemaError, "schema version: 2"
        ):
            self.importer.import_json(json.dumps(document))

    def test_missing_or_noninteger_schema_version_is_validation_failure(self) -> None:
        for value in (None, "1", True):
            with self.subTest(value=value):
                document = _document()
                manifest = document["manifest"]
                assert isinstance(manifest, dict)
                if value is None:
                    manifest.pop("schema_version")
                else:
                    manifest["schema_version"] = value
                with self.assertRaises(HistoricalDatasetValidationError):
                    self.importer.import_json(json.dumps(document))

    def test_missing_required_field_and_unknown_fields_are_not_ignored(self) -> None:
        missing = _document(_observation("observation-1"))
        missing.pop("observations")
        with self.assertRaisesRegex(
            HistoricalDatasetValidationError, "observations: Field required"
        ):
            self.importer.import_json(json.dumps(missing))

        unknown = _document(_observation("observation-1"))
        unknown["unexpected"] = "not permitted"
        with self.assertRaisesRegex(
            HistoricalDatasetValidationError, "Extra inputs are not permitted"
        ):
            self.importer.import_json(json.dumps(unknown))

        nested_unknown = _document(_observation("observation-1"))
        observations = nested_unknown["observations"]
        assert isinstance(observations, list)
        record = observations[0]
        assert isinstance(record, dict)
        analysis = record["analysis"]
        assert isinstance(analysis, dict)
        analytics = analysis["analytics"]
        assert isinstance(analytics, dict)
        analytics["unexpected_metric"] = 1
        with self.assertRaisesRegex(
            HistoricalDatasetValidationError,
            "observations.0.analysis.analytics.unexpected_metric",
        ):
            self.importer.import_json(json.dumps(nested_unknown))

    def test_invalid_timestamp_and_subscriber_count_are_not_coerced(self) -> None:
        for field, value in (
            ("observed_at", "not-a-timestamp"),
            ("subscriber_count", "500"),
            ("subscriber_count", 0),
        ):
            with self.subTest(field=field, value=value):
                document = _document(_observation("observation-1"))
                observations = document["observations"]
                assert isinstance(observations, list)
                record = observations[0]
                assert isinstance(record, dict)
                record[field] = value
                with self.assertRaises(HistoricalDatasetValidationError):
                    self.importer.import_json(json.dumps(document))

    def test_naive_timestamp_is_rejected(self) -> None:
        document = _document(_observation("observation-1"))
        observations = document["observations"]
        assert isinstance(observations, list)
        record = observations[0]
        assert isinstance(record, dict)
        record["observed_at"] = "2026-07-22T12:00:00"
        qualification = record["analysis"]
        assert isinstance(qualification, dict)
        qualification_value = qualification["qualification"]
        assert isinstance(qualification_value, dict)
        qualification_value["evaluated_at"] = "2026-07-22T12:00:00"

        with self.assertRaisesRegex(
            HistoricalDatasetValidationError, "timezone-aware"
        ):
            self.importer.import_json(json.dumps(document))

    def test_duplicate_observation_id_and_snapshot_have_typed_errors(self) -> None:
        duplicate_id = _json(
            _observation("observation-1", channel_id="channel-1"),
            _observation("observation-1", channel_id="channel-2"),
        )
        with self.assertRaisesRegex(
            HistoricalDatasetDuplicateError, "duplicate observation IDs"
        ):
            self.importer.import_json(duplicate_id)

        duplicate_snapshot = _json(
            _observation("observation-1", channel_id="channel-1"),
            _observation("observation-2", channel_id="channel-1"),
        )
        with self.assertRaisesRegex(
            HistoricalDatasetDuplicateError, "duplicate channel snapshots"
        ):
            self.importer.import_json(duplicate_snapshot)

    def test_observations_are_canonically_ordered_and_input_order_is_irrelevant(self) -> None:
        first = _observation("observation-1")
        second = _observation("observation-2")

        forward = self.importer.import_json(_json(first, second))
        reverse = self.importer.import_json(_json(second, first))

        self.assertEqual(forward, reverse)
        self.assertEqual(
            tuple(item.observation_id for item in forward.dataset.observations),
            ("observation-1", "observation-2"),
        )

    def test_import_result_serialization_round_trip_is_stable(self) -> None:
        result = self.importer.import_json(_json(_observation("observation-1")))
        serialized = result.model_dump_json()
        self.assertEqual(
            HistoricalDatasetImportResult.model_validate_json(serialized),
            result,
        )

    def test_manifest_rejects_invalid_identity_and_version(self) -> None:
        for values in (
            {"schema_version": 1, "dataset_id": "Invalid ID", "dataset_version": 1},
            {"schema_version": 1, "dataset_id": "research-v1", "dataset_version": 0},
        ):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                HistoricalDatasetManifest.model_validate(values)


if __name__ == "__main__":
    import unittest

    unittest.main()
