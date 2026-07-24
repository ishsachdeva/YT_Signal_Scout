"""Tests for immutable governed ground-truth label artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest import TestCase
from unittest.mock import patch

from pydantic import ValidationError

from app.services.backtesting import (
    AdjudicatedLabelDecision,
    GroundTruthLabel,
    GroundTruthLabelArtifact,
    GroundTruthLabelCanonicalizer,
    GroundTruthLabelDigestMismatchError,
    GroundTruthLabelDuplicateError,
    GroundTruthLabelImporter,
    GroundTruthLabelImportResult,
    GroundTruthLabelReadError,
    GroundTruthLabelSet,
    GroundTruthLabelSetManifest,
    GroundTruthLabelSyntaxError,
    GroundTruthLabelValidationError,
    IndependentLabelReview,
    LabelContentDigest,
    LabelEvidenceReference,
    LabelReviewerIdentity,
    SupersededLabelArtifactReference,
    UnsupportedGroundTruthLabelSchemaError,
)

_REVIEWED_AT = datetime(2026, 7, 24, 10, tzinfo=UTC)
_CREATED_AT = datetime(2026, 7, 24, 12, tzinfo=UTC)


def _digest(value: str = "a") -> LabelContentDigest:
    return LabelContentDigest(algorithm="sha256", value=value * 64)


def _review(
    review_id: str,
    reviewer_id: str,
    label: GroundTruthLabel,
    *,
    reviewed_at: datetime = _REVIEWED_AT,
) -> IndependentLabelReview:
    return IndependentLabelReview(
        review_id=review_id,
        reviewer=LabelReviewerIdentity(reviewer_id=reviewer_id),
        reviewed_at=reviewed_at,
        label=label,
        reason_code="rubric-reason",
        reasoning_notes="Permitted evidence supports this research label.",
    )


def _artifact(
    artifact_id: str = "artifact-1",
    observation_id: str = "observation-1",
    channel_id: str = "channel-1",
    *,
    first_label: GroundTruthLabel = GroundTruthLabel.POSITIVE,
    second_label: GroundTruthLabel = GroundTruthLabel.POSITIVE,
    reverse_reviews: bool = False,
) -> GroundTruthLabelArtifact:
    reviews = (
        _review("review-1", "reviewer-1", first_label),
        _review("review-2", "reviewer-2", second_label),
    )
    if reverse_reviews:
        reviews = tuple(reversed(reviews))
    adjudication = None
    final_label = first_label
    if first_label is not second_label:
        final_label = GroundTruthLabel.BORDERLINE
        adjudication = AdjudicatedLabelDecision(
            adjudication_id="adjudication-1",
            adjudicator=LabelReviewerIdentity(reviewer_id="adjudicator-1"),
            adjudicated_at=_REVIEWED_AT + timedelta(hours=1),
            label=final_label,
            reason_code="adjudication-reason",
            reasoning_notes="The same evidence was ambiguous under the rubric.",
        )
    return GroundTruthLabelArtifact(
        artifact_id=artifact_id,
        artifact_version=1,
        label_set_id="label-set-v1",
        label_set_version=1,
        dataset_id="research-dataset-v1",
        dataset_version=1,
        observation_id=observation_id,
        channel_id=channel_id,
        evidence=LabelEvidenceReference(
            evidence_pack_definition_id="evidence-pack-definition-v1",
            evidence_pack_definition_version=1,
            evidence_pack_id="evidence-pack-v1",
            evidence_pack_version=1,
            evidence_pack_digest=_digest("b"),
            rubric_id="label-rubric-v1",
            rubric_version=1,
            rubric_digest=_digest("c"),
        ),
        independent_reviews=reviews,
        adjudication=adjudication,
        final_label=final_label,
    )


def _manifest() -> GroundTruthLabelSetManifest:
    return GroundTruthLabelSetManifest(
        schema_version=1,
        label_set_id="label-set-v1",
        label_set_version=1,
        dataset_id="research-dataset-v1",
        dataset_version=1,
        created_at=_CREATED_AT,
        creator_identity="analytics-owner",
        digest=_digest("0"),
    )


def _document(*artifacts: GroundTruthLabelArtifact) -> dict[str, object]:
    manifest = _manifest()
    digest = GroundTruthLabelCanonicalizer.calculate_digest(manifest, artifacts)
    manifest = manifest.model_copy(
        update={"digest": LabelContentDigest(algorithm="sha256", value=digest)}
    )
    return {
        "manifest": manifest.model_dump(mode="json"),
        "artifacts": [artifact.model_dump(mode="json") for artifact in artifacts],
    }


class GroundTruthLabelTests(TestCase):
    def setUp(self) -> None:
        self.importer = GroundTruthLabelImporter()

    def test_only_protocol_defined_labels_exist(self) -> None:
        self.assertEqual(
            tuple(GroundTruthLabel),
            (
                GroundTruthLabel.POSITIVE,
                GroundTruthLabel.NEGATIVE,
                GroundTruthLabel.BORDERLINE,
                GroundTruthLabel.UNKNOWN,
            ),
        )

    def test_valid_document_imports_immutable_dataset_bound_label_set(self) -> None:
        result = self.importer.import_json(json.dumps(_document(_artifact())))

        self.assertIsInstance(result, GroundTruthLabelImportResult)
        self.assertEqual(result.label_set.dataset_id, "research-dataset-v1")
        self.assertEqual(result.label_set.artifacts[0].final_label, GroundTruthLabel.POSITIVE)
        with self.assertRaises(ValidationError):
            result.label_set.version = 2

    def test_matching_reviews_define_final_label_without_adjudication(self) -> None:
        artifact = _artifact(
            first_label=GroundTruthLabel.NEGATIVE,
            second_label=GroundTruthLabel.NEGATIVE,
        )

        self.assertEqual(artifact.final_label, GroundTruthLabel.NEGATIVE)
        self.assertIsNone(artifact.adjudication)

    def test_disagreement_requires_independent_adjudication(self) -> None:
        artifact = _artifact(
            first_label=GroundTruthLabel.POSITIVE,
            second_label=GroundTruthLabel.NEGATIVE,
        )
        self.assertEqual(artifact.final_label, GroundTruthLabel.BORDERLINE)

        for updates, message in (
            ({"adjudication": None}, "require adjudication"),
            (
                {
                    "adjudication": artifact.adjudication.model_copy(
                        update={
                            "adjudicator": LabelReviewerIdentity(
                                reviewer_id="reviewer-1"
                            )
                        }
                    )
                },
                "independent from label reviewers",
            ),
            (
                {
                    "adjudication": artifact.adjudication.model_copy(
                        update={"adjudicated_at": _REVIEWED_AT - timedelta(seconds=1)}
                    )
                },
                "cannot precede",
            ),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(
                ValidationError, message
            ):
                GroundTruthLabelArtifact.model_validate(
                    {**artifact.model_dump(), **updates}
                )

    def test_exactly_two_unique_independent_reviewers_are_required(self) -> None:
        artifact = _artifact()
        cases = (
            artifact.independent_reviews[:1],
            (
                artifact.independent_reviews[0],
                artifact.independent_reviews[1].model_copy(
                    update={"reviewer": artifact.independent_reviews[0].reviewer}
                ),
            ),
        )
        for reviews in cases:
            with self.subTest(reviews=reviews), self.assertRaises(ValidationError):
                GroundTruthLabelArtifact.model_validate(
                    {**artifact.model_dump(), "independent_reviews": reviews}
                )

    def test_replacement_artifact_requires_version_history(self) -> None:
        first = _artifact()
        replacement = GroundTruthLabelArtifact(
            **{
                **first.model_dump(exclude={"supersedes", "change_reason"}),
                "artifact_version": 2,
                "label_set_version": 2,
                "supersedes": SupersededLabelArtifactReference(
                    label_set_id=first.label_set_id,
                    label_set_version=1,
                    artifact_id=first.artifact_id,
                    artifact_version=1,
                ),
                "change_reason": "Corrected a documented rubric application error.",
            }
        )

        self.assertEqual(replacement.supersedes.artifact_version, 1)
        with self.assertRaisesRegex(ValidationError, "requires history"):
            GroundTruthLabelArtifact.model_validate(
                {
                    **replacement.model_dump(),
                    "supersedes": None,
                    "change_reason": None,
                }
            )

    def test_import_is_canonically_ordered_and_input_order_independent(self) -> None:
        first = _artifact("artifact-1", "observation-1", "channel-1")
        second = _artifact("artifact-2", "observation-2", "channel-2", reverse_reviews=True)
        forward = self.importer.import_json(json.dumps(_document(first, second)))
        reverse = self.importer.import_json(json.dumps(_document(second, first)))

        self.assertEqual(forward, reverse)
        self.assertEqual(
            tuple(item.observation_id for item in forward.label_set.artifacts),
            ("observation-1", "observation-2"),
        )
        self.assertEqual(
            tuple(
                item.review_id
                for item in forward.label_set.artifacts[1].independent_reviews
            ),
            ("review-1", "review-2"),
        )

        with self.assertRaisesRegex(ValidationError, "canonically ordered"):
            GroundTruthLabelSet(
                label_set_id=forward.label_set.label_set_id,
                version=forward.label_set.version,
                dataset_id=forward.label_set.dataset_id,
                dataset_version=forward.label_set.dataset_version,
                artifacts=tuple(reversed(forward.label_set.artifacts)),
            )

    def test_canonical_serialization_round_trip_is_stable(self) -> None:
        result = self.importer.import_json(json.dumps(_document(_artifact())))
        canonical = GroundTruthLabelCanonicalizer.serialize_import_result(result)

        self.assertEqual(self.importer.import_json(canonical), result)
        self.assertEqual(
            GroundTruthLabelCanonicalizer.serialize_import_result(
                self.importer.import_json(canonical)
            ),
            canonical,
        )

    def test_tampering_with_label_or_evidence_is_rejected_by_digest(self) -> None:
        for target in ("label", "evidence"):
            with self.subTest(target=target):
                document = _document(_artifact())
                artifacts = document["artifacts"]
                assert isinstance(artifacts, list)
                artifact = artifacts[0]
                assert isinstance(artifact, dict)
                if target == "label":
                    artifact["final_label"] = "negative"
                else:
                    evidence = artifact["evidence"]
                    assert isinstance(evidence, dict)
                    evidence["evidence_pack_version"] = 2
                with self.assertRaises(
                    (GroundTruthLabelValidationError, GroundTruthLabelDigestMismatchError)
                ):
                    self.importer.import_json(json.dumps(document))

    def test_duplicate_artifact_observation_and_channel_identities_are_rejected(self) -> None:
        cases = (
            (_artifact(), _artifact()),
            (_artifact(), _artifact("artifact-2", "observation-1", "channel-2")),
            (_artifact(), _artifact("artifact-2", "observation-2", "channel-1")),
        )
        for artifacts in cases:
            with self.subTest(artifacts=artifacts), self.assertRaises(
                GroundTruthLabelDuplicateError
            ):
                self.importer.import_json(json.dumps(_document(*artifacts)))

    def test_artifacts_must_share_manifest_and_evidence_definition_bindings(self) -> None:
        first = _artifact()
        second = _artifact("artifact-2", "observation-2", "channel-2")
        mismatches = (
            second.model_copy(update={"dataset_version": 2}),
            second.model_copy(
                update={
                    "evidence": second.evidence.model_copy(
                        update={"rubric_version": 2}
                    )
                }
            ),
            second.model_copy(
                update={
                    "evidence": second.evidence.model_copy(
                        update={"evidence_pack_definition_version": 2}
                    )
                }
            ),
        )
        for mismatch in mismatches:
            with self.subTest(mismatch=mismatch), self.assertRaises(
                GroundTruthLabelValidationError
            ):
                self.importer.import_json(json.dumps(_document(first, mismatch)))

    def test_label_set_creation_cannot_precede_review_or_adjudication(self) -> None:
        document = _document(
            _artifact(
                first_label=GroundTruthLabel.POSITIVE,
                second_label=GroundTruthLabel.NEGATIVE,
            )
        )
        manifest = document["manifest"]
        assert isinstance(manifest, dict)
        manifest["created_at"] = "2026-07-24T10:30:00Z"

        with self.assertRaisesRegex(
            GroundTruthLabelValidationError, "occurs after set creation"
        ):
            self.importer.import_json(json.dumps(document))

    def test_strict_schema_unknown_fields_and_timestamps_are_rejected(self) -> None:
        cases = []
        unknown = _document(_artifact())
        unknown["unexpected"] = True
        cases.append(unknown)
        invalid_time = _document(_artifact())
        manifest = invalid_time["manifest"]
        assert isinstance(manifest, dict)
        manifest["created_at"] = "2026-07-24T12:00:00"
        cases.append(invalid_time)
        invalid_label = _document(_artifact())
        artifacts = invalid_label["artifacts"]
        assert isinstance(artifacts, list)
        artifact = artifacts[0]
        assert isinstance(artifact, dict)
        artifact["final_label"] = "approved"
        cases.append(invalid_label)

        for document in cases:
            with self.subTest(document=document), self.assertRaises(
                GroundTruthLabelValidationError
            ):
                self.importer.import_json(json.dumps(document))

    def test_typed_read_syntax_and_schema_failures(self) -> None:
        with self.assertRaises(GroundTruthLabelReadError):
            self.importer.import_file("missing-ground-truth-labels.json")
        with self.assertRaises(GroundTruthLabelSyntaxError):
            self.importer.import_json('{"manifest":')

        document = _document(_artifact())
        manifest = document["manifest"]
        assert isinstance(manifest, dict)
        manifest["schema_version"] = 2
        with self.assertRaises(UnsupportedGroundTruthLabelSchemaError):
            self.importer.import_json(json.dumps(document))

    def test_file_import_uses_same_contract(self) -> None:
        payload = json.dumps(_document(_artifact())).encode("utf-8")
        with patch(
            "app.services.backtesting.label_importer.Path.read_bytes",
            return_value=payload,
        ) as read_bytes:
            imported = self.importer.import_file("labels.json")

        read_bytes.assert_called_once_with()
        self.assertEqual(imported, self.importer.import_json(payload))

    def test_label_artifacts_contain_no_threshold_or_runtime_decision(self) -> None:
        fields = GroundTruthLabelArtifact.model_fields
        for prohibited in (
            "threshold",
            "precision",
            "recall",
            "f1",
            "ranking",
            "signal",
            "production_approved",
        ):
            self.assertNotIn(prohibited, fields)
