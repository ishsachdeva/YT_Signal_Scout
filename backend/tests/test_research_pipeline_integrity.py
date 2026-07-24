"""End-to-end integrity checks for the complete governed research pipeline."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

import app.services.backtesting as backtesting
from app.services.backtesting import (
    EvaluationAggregationConfiguration,
    EvaluationAggregationDefinition,
    EvaluationAggregationRequest,
    EvaluationAggregationService,
    EvaluationCanonicalizer,
    EvaluationConfiguration,
    EvaluationDefinition,
    EvaluationOutcome,
    EvaluationRequest,
    EvidencePackCanonicalizer,
    EvidencePackDocument,
    EvidencePackImporter,
    GroundTruthLabel,
    GroundTruthLabelImporter,
    LabelContentDigest,
    LabelEvidenceReference,
    LabelledEvaluationService,
    ObservationPrediction,
    PredictedOutcome,
    RubricDocument,
    RubricImporter,
    StatisticalEvaluationCanonicalizer,
    StatisticalEvaluationConfiguration,
    StatisticalEvaluationDefinition,
    StatisticalEvaluationRequest,
    StatisticalEvaluationService,
    StudyConfiguration,
    StudyDefinition,
    StudyExecutionRequest,
    StudyExecutionService,
    StudyInputBundle,
)
from tests.test_evidence_packs_and_rubrics import _definition, _pack, _rubric
from tests.test_ground_truth_labels import _artifact, _document as _label_document
from tests.test_historical_dataset_importer import (
    HistoricalDatasetImporter,
    _OBSERVED_AT,
    _json as _dataset_json,
    _observation,
)


def _pipeline_inputs():
    observation_ids = tuple(f"observation-{index}" for index in range(1, 7))
    channel_ids = tuple(f"channel-{index}" for index in range(1, 7))
    dataset = HistoricalDatasetImporter().import_json(
        _dataset_json(
            *(
                _observation(
                    observation_id,
                    channel_id=channel_id,
                    observed_at=_OBSERVED_AT,
                )
                for observation_id, channel_id in zip(
                    observation_ids, channel_ids, strict=True
                )
            )
        )
    )

    definition = _definition()
    evidence_results = []
    for index, (observation_id, channel_id) in enumerate(
        zip(observation_ids, channel_ids, strict=True), start=1
    ):
        provisional = _pack(definition).model_copy(
            update={
                "evidence_pack_id": f"evidence-pack-{index}",
                "snapshot": _pack(definition).snapshot.model_copy(
                    update={
                        "snapshot_id": f"evidence-snapshot-{index}",
                        "observation_id": observation_id,
                        "channel_id": channel_id,
                        "observed_at": _OBSERVED_AT,
                    }
                ),
            }
        )
        pack = provisional.model_copy(
            update={
                "digest": LabelContentDigest(
                    algorithm="sha256",
                    value=EvidencePackCanonicalizer.calculate_pack_digest(provisional),
                )
            }
        )
        document = EvidencePackDocument(
            schema_version=1, definition=definition, pack=pack
        )
        evidence_results.append(
            EvidencePackImporter().import_json(
                json.dumps(document.model_dump(mode="json"))
            )
        )

    rubric_document = RubricDocument(schema_version=1, rubric=_rubric(definition))
    rubric_result = RubricImporter().import_json(
        json.dumps(rubric_document.model_dump(mode="json"))
    )
    truths = (
        GroundTruthLabel.POSITIVE,
        GroundTruthLabel.NEGATIVE,
        GroundTruthLabel.NEGATIVE,
        GroundTruthLabel.POSITIVE,
        GroundTruthLabel.BORDERLINE,
        GroundTruthLabel.POSITIVE,
    )
    artifacts = []
    for index, (observation_id, channel_id, truth, evidence_result) in enumerate(
        zip(
            observation_ids,
            channel_ids,
            truths,
            evidence_results,
            strict=True,
        ),
        start=1,
    ):
        evidence = evidence_result.document
        artifacts.append(
            _artifact(
                artifact_id=f"artifact-{index}",
                observation_id=observation_id,
                channel_id=channel_id,
                first_label=truth,
                second_label=truth,
            ).model_copy(
                update={
                    "evidence": LabelEvidenceReference(
                        evidence_pack_definition_id=definition.definition_id,
                        evidence_pack_definition_version=definition.version,
                        evidence_pack_id=evidence.pack.evidence_pack_id,
                        evidence_pack_version=evidence.pack.version,
                        evidence_pack_digest=evidence.pack.digest,
                        rubric_id=rubric_result.document.rubric.rubric_id,
                        rubric_version=rubric_result.document.rubric.version,
                        rubric_digest=rubric_result.document.rubric.digest,
                    )
                }
            )
        )
    labels = GroundTruthLabelImporter().import_json(
        json.dumps(_label_document(*artifacts))
    )
    return dataset, tuple(evidence_results), rubric_result, labels


def test_complete_research_pipeline_is_deterministic_and_content_addressed() -> None:
    dataset, evidence, rubric, labels = _pipeline_inputs()
    study_configuration = StudyConfiguration(
        configuration_id="pipeline-study-configuration-v1",
        version=1,
        dataset_schema_version=2,
        evidence_pack_schema_version=1,
        labelling_rubric_schema_version=1,
        ground_truth_label_schema_version=1,
    )
    study_definition = StudyDefinition(
        study_id="pipeline-study-v1",
        version=1,
        title="Synthetic pipeline integrity study",
        objective="Verify governed research architecture with synthetic artifacts only.",
        protocol_id="sig-002-research-protocol",
        protocol_version=4,
        configuration_id=study_configuration.configuration_id,
        configuration_version=study_configuration.version,
        created_at=datetime(2026, 7, 24, 12, tzinfo=UTC),
    )
    study_time = datetime(2026, 7, 24, 13, tzinfo=UTC)
    study_request = StudyExecutionRequest(
        execution_id="pipeline-study-execution-v1",
        requested_at=study_time,
        started_at=study_time,
        completed_at=study_time,
        definition=study_definition,
        inputs=StudyInputBundle(
            dataset=dataset,
            evidence_packs=evidence,
            labelling_rubric=rubric,
            ground_truth_labels=labels,
            configuration=study_configuration,
        ),
    )
    study_result = StudyExecutionService().execute(study_request)
    assert study_result.manifest.dataset_digest.value == dataset.manifest.digest.value
    assert study_result.manifest.evidence_definition_digest == (
        evidence[0].document.definition.digest
    )
    assert study_result.manifest.evidence_pack_digests == tuple(
        item.document.pack.digest for item in evidence
    )
    assert study_result.manifest.rubric_digest == rubric.document.rubric.digest
    assert study_result.manifest.ground_truth_label_digest == labels.manifest.digest

    evaluation_configuration = EvaluationConfiguration(
        configuration_id="pipeline-evaluation-configuration-v1",
        version=1,
        study_execution_id=study_result.metadata.execution_id,
        dataset_id=dataset.dataset.dataset_id,
        dataset_version=dataset.dataset.version,
        label_set_id=labels.label_set.label_set_id,
        label_set_version=labels.label_set.version,
        prediction_vocabulary_version=1,
    )
    evaluation_definition = EvaluationDefinition(
        evaluation_id="pipeline-evaluation-v1",
        version=1,
        title="Synthetic observation evaluation",
        objective="Verify all closed outcomes without real research.",
        configuration_id=evaluation_configuration.configuration_id,
        configuration_version=evaluation_configuration.version,
        created_at=datetime(2026, 7, 24, 14, tzinfo=UTC),
    )
    predicted = (
        PredictedOutcome.POSITIVE,
        PredictedOutcome.NEGATIVE,
        PredictedOutcome.POSITIVE,
        PredictedOutcome.NEGATIVE,
        PredictedOutcome.POSITIVE,
        PredictedOutcome.NOT_EVALUATED,
    )
    predictions = tuple(
        ObservationPrediction(
            prediction_id=f"prediction-{index}",
            observation_id=f"observation-{index}",
            channel_id=f"channel-{index}",
            predicted_outcome=outcome,
        )
        for index, outcome in enumerate(predicted, start=1)
    )
    evaluation_request = EvaluationRequest(
        evaluated_at=datetime(2026, 7, 24, 15, tzinfo=UTC),
        definition=evaluation_definition,
        configuration=evaluation_configuration,
        study_execution=study_result,
        dataset=dataset,
        ground_truth_labels=labels,
        predictions=predictions,
    )
    evaluation_result = LabelledEvaluationService().evaluate(evaluation_request)
    assert tuple(item.outcome for item in evaluation_result.observations) == tuple(
        EvaluationOutcome
    )
    assert evaluation_result.manifest.study_execution_digest == (
        study_result.manifest.result_digest
    )
    assert evaluation_result.manifest.dataset_digest.value == dataset.manifest.digest.value
    assert evaluation_result.manifest.ground_truth_label_digest == labels.manifest.digest

    aggregation_configuration = EvaluationAggregationConfiguration(
        configuration_id="pipeline-aggregation-configuration-v1",
        version=1,
        evaluation_id=evaluation_result.metadata.evaluation_id,
        evaluation_version=evaluation_result.metadata.evaluation_version,
        evaluation_schema_version=evaluation_result.manifest.schema_version,
        expected_observation_count=6,
    )
    aggregation_definition = EvaluationAggregationDefinition(
        aggregation_id="pipeline-aggregation-v1",
        version=1,
        title="Synthetic outcome aggregation",
        objective="Count every closed outcome exactly once.",
        configuration_id=aggregation_configuration.configuration_id,
        configuration_version=aggregation_configuration.version,
        created_at=datetime(2026, 7, 24, 16, tzinfo=UTC),
    )
    aggregation_request = EvaluationAggregationRequest(
        aggregated_at=datetime(2026, 7, 24, 17, tzinfo=UTC),
        definition=aggregation_definition,
        configuration=aggregation_configuration,
        evaluation_result=evaluation_result,
    )
    aggregation_result = EvaluationAggregationService().aggregate(aggregation_request)
    assert aggregation_result.summary.model_dump() == {
        "true_positive_count": 1,
        "true_negative_count": 1,
        "false_positive_count": 1,
        "false_negative_count": 1,
        "unknown_count": 1,
        "not_evaluated_count": 1,
        "total_evaluated": 5,
        "total_observations": 6,
    }

    statistical_configuration = StatisticalEvaluationConfiguration(
        configuration_id="pipeline-statistical-configuration-v1",
        version=1,
        aggregation_id=aggregation_result.metadata.aggregation_id,
        aggregation_version=aggregation_result.metadata.aggregation_version,
        aggregation_schema_version=aggregation_result.manifest.schema_version,
        confidence_level="0.95",
        wilson_z="1.959963984540054",
    )
    statistical_definition = StatisticalEvaluationDefinition(
        statistical_evaluation_id="pipeline-statistical-evaluation-v1",
        version=1,
        title="Synthetic statistical verification",
        objective="Verify complete mathematical continuity without interpretation.",
        configuration_id=statistical_configuration.configuration_id,
        configuration_version=statistical_configuration.version,
        created_at=datetime(2026, 7, 24, 18, tzinfo=UTC),
    )
    statistical_request = StatisticalEvaluationRequest(
        evaluated_at=datetime(2026, 7, 24, 19, tzinfo=UTC),
        definition=statistical_definition,
        configuration=statistical_configuration,
        aggregation_result=aggregation_result,
    )
    service = StatisticalEvaluationService()
    first = service.evaluate(statistical_request)
    second = service.evaluate(statistical_request)

    assert first == second
    assert first.summary.accuracy == pytest.approx(0.5)
    assert first.summary.precision == pytest.approx(0.5)
    assert first.summary.recall == pytest.approx(0.5)
    assert first.summary.specificity == pytest.approx(0.5)
    assert first.summary.balanced_accuracy == pytest.approx(0.5)
    assert first.summary.f1_score == pytest.approx(0.5)
    assert first.summary.matthews_correlation_coefficient == pytest.approx(0.0)
    assert aggregation_result.manifest.evaluation_result_digest == (
        evaluation_result.manifest.result_digest
    )
    assert first.manifest.aggregation_result_digest == (
        aggregation_result.manifest.result_digest
    )
    assert StatisticalEvaluationCanonicalizer.serialize_result(first) == (
        StatisticalEvaluationCanonicalizer.serialize_result(second)
    )
    assert EvaluationCanonicalizer.serialize_result(evaluation_result)


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(backtesting.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(backtesting, name) for name in exported)


def test_research_dependencies_flow_downstream_and_runtime_does_not_import_them() -> None:
    package = Path(backtesting.__file__).parent
    forbidden = {
        "study_execution.py": (
            "labelled_evaluation",
            "evaluation_aggregation",
            "statistical_evaluation",
        ),
        "labelled_evaluation.py": ("evaluation_aggregation", "statistical_evaluation"),
        "evaluation_aggregation.py": ("statistical_evaluation",),
    }
    for filename, names in forbidden.items():
        source = (package / filename).read_text(encoding="utf-8")
        assert all(f"backtesting.{name}" not in source for name in names)

    boundary_services = (
        "study_execution.py",
        "labelled_evaluation.py",
        "evaluation_aggregation.py",
        "statistical_evaluation.py",
    )
    assert all(
        "except Exception" not in (package / filename).read_text(encoding="utf-8")
        for filename in boundary_services
    )

    application = package.parents[1] / "application.py"
    source = application.read_text(encoding="utf-8")
    assert "services.backtesting" not in source
