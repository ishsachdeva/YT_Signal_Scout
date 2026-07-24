"""Immutable contracts for governed channel ground-truth labels."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.backtesting.models import ResearchIdentifier

GROUND_TRUTH_LABEL_SCHEMA_VERSION = 1
LabelText = Annotated[str, Field(min_length=1, max_length=4_000)]
Sha256Value = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class GroundTruthLabel(StrEnum):
    """Protocol-defined channel label states; no other state is permitted."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    BORDERLINE = "borderline"
    UNKNOWN = "unknown"


class LabelReviewerIdentity(BaseModel):
    """Stable supplied research-reviewer identity without authentication claims."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reviewer_id: ResearchIdentifier


class LabelContentDigest(BaseModel):
    """SHA-256 identity for evidence, rubric, or label-set content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    algorithm: Literal["sha256"]
    value: Sha256Value


class LabelEvidenceReference(BaseModel):
    """Exact rubric and channel evidence pack used for every label decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_pack_definition_id: ResearchIdentifier
    evidence_pack_definition_version: int = Field(ge=1)
    evidence_pack_id: ResearchIdentifier
    evidence_pack_version: int = Field(ge=1)
    evidence_pack_digest: LabelContentDigest
    rubric_id: ResearchIdentifier
    rubric_version: int = Field(ge=1)
    rubric_digest: LabelContentDigest


class IndependentLabelReview(BaseModel):
    """One blinded independent label decision for one observation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    review_id: ResearchIdentifier
    reviewer: LabelReviewerIdentity
    reviewed_at: datetime
    label: GroundTruthLabel
    reason_code: ResearchIdentifier
    reasoning_notes: Annotated[
        str | None,
        Field(default=None, min_length=1, max_length=4_000),
    ]

    @model_validator(mode="after")
    def validate_time(self) -> IndependentLabelReview:
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("independent label review timestamp must be timezone-aware")
        return self


class AdjudicatedLabelDecision(BaseModel):
    """Final decision used only when independent labels disagree."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    adjudication_id: ResearchIdentifier
    adjudicator: LabelReviewerIdentity
    adjudicated_at: datetime
    label: GroundTruthLabel
    reason_code: ResearchIdentifier
    reasoning_notes: LabelText

    @model_validator(mode="after")
    def validate_time(self) -> AdjudicatedLabelDecision:
        if self.adjudicated_at.tzinfo is None or self.adjudicated_at.utcoffset() is None:
            raise ValueError("label adjudication timestamp must be timezone-aware")
        return self


class SupersededLabelArtifactReference(BaseModel):
    """Immutable link to the previous artifact version retained in history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label_set_id: ResearchIdentifier
    label_set_version: int = Field(ge=1)
    artifact_id: ResearchIdentifier
    artifact_version: int = Field(ge=1)


class GroundTruthLabelArtifact(BaseModel):
    """Two independent reviews and one governed final channel label."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: ResearchIdentifier
    artifact_version: int = Field(ge=1)
    label_set_id: ResearchIdentifier
    label_set_version: int = Field(ge=1)
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    observation_id: ResearchIdentifier
    channel_id: Annotated[str, Field(min_length=1, max_length=100)]
    evidence: LabelEvidenceReference
    independent_reviews: Annotated[
        tuple[IndependentLabelReview, ...],
        Field(min_length=2, max_length=2),
    ]
    adjudication: AdjudicatedLabelDecision | None = None
    final_label: GroundTruthLabel
    supersedes: SupersededLabelArtifactReference | None = None
    change_reason: Annotated[
        str | None,
        Field(default=None, min_length=1, max_length=4_000),
    ]

    @model_validator(mode="after")
    def validate_decisions_and_history(self) -> GroundTruthLabelArtifact:
        review_ids = tuple(review.review_id for review in self.independent_reviews)
        reviewer_ids = tuple(
            review.reviewer.reviewer_id for review in self.independent_reviews
        )
        if len(set(review_ids)) != 2:
            raise ValueError("independent label review IDs must be unique")
        if len(set(reviewer_ids)) != 2:
            raise ValueError("independent label reviewers must be unique")

        labels = tuple(review.label for review in self.independent_reviews)
        latest_review = max(review.reviewed_at for review in self.independent_reviews)
        if labels[0] == labels[1]:
            if self.adjudication is not None:
                raise ValueError("matching independent labels must not be adjudicated")
            if self.final_label is not labels[0]:
                raise ValueError("matching independent labels must define the final label")
        else:
            if self.adjudication is None:
                raise ValueError("disagreeing independent labels require adjudication")
            if self.adjudication.label is not self.final_label:
                raise ValueError("adjudicated label must define the final label")
            if self.adjudication.adjudicator.reviewer_id in set(reviewer_ids):
                raise ValueError("adjudicator must be independent from label reviewers")
            if self.adjudication.adjudicated_at < latest_review:
                raise ValueError("adjudication cannot precede independent reviews")

        if self.artifact_version == 1:
            if self.supersedes is not None or self.change_reason is not None:
                raise ValueError("initial label artifact cannot supersede another version")
        else:
            if self.supersedes is None or self.change_reason is None:
                raise ValueError("replacement label artifact requires history and change reason")
            if (
                self.supersedes.label_set_id != self.label_set_id
                or self.supersedes.artifact_id != self.artifact_id
            ):
                raise ValueError("superseded label identity must match replacement identity")
            if self.supersedes.label_set_version >= self.label_set_version:
                raise ValueError("superseded label-set version must be earlier")
            if self.supersedes.artifact_version != self.artifact_version - 1:
                raise ValueError("label artifact versions must advance by one")
        return self


class GroundTruthLabelSetManifest(BaseModel):
    """Versioned identity and digest for one dataset-bound label set."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    label_set_id: ResearchIdentifier
    label_set_version: int = Field(ge=1)
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    created_at: datetime
    creator_identity: ResearchIdentifier
    digest: LabelContentDigest

    @model_validator(mode="after")
    def validate_time(self) -> GroundTruthLabelSetManifest:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("label-set creation timestamp must be timezone-aware")
        return self


class GroundTruthLabelSet(BaseModel):
    """Canonically ordered immutable labels bound to one dataset version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label_set_id: ResearchIdentifier
    version: int = Field(ge=1)
    dataset_id: ResearchIdentifier
    dataset_version: int = Field(ge=1)
    artifacts: Annotated[tuple[GroundTruthLabelArtifact, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_artifacts(self) -> GroundTruthLabelSet:
        identities = (
            ("artifact", tuple(item.artifact_id for item in self.artifacts)),
            ("observation", tuple(item.observation_id for item in self.artifacts)),
            ("channel", tuple(item.channel_id for item in self.artifacts)),
        )
        for name, values in identities:
            if len(set(values)) != len(values):
                raise ValueError(f"ground-truth label {name} identities must be unique")
        for artifact in self.artifacts:
            if (
                artifact.label_set_id != self.label_set_id
                or artifact.label_set_version != self.version
            ):
                raise ValueError("label artifact must match its label-set identity")
            if (
                artifact.dataset_id != self.dataset_id
                or artifact.dataset_version != self.dataset_version
            ):
                raise ValueError("label artifact must match its dataset identity")
        expected_order = tuple(
            sorted(
                self.artifacts,
                key=lambda item: (item.observation_id, item.artifact_id),
            )
        )
        if self.artifacts != expected_order:
            raise ValueError("ground-truth label artifacts must be canonically ordered")
        return self


class GroundTruthLabelImportResult(BaseModel):
    """Strictly imported manifest and immutable canonical label set."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest: GroundTruthLabelSetManifest
    label_set: GroundTruthLabelSet

    @model_validator(mode="after")
    def validate_binding(self) -> GroundTruthLabelImportResult:
        if self.manifest.label_set_id != self.label_set.label_set_id:
            raise ValueError("manifest and label-set IDs must match")
        if self.manifest.label_set_version != self.label_set.version:
            raise ValueError("manifest and label-set versions must match")
        if self.manifest.dataset_id != self.label_set.dataset_id:
            raise ValueError("manifest and label-set dataset IDs must match")
        if self.manifest.dataset_version != self.label_set.dataset_version:
            raise ValueError("manifest and label-set dataset versions must match")
        return self
