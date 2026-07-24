"""Pure validation and packaging for one governed offline study."""

from __future__ import annotations

from app.services.backtesting.evidence_importer import EvidencePackCanonicalizer
from app.services.backtesting.exceptions import (
    EvidencePackDigestMismatchError,
    GroundTruthLabelBindingError,
    GroundTruthLabelDigestMismatchError,
    HistoricalDatasetDigestMismatchError,
    RubricDigestMismatchError,
    StudyExecutionDigestMismatchError,
    StudyExecutionValidationError,
)
from app.services.backtesting.importer import HistoricalDatasetCanonicalizer
from app.services.backtesting.label_binding import GroundTruthLabelBindingValidator
from app.services.backtesting.label_importer import GroundTruthLabelCanonicalizer
from app.services.backtesting.label_models import LabelContentDigest
from app.services.backtesting.rubric_importer import RubricCanonicalizer
from app.services.backtesting.study_execution_canonicalizer import (
    StudyExecutionCanonicalizer,
)
from app.services.backtesting.study_execution_models import (
    STUDY_EXECUTION_SCHEMA_VERSION,
    StudyExecutionContext,
    StudyExecutionManifest,
    StudyExecutionMetadata,
    StudyExecutionRequest,
    StudyExecutionResult,
)


class StudyExecutionValidator:
    """Fail fast on incompatible, mismatched, or corrupt governed inputs."""

    def __init__(self) -> None:
        self._label_binding = GroundTruthLabelBindingValidator()

    def validate(self, request: StudyExecutionRequest) -> StudyExecutionContext:
        if not isinstance(request, StudyExecutionRequest):
            raise StudyExecutionValidationError(("typed study execution request is required",))

        inputs = request.inputs
        definition = request.definition
        configuration = inputs.configuration
        dataset = inputs.dataset
        evidences = tuple(item.document for item in inputs.evidence_packs)
        evidence = evidences[0]
        rubric = inputs.labelling_rubric.document.rubric
        labels = inputs.ground_truth_labels

        if (definition.configuration_id, definition.configuration_version) != (
            configuration.configuration_id,
            configuration.version,
        ):
            self._fail("study definition configuration mismatch")
        expected_dataset = (dataset.dataset.dataset_id, dataset.dataset.version)
        if (labels.label_set.dataset_id, labels.label_set.dataset_version) != expected_dataset:
            self._fail("ground-truth dataset mismatch")
        observations = {item.observation_id: item for item in dataset.dataset.observations}
        artifacts = {item.observation_id: item for item in labels.label_set.artifacts}
        evidence_by_observation = {item.pack.snapshot.observation_id: item for item in evidences}
        if len(evidence_by_observation) != len(evidences):
            self._fail("duplicate evidence observation identity")
        pack_ids = tuple(item.pack.evidence_pack_id for item in evidences)
        if len(set(pack_ids)) != len(pack_ids):
            self._fail("duplicate evidence-pack identity")
        evidence_order = tuple(item.pack.snapshot.observation_id for item in evidences)
        if evidence_order != tuple(sorted(evidence_order)):
            self._fail("evidence packs must be canonically ordered by observation ID")
        expected_ids = set(observations)
        if set(artifacts) != expected_ids:
            self._fail("ground-truth observation coverage mismatch")
        if set(evidence_by_observation) != expected_ids:
            self._fail("evidence observation coverage mismatch")
        definition_binding = (
            evidence.definition.definition_id,
            evidence.definition.version,
            evidence.definition.digest,
        )
        for document in evidences:
            if (document.definition.definition_id, document.definition.version, document.definition.digest) != definition_binding:
                self._fail("evidence-pack definition mismatch within study")
            observation = observations[document.pack.snapshot.observation_id]
            snapshot = document.pack.snapshot
            if (snapshot.dataset_id, snapshot.dataset_version) != expected_dataset:
                self._fail("evidence dataset mismatch")
            if (snapshot.channel_id, snapshot.observed_at) != (observation.channel_id, observation.observed_at):
                self._fail("evidence observation mismatch")

        schema_versions = (
            (configuration.dataset_schema_version, dataset.manifest.schema_version, "dataset"),
            (configuration.evidence_pack_schema_version, evidence.schema_version, "evidence-pack"),
            (configuration.labelling_rubric_schema_version, inputs.labelling_rubric.document.schema_version, "labelling-rubric"),
            (configuration.ground_truth_label_schema_version, labels.manifest.schema_version, "ground-truth label"),
        )
        for configured, supplied, name in schema_versions:
            if configured != supplied:
                self._fail(f"{name} schema version mismatch")

        try:
            HistoricalDatasetCanonicalizer.validate_digest(dataset.manifest, dataset.dataset.observations)
            for document in evidences:
                EvidencePackCanonicalizer.validate_definition_digest(document.definition)
                EvidencePackCanonicalizer.validate_pack_digest(document.pack)
            RubricCanonicalizer.validate_digest(inputs.labelling_rubric.document)
            GroundTruthLabelCanonicalizer.validate_digest(labels.manifest, labels.label_set.artifacts)
        except (
            HistoricalDatasetDigestMismatchError,
            EvidencePackDigestMismatchError,
            RubricDigestMismatchError,
            GroundTruthLabelDigestMismatchError,
        ) as exc:
            raise StudyExecutionDigestMismatchError((str(exc),)) from exc

        try:
            for observation_id, artifact in artifacts.items():
                self._label_binding.validate(
                    artifact, evidence_by_observation[observation_id], rubric
                )
        except GroundTruthLabelBindingError as exc:
            raise StudyExecutionValidationError((str(exc),)) from exc

        identities = (
            request.execution_id,
            definition.study_id,
            configuration.configuration_id,
            rubric.rubric_id,
            labels.label_set.label_set_id,
        )
        if len(set(identities)) != len(identities):
            self._fail("execution and governed artifact identities must be unique")

        return StudyExecutionContext(
            dataset_id=expected_dataset[0], dataset_version=expected_dataset[1],
            observation_count=len(observations), evidence_pack_count=len(evidences), label_count=len(artifacts),
            evidence_pack_definition_id=evidence.definition.definition_id,
            evidence_pack_definition_version=evidence.definition.version,
            rubric_id=rubric.rubric_id, rubric_version=rubric.version,
            label_set_id=labels.label_set.label_set_id, label_set_version=labels.label_set.version,
            configuration_id=configuration.configuration_id, configuration_version=configuration.version,
        )

    @staticmethod
    def _fail(issue: str) -> None:
        raise StudyExecutionValidationError((issue,))


class StudyExecutionService:
    """Synchronously validate and package one study without analysis."""

    def __init__(self, validator: StudyExecutionValidator | None = None) -> None:
        self._validator = validator or StudyExecutionValidator()

    def execute(self, request: StudyExecutionRequest) -> StudyExecutionResult:
        context = self._validator.validate(request)
        metadata = StudyExecutionMetadata(
            execution_id=request.execution_id,
            requested_at=request.requested_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
            study_id=request.definition.study_id,
            study_version=request.definition.version,
        )
        inputs = request.inputs
        manifest_without_result = StudyExecutionManifest(
            schema_version=STUDY_EXECUTION_SCHEMA_VERSION,
            dataset_digest=LabelContentDigest(algorithm="sha256", value=inputs.dataset.manifest.digest.value),
            evidence_definition_digest=inputs.evidence_packs[0].document.definition.digest,
            evidence_pack_digests=tuple(item.document.pack.digest for item in inputs.evidence_packs),
            rubric_digest=inputs.labelling_rubric.document.rubric.digest,
            ground_truth_label_digest=inputs.ground_truth_labels.manifest.digest,
            result_digest=LabelContentDigest(algorithm="sha256", value="0" * 64),
        )
        digest = StudyExecutionCanonicalizer.calculate_result_digest(
            metadata, context, manifest_without_result
        )
        return StudyExecutionResult(
            metadata=metadata,
            context=context,
            manifest=manifest_without_result.model_copy(
                update={"result_digest": LabelContentDigest(algorithm="sha256", value=digest)}
            ),
        )
