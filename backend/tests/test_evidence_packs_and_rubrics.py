"""Tests for immutable reviewer evidence packs and labelling rubrics."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest import TestCase

from pydantic import ValidationError

from app.services.backtesting import (
    EVIDENCE_PACK_SCHEMA_VERSION,
    LABELLING_RUBRIC_SCHEMA_VERSION,
    EvidenceFact,
    EvidenceFactDefinition,
    EvidenceItem,
    EvidenceItemDefinition,
    EvidencePack,
    EvidencePackCanonicalizer,
    EvidencePackDefinition,
    EvidencePackDigestMismatchError,
    EvidencePackDocument,
    EvidencePackImporter,
    EvidenceReference,
    EvidencePackValidationError,
    EvidenceSnapshot,
    EvidenceValueType,
    GroundTruthLabel,
    GroundTruthLabelBindingError,
    GroundTruthLabelBindingValidator,
    LabelContentDigest,
    RubricCanonicalizer,
    RubricCriterion,
    RubricDecisionRule,
    RubricDefinition,
    RubricDigestMismatchError,
    RubricDocument,
    RubricImporter,
    RubricVersion,
    RubricReasonCode,
)
from tests.test_ground_truth_labels import _artifact


def test_public_reference_and_version_contracts_are_exported() -> None:
    assert EvidenceReference.__name__ == "LabelEvidenceReference"
    assert RubricVersion is not None

_OBSERVED_AT = datetime(2026, 7, 24, 10, tzinfo=UTC)
_CREATED_AT = datetime(2026, 7, 24, 12, tzinfo=UTC)


def _digest(value: str = "0") -> LabelContentDigest:
    return LabelContentDigest(algorithm="sha256", value=value * 64)


def _definition() -> EvidencePackDefinition:
    provisional = EvidencePackDefinition(
        definition_id="evidence-pack-definition-v1",
        version=1,
        name="SIG-002 ground-truth evidence",
        purpose="Define factual evidence visible during independent labelling.",
        created_at=_CREATED_AT,
        item_definitions=(
            EvidenceItemDefinition(
                item_id="snapshot-facts",
                title="Snapshot facts",
                description="Timestamp and eligible-video public views.",
                required=True,
                fact_definitions=(
                    EvidenceFactDefinition(
                        fact_name="snapshot-timestamp",
                        value_type=EvidenceValueType.TIMESTAMP,
                        required=True,
                        repeatable=False,
                        semantic_unit="utc-timestamp",
                        description="Historical observation time.",
                    ),
                    EvidenceFactDefinition(
                        fact_name="video-view-count",
                        value_type=EvidenceValueType.INTEGER,
                        required=True,
                        repeatable=True,
                        semantic_unit="public-views",
                        description="Public views for one eligible video.",
                    ),
                ),
            ),
        ),
        digest=_digest(),
    )
    value = EvidencePackCanonicalizer.calculate_definition_digest(provisional)
    return provisional.model_copy(
        update={"digest": LabelContentDigest(algorithm="sha256", value=value)}
    )


def _pack(definition: EvidencePackDefinition | None = None) -> EvidencePack:
    definition = definition or _definition()
    provisional = EvidencePack(
        evidence_pack_id="evidence-pack-v1",
        version=1,
        definition_id=definition.definition_id,
        definition_version=definition.version,
        definition_digest=definition.digest,
        created_at=_CREATED_AT,
        snapshot=EvidenceSnapshot(
            snapshot_id="evidence-snapshot-v1",
            snapshot_version=1,
            dataset_id="research-dataset-v1",
            dataset_version=1,
            observation_id="observation-1",
            channel_id="channel-1",
            observed_at=_OBSERVED_AT,
        ),
        items=(
            EvidenceItem(
                item_id="snapshot-facts",
                facts=(
                    EvidenceFact(
                        fact_name="snapshot-timestamp",
                        value_type=EvidenceValueType.TIMESTAMP,
                        value=_OBSERVED_AT,
                        semantic_unit="utc-timestamp",
                    ),
                    EvidenceFact(
                        fact_name="video-view-count",
                        subject_id="video-1",
                        value_type=EvidenceValueType.INTEGER,
                        value=500,
                        semantic_unit="public-views",
                    ),
                ),
            ),
        ),
        digest=_digest(),
    )
    value = EvidencePackCanonicalizer.calculate_pack_digest(provisional)
    return provisional.model_copy(
        update={"digest": LabelContentDigest(algorithm="sha256", value=value)}
    )


def _evidence_document() -> EvidencePackDocument:
    definition = _definition()
    return EvidencePackDocument(
        schema_version=EVIDENCE_PACK_SCHEMA_VERSION,
        definition=definition,
        pack=_pack(definition),
    )


def _rubric(definition: EvidencePackDefinition | None = None) -> RubricDefinition:
    definition = definition or _definition()
    reason = RubricReasonCode(
        reason_code="rubric-reason",
        allowed_labels=tuple(GroundTruthLabel),
        description="Permitted evidence supports the selected research label.",
    )
    provisional = RubricDefinition(
        rubric_id="label-rubric-v1",
        version=1,
        name="SIG-002 ground-truth rubric",
        purpose="Govern independent interpretation without deciding labels automatically.",
        created_at=_CREATED_AT,
        evidence_pack_definition_id=definition.definition_id,
        evidence_pack_definition_version=definition.version,
        evidence_pack_definition_digest=definition.digest,
        criteria=(
            RubricCriterion(
                criterion_id="inspect-snapshot",
                description="Inspect the defined snapshot facts.",
                required=True,
                evidence_item_ids=("snapshot-facts",),
            ),
        ),
        allowed_decision_states=tuple(GroundTruthLabel),
        reason_codes=(reason,),
        decision_rules=tuple(
            RubricDecisionRule(
                rule_id=f"{label.value}-rule",
                label=label,
                description=f"Human guidance for the {label.value} research state.",
                permitted_reason_codes=(reason.reason_code,),
            )
            for label in GroundTruthLabel
        ),
        digest=_digest(),
    )
    document = RubricDocument(
        schema_version=LABELLING_RUBRIC_SCHEMA_VERSION,
        rubric=provisional,
    )
    value = RubricCanonicalizer.calculate_digest(document)
    return provisional.model_copy(
        update={"digest": LabelContentDigest(algorithm="sha256", value=value)}
    )


def _rubric_document() -> RubricDocument:
    return RubricDocument(
        schema_version=LABELLING_RUBRIC_SCHEMA_VERSION,
        rubric=_rubric(),
    )


class EvidencePackAndRubricTests(TestCase):
    def test_evidence_import_is_immutable_strict_and_canonical(self) -> None:
        importer = EvidencePackImporter()
        payload = json.dumps(_evidence_document().model_dump(mode="json"))
        result = importer.import_json(payload)
        canonical = EvidencePackCanonicalizer.serialize_import_result(result)

        self.assertEqual(importer.import_json(canonical), result)
        self.assertEqual(
            EvidencePackCanonicalizer.serialize_import_result(importer.import_json(canonical)),
            canonical,
        )
        with self.assertRaises(ValidationError):
            result.document.pack.version = 2

    def test_evidence_pack_requires_exact_definition_items_facts_types_and_units(self) -> None:
        document = _evidence_document().model_dump(mode="json")
        cases = (
            ("item", "different-item"),
            ("fact", "unknown-fact"),
            ("type", "text"),
            ("unit", "subscribers"),
        )
        for case, value in cases:
            with self.subTest(case=case):
                changed = json.loads(json.dumps(document))
                if case == "item":
                    changed["pack"]["items"][0]["item_id"] = value
                elif case == "fact":
                    changed["pack"]["items"][0]["facts"][0]["fact_name"] = value
                elif case == "type":
                    changed["pack"]["items"][0]["facts"][0]["value_type"] = value
                    changed["pack"]["items"][0]["facts"][0]["value"] = "text"
                else:
                    changed["pack"]["items"][0]["facts"][0]["semantic_unit"] = value
                with self.assertRaises(
                    (EvidencePackValidationError, EvidencePackDigestMismatchError)
                ):
                    EvidencePackImporter().import_json(json.dumps(changed))

    def test_evidence_definition_and_pack_tampering_fail_digest_validation(self) -> None:
        for target in ("definition", "pack"):
            with self.subTest(target=target):
                document = _evidence_document().model_dump(mode="json")
                document[target]["created_at"] = "2026-07-24T13:00:00Z"
                with self.assertRaises(EvidencePackDigestMismatchError):
                    EvidencePackImporter().import_json(json.dumps(document))

    def test_evidence_fact_values_are_exactly_typed_and_timestamps_are_aware(self) -> None:
        base = _pack().items[0].facts[1].model_dump()
        for updates in (
            {"value": True},
            {"value_type": EvidenceValueType.FLOAT, "value": 500},
            {
                "fact_name": "timestamp",
                "value_type": EvidenceValueType.TIMESTAMP,
                "value": datetime(2026, 7, 24),
            },
        ):
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                EvidenceFact.model_validate({**base, **updates})

    def test_rubric_import_is_immutable_strict_and_canonical(self) -> None:
        importer = RubricImporter()
        payload = json.dumps(_rubric_document().model_dump(mode="json"))
        result = importer.import_json(payload)
        canonical = RubricCanonicalizer.serialize_import_result(result)

        self.assertEqual(importer.import_json(canonical), result)
        self.assertEqual(
            RubricCanonicalizer.serialize_import_result(importer.import_json(canonical)),
            canonical,
        )

    def test_rubric_requires_all_protocol_states_and_one_ordered_rule_per_state(self) -> None:
        rubric = _rubric()
        for updates in (
            {"allowed_decision_states": tuple(GroundTruthLabel)[:-1]},
            {"decision_rules": tuple(reversed(rubric.decision_rules))},
        ):
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                RubricDefinition.model_validate({**rubric.model_dump(), **updates})

    def test_rubric_rules_require_known_label_compatible_reason_codes(self) -> None:
        rubric = _rubric()
        first = rubric.decision_rules[0]
        cases = (
            first.model_copy(update={"permitted_reason_codes": ("missing",)}),
            first.model_copy(update={"label": GroundTruthLabel.NEGATIVE}),
        )
        for rule in cases:
            with self.subTest(rule=rule), self.assertRaises(ValidationError):
                RubricDefinition.model_validate(
                    {
                        **rubric.model_dump(),
                        "decision_rules": (rule, *rubric.decision_rules[1:]),
                    }
                )

    def test_rubric_tampering_fails_digest_validation(self) -> None:
        document = _rubric_document().model_dump(mode="json")
        document["rubric"]["purpose"] = "Tampered purpose"
        with self.assertRaises(RubricDigestMismatchError):
            RubricImporter().import_json(json.dumps(document))

    def test_label_binding_validates_exact_evidence_rubric_and_reason_codes(self) -> None:
        evidence = _evidence_document()
        rubric = _rubric(evidence.definition)
        artifact = _artifact().model_copy(
            update={
                "evidence": _artifact().evidence.model_copy(
                    update={
                        "evidence_pack_definition_digest": evidence.definition.digest,
                        "evidence_pack_digest": evidence.pack.digest,
                        "rubric_digest": rubric.digest,
                    }
                )
            }
        )

        GroundTruthLabelBindingValidator().validate(artifact, evidence, rubric)

        with self.assertRaises(GroundTruthLabelBindingError):
            GroundTruthLabelBindingValidator().validate(
                artifact.model_copy(update={"channel_id": "different-channel"}),
                evidence,
                rubric,
            )

    def test_contracts_contain_no_labels_outside_protocol_or_execution_outputs(self) -> None:
        self.assertEqual(tuple(GroundTruthLabel), tuple(_rubric().allowed_decision_states))
        for model in (EvidencePack, EvidencePackDefinition, RubricDefinition):
            for prohibited in (
                "threshold",
                "precision",
                "recall",
                "f1",
                "ranking",
                "decision_result",
            ):
                self.assertNotIn(prohibited, model.model_fields)
