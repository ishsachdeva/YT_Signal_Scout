"""Structural binding validation across labels, evidence packs, and rubrics."""

from __future__ import annotations

from app.services.backtesting.evidence_models import EvidencePackDocument
from app.services.backtesting.exceptions import GroundTruthLabelBindingError
from app.services.backtesting.label_models import GroundTruthLabel, GroundTruthLabelArtifact
from app.services.backtesting.rubric_models import RubricDefinition, RubricReasonCode


class GroundTruthLabelBindingValidator:
    """Validate supplied artifact references without deciding or changing a label."""

    def validate(
        self,
        artifact: GroundTruthLabelArtifact,
        evidence: EvidencePackDocument,
        rubric: RubricDefinition,
    ) -> None:
        """Fail when exact content identities or allowed reason codes do not bind."""
        reference = artifact.evidence
        pack = evidence.pack
        definition = evidence.definition
        bindings = (
            (
                reference.evidence_pack_definition_id,
                definition.definition_id,
                "evidence-pack definition ID",
            ),
            (
                reference.evidence_pack_definition_version,
                definition.version,
                "evidence-pack definition version",
            ),
            (reference.evidence_pack_id, pack.evidence_pack_id, "evidence-pack ID"),
            (reference.evidence_pack_version, pack.version, "evidence-pack version"),
            (reference.evidence_pack_digest, pack.digest, "evidence-pack digest"),
            (reference.rubric_id, rubric.rubric_id, "rubric ID"),
            (reference.rubric_version, rubric.version, "rubric version"),
            (reference.rubric_digest, rubric.digest, "rubric digest"),
            (artifact.dataset_id, pack.snapshot.dataset_id, "dataset ID"),
            (artifact.dataset_version, pack.snapshot.dataset_version, "dataset version"),
            (artifact.observation_id, pack.snapshot.observation_id, "observation ID"),
            (artifact.channel_id, pack.snapshot.channel_id, "channel ID"),
        )
        for actual, expected, name in bindings:
            if actual != expected:
                raise GroundTruthLabelBindingError(f"ground-truth label {name} mismatch")

        if (
            rubric.evidence_pack_definition_id != definition.definition_id
            or rubric.evidence_pack_definition_version != definition.version
            or rubric.evidence_pack_definition_digest != definition.digest
        ):
            raise GroundTruthLabelBindingError(
                "labelling rubric evidence-pack definition mismatch"
            )

        evidence_item_ids = {item.item_id for item in definition.item_definitions}
        for criterion in rubric.criteria:
            if not set(criterion.evidence_item_ids).issubset(evidence_item_ids):
                raise GroundTruthLabelBindingError(
                    "labelling rubric criterion references unknown evidence item"
                )

        reasons = {reason.reason_code: reason for reason in rubric.reason_codes}
        for review in artifact.independent_reviews:
            self._validate_reason(reasons, review.reason_code, review.label)
        if artifact.adjudication is not None:
            self._validate_reason(
                reasons,
                artifact.adjudication.reason_code,
                artifact.adjudication.label,
            )

    @staticmethod
    def _validate_reason(
        reasons: dict[str, RubricReasonCode],
        reason_code: str,
        label: GroundTruthLabel,
    ) -> None:
        reason = reasons.get(reason_code)
        if reason is None:
            raise GroundTruthLabelBindingError(
                "ground-truth label uses reason code absent from rubric"
            )
        if label not in reason.allowed_labels:
            raise GroundTruthLabelBindingError(
                "ground-truth label reason code does not permit label state"
            )
