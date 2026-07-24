"""Behavior-focused tests for the canonical Evidence Manifest boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

import app.services.evidence_manifest as evidence_manifest
from app.services.evidence_manifest import (
    EvidenceManifest,
    EvidenceManifestCanonicalizer,
)

COMPLETE_MANIFEST_JSON = (
    b'{"created_at":"2026-07-24T10:30:15Z",'
    b'"description":"Initial espresso evidence snapshot",'
    b'"evidence_reference_ids":['
    b'"evidence.channel.alpha","evidence.video.espresso-001"],'
    b'"manifest_id":"manifest.espresso.initial",'
    b'"manifest_version":1,'
    b'"schema_version":1}'
)
COMPLETE_MANIFEST_DIGEST = (
    "f13b6ec8ede608d440ec2b45fd094b1eac92721fbfb4298340b2b807f5b799aa"
)


def complete_manifest() -> EvidenceManifest:
    return EvidenceManifest(
        schema_version=1,
        manifest_id="manifest.espresso.initial",
        manifest_version=1,
        evidence_reference_ids=(
            "evidence.channel.alpha",
            "evidence.video.espresso-001",
        ),
        created_at=datetime(2026, 7, 24, 10, 30, 15, tzinfo=timezone.utc),
        description="Initial espresso evidence snapshot",
    )


def test_valid_manifest_preserves_ordered_reference_identity_snapshot() -> None:
    manifest = complete_manifest()

    assert manifest.manifest_id == "manifest.espresso.initial"
    assert manifest.evidence_reference_ids == (
        "evidence.channel.alpha",
        "evidence.video.espresso-001",
    )
    assert manifest.created_at.tzinfo is timezone.utc
    assert manifest.description == "Initial espresso evidence snapshot"


@pytest.mark.parametrize(
    "missing",
    (
        "schema_version",
        "manifest_id",
        "manifest_version",
        "evidence_reference_ids",
        "created_at",
    ),
)
def test_required_fields_cannot_be_omitted(missing: str) -> None:
    values = complete_manifest().model_dump(mode="python")
    del values[missing]

    with pytest.raises(ValidationError):
        EvidenceManifest(**values)


def test_description_is_optional_and_explicitly_serialized() -> None:
    values = complete_manifest().model_dump(mode="python")
    values["description"] = None
    manifest = EvidenceManifest(**values)

    assert manifest.description is None
    assert b'"description":null' in EvidenceManifestCanonicalizer.serialize(manifest)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("manifest_id", ""),
        ("manifest_id", "Manifest One"),
        ("manifest_id", 1),
        ("manifest_version", 0),
        ("manifest_version", -1),
        ("manifest_version", True),
        ("manifest_version", 1.0),
        ("manifest_version", "1"),
        ("evidence_reference_ids", ()),
        ("evidence_reference_ids", ["evidence.channel.alpha"]),
        ("evidence_reference_ids", {"evidence.channel.alpha"}),
        ("evidence_reference_ids", "evidence.channel.alpha"),
        ("evidence_reference_ids", ("",)),
        ("evidence_reference_ids", (1,)),
        ("created_at", "2026-07-24T10:30:15Z"),
        ("created_at", 1_753_352_415),
        ("description", ""),
        ("description", " padded description "),
        ("description", 1),
        ("unexpected_field", "value"),
    ),
)
def test_strict_validation_rejects_invalid_values_and_primitive_types(
    field: str, value: object
) -> None:
    values = complete_manifest().model_dump(mode="python")
    values[field] = value

    with pytest.raises(ValidationError):
        EvidenceManifest(**values)


def test_duplicate_evidence_references_are_rejected() -> None:
    values = complete_manifest().model_dump(mode="python")
    values["evidence_reference_ids"] = (
        "evidence.channel.alpha",
        "evidence.channel.alpha",
    )

    with pytest.raises(ValidationError, match="identities must be unique"):
        EvidenceManifest(**values)


def test_naive_timestamp_is_rejected() -> None:
    values = complete_manifest().model_dump(mode="python")
    values["created_at"] = datetime(2026, 7, 24, 10, 30, 15)

    with pytest.raises(ValidationError, match="timezone-aware"):
        EvidenceManifest(**values)


def test_equivalent_timestamp_is_normalized_to_utc() -> None:
    values = complete_manifest().model_dump(mode="python")
    values["created_at"] = datetime(
        2026,
        7,
        24,
        16,
        0,
        15,
        tzinfo=timezone(timedelta(hours=5, minutes=30)),
    )
    manifest = EvidenceManifest(**values)

    assert manifest == complete_manifest()
    assert EvidenceManifestCanonicalizer.serialize(manifest) == COMPLETE_MANIFEST_JSON


@pytest.mark.parametrize(
    "prohibited_field",
    (
        "evidence_payload",
        "provenance",
        "url",
        "metadata",
        "analytics",
        "qualification",
        "confidence",
        "recommendation",
        "lifecycle_status",
        "score",
        "ai_output",
        "discovery_query",
        "retrieval_status",
        "persistence_id",
    ),
)
def test_payload_and_behavior_fields_are_rejected(prohibited_field: str) -> None:
    values = complete_manifest().model_dump(mode="python")
    values[prohibited_field] = "not-authorized"

    with pytest.raises(ValidationError):
        EvidenceManifest(**values)


def test_manifest_is_recursively_immutable() -> None:
    manifest = complete_manifest()

    with pytest.raises(ValidationError):
        manifest.manifest_version = 2
    with pytest.raises(TypeError):
        manifest.evidence_reference_ids[0] = "evidence.changed"  # type: ignore[index]


def test_structural_equality_and_hashing_are_stable() -> None:
    first = complete_manifest()
    second = complete_manifest()
    values = first.model_dump(mode="python")
    values["manifest_version"] = 2
    changed = EvidenceManifest(**values)

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second, changed}) == 2
    assert first != changed


def test_reference_order_remains_part_of_manifest_identity() -> None:
    values = complete_manifest().model_dump(mode="python")
    values["evidence_reference_ids"] = tuple(
        reversed(values["evidence_reference_ids"])
    )
    reordered = EvidenceManifest(**values)

    assert reordered != complete_manifest()
    assert EvidenceManifestCanonicalizer.serialize(reordered) != COMPLETE_MANIFEST_JSON


def test_canonical_serialization_is_construction_order_independent() -> None:
    first = complete_manifest()
    second = EvidenceManifest(
        description="Initial espresso evidence snapshot",
        created_at=datetime(2026, 7, 24, 10, 30, 15, tzinfo=timezone.utc),
        evidence_reference_ids=(
            "evidence.channel.alpha",
            "evidence.video.espresso-001",
        ),
        manifest_version=1,
        manifest_id="manifest.espresso.initial",
        schema_version=1,
    )

    first_bytes = EvidenceManifestCanonicalizer.serialize(first)
    second_bytes = EvidenceManifestCanonicalizer.serialize(second)
    assert first_bytes == COMPLETE_MANIFEST_JSON
    assert first_bytes == second_bytes
    assert b"\n" not in first_bytes
    assert b": " not in first_bytes and b", " not in first_bytes
    assert (
        EvidenceManifestCanonicalizer.calculate_digest(first)
        == COMPLETE_MANIFEST_DIGEST
    )
    assert (
        EvidenceManifestCanonicalizer.calculate_digest(second)
        == COMPLETE_MANIFEST_DIGEST
    )


def test_canonicalizer_rejects_untyped_input() -> None:
    with pytest.raises(TypeError, match="manifest must be EvidenceManifest"):
        EvidenceManifestCanonicalizer.serialize({})  # type: ignore[arg-type]


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(evidence_manifest.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(evidence_manifest, name) for name in exported)


def test_manifest_dependency_boundary_and_startup_isolation() -> None:
    package = Path(evidence_manifest.__file__).parent
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
    assert "app.services.evidence_reference.models" in source

    application = package.parents[1] / "application.py"
    assert "services.evidence_manifest" not in application.read_text(encoding="utf-8")
