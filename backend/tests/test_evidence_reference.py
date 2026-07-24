"""Behavior-focused tests for the canonical Evidence Reference boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import app.services.evidence_reference as evidence_reference
from app.services.evidence_reference import (
    EvidenceReference,
    EvidenceReferenceCanonicalizer,
    EvidenceSourcePlatform,
    EvidenceType,
)

COMPLETE_REFERENCE_JSON = (
    b'{"evidence_reference_id":"evidence.video.espresso-001",'
    b'"evidence_type":"video",'
    b'"evidence_version":1,'
    b'"schema_version":1,'
    b'"source_object_id":"dQw4w9WgXcQ",'
    b'"source_platform":"youtube"}'
)
COMPLETE_REFERENCE_DIGEST = (
    "5d069e645de69b401a065b302df284396a1368b5e57a68affa55aeabede10fe5"
)


def complete_reference() -> EvidenceReference:
    return EvidenceReference(
        schema_version=1,
        evidence_reference_id="evidence.video.espresso-001",
        evidence_version=1,
        evidence_type=EvidenceType.VIDEO,
        source_platform=EvidenceSourcePlatform.YOUTUBE,
        source_object_id="dQw4w9WgXcQ",
    )


def test_valid_reference_preserves_pointer_identity_only() -> None:
    reference = complete_reference()

    assert reference.evidence_reference_id == "evidence.video.espresso-001"
    assert reference.evidence_type is EvidenceType.VIDEO
    assert reference.source_platform is EvidenceSourcePlatform.YOUTUBE
    assert reference.source_object_id == "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "missing",
    (
        "schema_version",
        "evidence_reference_id",
        "evidence_version",
        "evidence_type",
        "source_platform",
        "source_object_id",
    ),
)
def test_every_contract_field_is_required(missing: str) -> None:
    values = complete_reference().model_dump(mode="python")
    del values[missing]

    with pytest.raises(ValidationError):
        EvidenceReference(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("evidence_reference_id", ""),
        ("evidence_reference_id", "Evidence Video"),
        ("evidence_reference_id", 1),
        ("evidence_version", 0),
        ("evidence_version", -1),
        ("evidence_version", True),
        ("evidence_version", 1.0),
        ("evidence_version", "1"),
        ("evidence_type", "observation"),
        ("evidence_type", 1),
        ("source_platform", "vimeo"),
        ("source_platform", 1),
        ("source_object_id", ""),
        ("source_object_id", "invalid object id"),
        ("source_object_id", 1),
        ("unexpected_field", "value"),
    ),
)
def test_strict_validation_rejects_invalid_values_and_primitive_types(
    field: str, value: object
) -> None:
    values = complete_reference().model_dump(mode="python")
    values[field] = value

    with pytest.raises(ValidationError):
        EvidenceReference(**values)


def test_duplicate_reference_and_source_identities_are_rejected() -> None:
    with pytest.raises(ValidationError, match="identities must be distinct"):
        EvidenceReference(
            schema_version=1,
            evidence_reference_id="same",
            evidence_version=1,
            evidence_type=EvidenceType.CHANNEL,
            source_platform=EvidenceSourcePlatform.YOUTUBE,
            source_object_id="same",
        )


@pytest.mark.parametrize(
    "prohibited_field",
    (
        "evidence_payload",
        "metadata",
        "analytics",
        "score",
        "confidence",
        "qualification",
        "recommendation",
        "lifecycle_status",
        "ai_output",
        "provenance",
        "timestamp",
        "url",
        "discovery_query",
    ),
)
def test_payload_and_behavior_fields_are_rejected(prohibited_field: str) -> None:
    values = complete_reference().model_dump(mode="python")
    values[prohibited_field] = "not-authorized"

    with pytest.raises(ValidationError):
        EvidenceReference(**values)


def test_reference_is_immutable() -> None:
    reference = complete_reference()

    with pytest.raises(ValidationError):
        reference.evidence_version = 2


def test_structural_equality_and_hashing_are_stable() -> None:
    first = complete_reference()
    second = complete_reference()
    values = first.model_dump(mode="python")
    values["evidence_version"] = 2
    changed = EvidenceReference(**values)

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second, changed}) == 2
    assert first != changed


def test_canonical_serialization_and_digest_are_construction_order_independent() -> None:
    first = complete_reference()
    second = EvidenceReference(
        source_object_id="dQw4w9WgXcQ",
        source_platform=EvidenceSourcePlatform.YOUTUBE,
        evidence_type=EvidenceType.VIDEO,
        evidence_version=1,
        evidence_reference_id="evidence.video.espresso-001",
        schema_version=1,
    )

    first_bytes = EvidenceReferenceCanonicalizer.serialize(first)
    second_bytes = EvidenceReferenceCanonicalizer.serialize(second)
    assert first_bytes == COMPLETE_REFERENCE_JSON
    assert first_bytes == second_bytes
    assert b"\n" not in first_bytes
    assert b": " not in first_bytes and b", " not in first_bytes
    assert (
        EvidenceReferenceCanonicalizer.calculate_digest(first)
        == COMPLETE_REFERENCE_DIGEST
    )
    assert (
        EvidenceReferenceCanonicalizer.calculate_digest(second)
        == COMPLETE_REFERENCE_DIGEST
    )


def test_canonicalizer_rejects_untyped_input() -> None:
    with pytest.raises(TypeError, match="reference must be EvidenceReference"):
        EvidenceReferenceCanonicalizer.serialize({})  # type: ignore[arg-type]


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(evidence_reference.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(evidence_reference, name) for name in exported)


def test_evidence_reference_dependency_boundary_and_startup_isolation() -> None:
    package = Path(evidence_reference.__file__).parent
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )
    prohibited_dependencies = (
        "app.api",
        "app.application",
        "app.db",
        "app.services.analytics",
        "app.services.backtesting",
        "app.services.opportunity",
        "app.services.opportunity_candidate",
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

    application = package.parents[1] / "application.py"
    assert "services.evidence_reference" not in application.read_text(encoding="utf-8")
