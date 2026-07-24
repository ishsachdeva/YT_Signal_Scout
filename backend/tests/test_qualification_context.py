"""Behavior-focused tests for the canonical Qualification Context boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

import app.services.qualification_context as qualification_context
from app.services.qualification_context import (
    QualificationContext,
    QualificationContextCanonicalizer,
)

COMPLETE_CONTEXT_JSON = (
    b'{"candidate_id":"candidate.espresso",'
    b'"description":"Initial espresso candidate evaluation request",'
    b'"evaluation_timestamp":"2026-07-24T12:30:15Z",'
    b'"profile_id":"owner.default",'
    b'"qualification_context_id":"qualification-context.espresso.initial",'
    b'"qualification_context_version":1,'
    b'"qualification_policy_id":"qualification-policy.initial",'
    b'"qualification_policy_version":1,'
    b'"schema_version":1,'
    b'"snapshot_id":"snapshot.espresso.initial"}'
)
COMPLETE_CONTEXT_DIGEST = (
    "2fac2f8fd43b6ec73b90ba2a756e101ebf79424c85c96b2aaa2b3f9dceb02dba"
)


def complete_context() -> QualificationContext:
    return QualificationContext(
        schema_version=1,
        qualification_context_id="qualification-context.espresso.initial",
        qualification_context_version=1,
        candidate_id="candidate.espresso",
        snapshot_id="snapshot.espresso.initial",
        profile_id="owner.default",
        qualification_policy_id="qualification-policy.initial",
        qualification_policy_version=1,
        evaluation_timestamp=datetime(
            2026, 7, 24, 12, 30, 15, tzinfo=timezone.utc
        ),
        description="Initial espresso candidate evaluation request",
    )


def test_valid_context_preserves_only_evaluation_request_facts() -> None:
    context = complete_context()

    assert context.candidate_id == "candidate.espresso"
    assert context.snapshot_id == "snapshot.espresso.initial"
    assert context.profile_id == "owner.default"
    assert context.qualification_policy_id == "qualification-policy.initial"
    assert context.evaluation_timestamp.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "missing",
    (
        "schema_version",
        "qualification_context_id",
        "qualification_context_version",
        "candidate_id",
        "snapshot_id",
        "profile_id",
        "qualification_policy_id",
        "qualification_policy_version",
        "evaluation_timestamp",
    ),
)
def test_every_identity_version_and_timestamp_field_is_required(missing: str) -> None:
    values = complete_context().model_dump(mode="python")
    del values[missing]

    with pytest.raises(ValidationError):
        QualificationContext(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("qualification_context_id", ""),
        ("qualification_context_id", "Context One"),
        ("qualification_context_id", 1),
        ("qualification_context_version", 0),
        ("qualification_context_version", True),
        ("qualification_context_version", 1.0),
        ("qualification_context_version", "1"),
        ("candidate_id", ""),
        ("candidate_id", "Candidate One"),
        ("candidate_id", 1),
        ("snapshot_id", ""),
        ("snapshot_id", "Snapshot One"),
        ("snapshot_id", 1),
        ("profile_id", ""),
        ("profile_id", "Profile One"),
        ("profile_id", 1),
        ("qualification_policy_id", ""),
        ("qualification_policy_id", "Policy One"),
        ("qualification_policy_id", 1),
        ("qualification_policy_version", 0),
        ("qualification_policy_version", True),
        ("qualification_policy_version", 1.0),
        ("qualification_policy_version", "1"),
        ("evaluation_timestamp", "2026-07-24T12:30:15Z"),
        ("evaluation_timestamp", 1_753_360_215),
        ("description", ""),
        ("description", " padded "),
        ("description", 1),
    ),
)
def test_invalid_values_and_wrong_primitive_types_are_rejected(
    field: str, value: object
) -> None:
    values = complete_context().model_dump(mode="python")
    values[field] = value

    with pytest.raises(ValidationError):
        QualificationContext(**values)


@pytest.mark.parametrize(
    "prohibited_field",
    (
        "opportunity",
        "candidate",
        "evidence_snapshot",
        "creator_profile",
        "evidence",
        "manifest",
        "url",
        "provenance",
        "metadata",
        "analytics",
        "signals",
        "confidence",
        "score",
        "recommendation",
        "ai_output",
        "qualification_result",
        "lifecycle",
        "persistence",
        "retrieval",
        "registry",
        "workflow",
    ),
)
def test_prohibited_product_and_runtime_fields_are_rejected(
    prohibited_field: str,
) -> None:
    values = complete_context().model_dump(mode="python")
    values[prohibited_field] = "not-authorized"

    with pytest.raises(ValidationError):
        QualificationContext(**values)


def test_naive_timestamp_is_rejected() -> None:
    values = complete_context().model_dump(mode="python")
    values["evaluation_timestamp"] = datetime(2026, 7, 24, 12, 30, 15)

    with pytest.raises(ValidationError, match="timezone-aware"):
        QualificationContext(**values)


def test_equivalent_timestamp_is_normalized_to_utc() -> None:
    values = complete_context().model_dump(mode="python")
    values["evaluation_timestamp"] = datetime(
        2026,
        7,
        24,
        18,
        0,
        15,
        tzinfo=timezone(timedelta(hours=5, minutes=30)),
    )
    context = QualificationContext(**values)

    assert context == complete_context()
    assert QualificationContextCanonicalizer.serialize(context) == COMPLETE_CONTEXT_JSON


def test_context_is_immutable() -> None:
    context = complete_context()

    with pytest.raises(ValidationError):
        context.qualification_context_version = 2


def test_structural_equality_and_hashing_are_stable() -> None:
    first = complete_context()
    second = complete_context()
    values = first.model_dump(mode="python")
    values["qualification_context_version"] = 2
    changed = QualificationContext(**values)

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second, changed}) == 2
    assert first != changed


def test_canonical_serialization_and_digest_are_construction_order_independent() -> None:
    first = complete_context()
    second = QualificationContext(
        description="Initial espresso candidate evaluation request",
        evaluation_timestamp=datetime(
            2026, 7, 24, 12, 30, 15, tzinfo=timezone.utc
        ),
        qualification_policy_version=1,
        qualification_policy_id="qualification-policy.initial",
        profile_id="owner.default",
        snapshot_id="snapshot.espresso.initial",
        candidate_id="candidate.espresso",
        qualification_context_version=1,
        qualification_context_id="qualification-context.espresso.initial",
        schema_version=1,
    )

    first_bytes = QualificationContextCanonicalizer.serialize(first)
    second_bytes = QualificationContextCanonicalizer.serialize(second)
    assert first_bytes == COMPLETE_CONTEXT_JSON
    assert first_bytes == second_bytes
    assert b"\n" not in first_bytes
    assert b": " not in first_bytes and b", " not in first_bytes
    assert (
        QualificationContextCanonicalizer.calculate_digest(first)
        == COMPLETE_CONTEXT_DIGEST
    )
    assert (
        QualificationContextCanonicalizer.calculate_digest(second)
        == COMPLETE_CONTEXT_DIGEST
    )


def test_canonicalizer_rejects_untyped_input() -> None:
    with pytest.raises(TypeError, match="context must be QualificationContext"):
        QualificationContextCanonicalizer.serialize({})  # type: ignore[arg-type]


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(qualification_context.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(qualification_context, name) for name in exported)


def test_dependency_boundary_and_startup_isolation() -> None:
    package = Path(qualification_context.__file__).parent
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )
    prohibited_dependencies = (
        "app.api",
        "app.application",
        "app.db",
        "app.services.analytics",
        "app.services.backtesting",
        "app.services.evidence_manifest",
        "app.services.evidence_reference",
        "app.services.opportunity.",
        "app.services.research",
        "app.services.signals",
        "app.services.youtube",
        "fastapi",
        "sqlalchemy",
        "httpx",
        "openai",
        "requests",
        "googleapiclient",
    )
    assert all(name not in source for name in prohibited_dependencies)
    assert "app.services.opportunity_candidate.models" in source
    assert "app.services.evidence_snapshot.models" in source
    assert "app.services.creator_profile.models" in source

    application = package.parents[1] / "application.py"
    assert "services.qualification_context" not in application.read_text(
        encoding="utf-8"
    )
