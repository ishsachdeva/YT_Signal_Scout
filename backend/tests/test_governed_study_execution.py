"""Tests for governed non-analytical study execution."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.services.backtesting import (
    EvidencePackImportResult,
    EvidencePackCanonicalizer,
    GroundTruthLabelImporter,
    LabelEvidenceReference,
    RubricImportResult,
    StudyConfiguration,
    StudyDefinition,
    StudyExecutionCanonicalizer,
    StudyExecutionDigestMismatchError,
    StudyExecutionRequest,
    StudyExecutionService,
    StudyExecutionValidationError,
    StudyInputBundle,
    HistoricalDatasetDigest,
)
from app.services.backtesting.evidence_models import EvidencePackDocument
from app.services.backtesting.rubric_models import RubricDocument
from tests.test_evidence_packs_and_rubrics import _evidence_document, _rubric
from tests.test_ground_truth_labels import _artifact, _document
from tests.test_historical_dataset_importer import (
    HistoricalDatasetImporter,
    _json,
    _observation,
    _OBSERVED_AT as DATASET_OBSERVED_AT,
)


def _request() -> StudyExecutionRequest:
    evidence = _evidence_document()
    snapshot = evidence.pack.snapshot.model_copy(
        update={"observed_at": DATASET_OBSERVED_AT}
    )
    provisional_pack = evidence.pack.model_copy(
        update={"snapshot": snapshot}
    )
    evidence = evidence.model_copy(
        update={
            "pack": provisional_pack.model_copy(
                update={
                    "digest": provisional_pack.digest.model_copy(
                        update={
                            "value": EvidencePackCanonicalizer.calculate_pack_digest(
                                provisional_pack
                            )
                        }
                    )
                }
            )
        }
    )
    rubric = RubricDocument(schema_version=1, rubric=_rubric(evidence.definition))
    artifact = _artifact().model_copy(
        update={
            "evidence": LabelEvidenceReference(
                evidence_pack_definition_id=evidence.definition.definition_id,
                evidence_pack_definition_version=evidence.definition.version,
                evidence_pack_id=evidence.pack.evidence_pack_id,
                evidence_pack_version=evidence.pack.version,
                evidence_pack_digest=evidence.pack.digest,
                rubric_id=rubric.rubric.rubric_id,
                rubric_version=rubric.rubric.version,
                rubric_digest=rubric.rubric.digest,
            )
        }
    )
    labels = GroundTruthLabelImporter().import_json(json.dumps(_document(artifact)))
    dataset = HistoricalDatasetImporter().import_json(
        _json(
            _observation(
                "observation-1",
                channel_id="channel-1",
                observed_at=evidence.pack.snapshot.observed_at,
            )
        )
    )
    configuration = StudyConfiguration(
        configuration_id="study-configuration-v1",
        version=1,
        dataset_schema_version=2,
        evidence_pack_schema_version=1,
        labelling_rubric_schema_version=1,
        ground_truth_label_schema_version=1,
    )
    definition = StudyDefinition(
        study_id="governed-study-v1",
        version=1,
        title="Governed fixture study",
        objective="Validate and package governed inputs without interpreting results.",
        protocol_id="sig-002-research-protocol",
        protocol_version=1,
        configuration_id=configuration.configuration_id,
        configuration_version=configuration.version,
        created_at=datetime(2026, 7, 24, 12, tzinfo=UTC),
    )
    executed_at = datetime(2026, 7, 24, 13, tzinfo=UTC)
    return StudyExecutionRequest(
        execution_id="study-execution-v1",
        requested_at=executed_at,
        started_at=executed_at,
        completed_at=executed_at,
        definition=definition,
        inputs=StudyInputBundle(
            dataset=dataset,
            evidence_packs=(EvidencePackImportResult(document=evidence),),
            labelling_rubric=RubricImportResult(document=rubric),
            ground_truth_labels=labels,
            configuration=configuration,
        ),
    )


def test_execution_is_immutable_deterministic_and_non_analytical() -> None:
    request = _request()
    service = StudyExecutionService()

    first = service.execute(request)
    second = service.execute(request)

    assert first == second
    assert first.context.observation_count == 1
    assert not hasattr(first, "report")
    assert not hasattr(first, "metrics")
    assert StudyExecutionCanonicalizer.serialize_result(first) == (
        StudyExecutionCanonicalizer.serialize_result(second)
    )
    with pytest.raises(ValidationError):
        first.context.observation_count = 2


def test_execution_rejects_dataset_and_evidence_observation_mismatch() -> None:
    request = _request()
    mismatched_dataset = request.inputs.dataset.model_copy(
        update={
            "dataset": request.inputs.dataset.dataset.model_copy(
                update={"dataset_id": "different-dataset"}
            )
        }
    )
    invalid = request.model_copy(
        update={"inputs": request.inputs.model_copy(update={"dataset": mismatched_dataset})}
    )

    with pytest.raises(StudyExecutionValidationError, match="ground-truth dataset mismatch"):
        StudyExecutionService().execute(invalid)


def test_unknown_request_fields_and_duplicate_execution_identity_are_rejected() -> None:
    request = _request()
    with pytest.raises(ValidationError):
        StudyExecutionRequest.model_validate(
            {**request.model_dump(mode="python"), "unknown": True}
        )

    duplicate = request.model_copy(
        update={"execution_id": request.definition.study_id}
    )
    with pytest.raises(StudyExecutionValidationError, match="identities must be unique"):
        StudyExecutionService().execute(duplicate)


def test_corrupted_governed_source_uses_execution_digest_error() -> None:
    request = _request()
    manifest = request.inputs.dataset.manifest.model_copy(
        update={
            "digest": HistoricalDatasetDigest(algorithm="sha256", value="0" * 64)
        }
    )
    dataset = request.inputs.dataset.model_copy(update={"manifest": manifest})
    corrupted = request.model_copy(
        update={"inputs": request.inputs.model_copy(update={"dataset": dataset})}
    )

    with pytest.raises(StudyExecutionDigestMismatchError):
        StudyExecutionService().execute(corrupted)
