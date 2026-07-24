"""Behavior-focused tests for the canonical Evidence Snapshot boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

import app.services.evidence_snapshot as evidence_snapshot
from app.services.evidence_snapshot import (
    EvidenceSnapshot,
    EvidenceSnapshotCanonicalizer,
)

COMPLETE_SNAPSHOT_JSON = (
    b'{"description":"Initial espresso qualification basis",'
    b'"manifest_digest":"f13b6ec8ede608d440ec2b45fd094b1eac92721fbfb4298340b2b807f5b799aa",'
    b'"manifest_id":"manifest.espresso.initial",'
    b'"manifest_version":1,'
    b'"schema_version":1,'
    b'"snapshot_id":"snapshot.espresso.initial",'
    b'"snapshot_timestamp":"2026-07-24T11:00:00Z",'
    b'"snapshot_version":1}'
)
COMPLETE_SNAPSHOT_DIGEST = (
    "10eea24f1e4593b87919ee4ebb94538906a667be7dc1c709c5bde5c89cf8d478"
)
MANIFEST_DIGEST = "f13b6ec8ede608d440ec2b45fd094b1eac92721fbfb4298340b2b807f5b799aa"


def complete_snapshot() -> EvidenceSnapshot:
    return EvidenceSnapshot(
        schema_version=1,
        snapshot_id="snapshot.espresso.initial",
        snapshot_version=1,
        manifest_id="manifest.espresso.initial",
        manifest_version=1,
        manifest_digest=MANIFEST_DIGEST,
        snapshot_timestamp=datetime(2026, 7, 24, 11, 0, 0, tzinfo=timezone.utc),
        description="Initial espresso qualification basis",
    )


def test_valid_snapshot_preserves_exact_manifest_identity_binding() -> None:
    snapshot = complete_snapshot()

    assert snapshot.snapshot_id == "snapshot.espresso.initial"
    assert snapshot.manifest_id == "manifest.espresso.initial"
    assert snapshot.manifest_version == 1
    assert snapshot.manifest_digest == MANIFEST_DIGEST
    assert snapshot.snapshot_timestamp.tzinfo is timezone.utc
    assert snapshot.description == "Initial espresso qualification basis"


@pytest.mark.parametrize(
    "missing",
    (
        "schema_version",
        "snapshot_id",
        "snapshot_version",
        "manifest_id",
        "manifest_version",
        "manifest_digest",
        "snapshot_timestamp",
    ),
)
def test_required_fields_cannot_be_omitted(missing: str) -> None:
    values = complete_snapshot().model_dump(mode="python")
    del values[missing]

    with pytest.raises(ValidationError):
        EvidenceSnapshot(**values)


def test_description_is_optional_and_explicitly_serialized() -> None:
    values = complete_snapshot().model_dump(mode="python")
    values["description"] = None
    snapshot = EvidenceSnapshot(**values)

    assert snapshot.description is None
    assert b'"description":null' in EvidenceSnapshotCanonicalizer.serialize(snapshot)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("snapshot_id", ""),
        ("snapshot_id", "Snapshot One"),
        ("snapshot_id", 1),
        ("snapshot_version", 0),
        ("snapshot_version", -1),
        ("snapshot_version", True),
        ("snapshot_version", 1.0),
        ("snapshot_version", "1"),
        ("manifest_id", ""),
        ("manifest_id", "Manifest One"),
        ("manifest_id", 1),
        ("manifest_version", 0),
        ("manifest_version", -1),
        ("manifest_version", True),
        ("manifest_version", 1.0),
        ("manifest_version", "1"),
        ("manifest_digest", MANIFEST_DIGEST.upper()),
        ("manifest_digest", "F" + MANIFEST_DIGEST[1:]),
        ("manifest_digest", MANIFEST_DIGEST[:-1]),
        ("manifest_digest", MANIFEST_DIGEST + "0"),
        ("manifest_digest", "g" * 64),
        ("manifest_digest", f" {MANIFEST_DIGEST} "),
        ("manifest_digest", 1),
        ("manifest_digest", MANIFEST_DIGEST.encode("ascii")),
        ("manifest_digest", True),
        ("snapshot_timestamp", "2026-07-24T11:00:00Z"),
        ("snapshot_timestamp", 1_753_354_800),
        ("description", ""),
        ("description", " padded description "),
        ("description", 1),
        ("unexpected_field", "value"),
    ),
)
def test_strict_validation_rejects_invalid_values_and_primitive_types(
    field: str, value: object
) -> None:
    values = complete_snapshot().model_dump(mode="python")
    values[field] = value

    with pytest.raises(ValidationError):
        EvidenceSnapshot(**values)


def test_naive_timestamp_is_rejected() -> None:
    values = complete_snapshot().model_dump(mode="python")
    values["snapshot_timestamp"] = datetime(2026, 7, 24, 11, 0, 0)

    with pytest.raises(ValidationError, match="timezone-aware"):
        EvidenceSnapshot(**values)


def test_equivalent_timestamp_is_normalized_to_utc() -> None:
    values = complete_snapshot().model_dump(mode="python")
    values["snapshot_timestamp"] = datetime(
        2026,
        7,
        24,
        16,
        30,
        0,
        tzinfo=timezone(timedelta(hours=5, minutes=30)),
    )
    snapshot = EvidenceSnapshot(**values)

    assert snapshot == complete_snapshot()
    assert EvidenceSnapshotCanonicalizer.serialize(snapshot) == COMPLETE_SNAPSHOT_JSON


@pytest.mark.parametrize(
    "prohibited_field",
    (
        "evidence_payload",
        "evidence_reference_ids",
        "manifest",
        "url",
        "provenance",
        "metadata",
        "analytics",
        "qualification",
        "recommendation",
        "lifecycle_status",
        "confidence",
        "ai_output",
        "discovery_query",
        "retrieval_status",
        "persistence_id",
    ),
)
def test_payload_and_behavior_fields_are_rejected(prohibited_field: str) -> None:
    values = complete_snapshot().model_dump(mode="python")
    values[prohibited_field] = "not-authorized"

    with pytest.raises(ValidationError):
        EvidenceSnapshot(**values)


def test_snapshot_is_immutable() -> None:
    snapshot = complete_snapshot()

    with pytest.raises(ValidationError):
        snapshot.manifest_version = 2


def test_structural_equality_and_hashing_are_stable() -> None:
    first = complete_snapshot()
    second = complete_snapshot()
    values = first.model_dump(mode="python")
    values["snapshot_version"] = 2
    changed = EvidenceSnapshot(**values)

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second, changed}) == 2
    assert first != changed


def test_manifest_digest_changes_snapshot_identity_and_canonical_content() -> None:
    first = complete_snapshot()
    values = first.model_dump(mode="python")
    values["manifest_digest"] = "0" * 64
    changed = EvidenceSnapshot(**values)

    assert first != changed
    assert hash(first) != hash(changed)
    assert EvidenceSnapshotCanonicalizer.serialize(first) != (
        EvidenceSnapshotCanonicalizer.serialize(changed)
    )
    assert EvidenceSnapshotCanonicalizer.calculate_digest(first) != (
        EvidenceSnapshotCanonicalizer.calculate_digest(changed)
    )


def test_canonical_serialization_is_construction_order_independent() -> None:
    first = complete_snapshot()
    second = EvidenceSnapshot(
        description="Initial espresso qualification basis",
        snapshot_timestamp=datetime(2026, 7, 24, 11, 0, 0, tzinfo=timezone.utc),
        manifest_version=1,
        manifest_digest=MANIFEST_DIGEST,
        manifest_id="manifest.espresso.initial",
        snapshot_version=1,
        snapshot_id="snapshot.espresso.initial",
        schema_version=1,
    )

    first_bytes = EvidenceSnapshotCanonicalizer.serialize(first)
    second_bytes = EvidenceSnapshotCanonicalizer.serialize(second)
    assert first_bytes == COMPLETE_SNAPSHOT_JSON
    assert first_bytes == second_bytes
    assert b"\n" not in first_bytes
    assert b": " not in first_bytes and b", " not in first_bytes
    assert (
        EvidenceSnapshotCanonicalizer.calculate_digest(first)
        == COMPLETE_SNAPSHOT_DIGEST
    )
    assert (
        EvidenceSnapshotCanonicalizer.calculate_digest(second)
        == COMPLETE_SNAPSHOT_DIGEST
    )


def test_canonicalizer_rejects_untyped_input() -> None:
    with pytest.raises(TypeError, match="snapshot must be EvidenceSnapshot"):
        EvidenceSnapshotCanonicalizer.serialize({})  # type: ignore[arg-type]


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(evidence_snapshot.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(evidence_snapshot, name) for name in exported)


def test_snapshot_dependency_boundary_and_startup_isolation() -> None:
    package = Path(evidence_snapshot.__file__).parent
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )
    prohibited_dependencies = (
        "app.api",
        "app.application",
        "app.db",
        "app.services.analytics",
        "app.services.backtesting",
        "app.services.evidence_reference",
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
    assert "app.services.evidence_manifest.models" in source

    application = package.parents[1] / "application.py"
    assert "services.evidence_snapshot" not in application.read_text(encoding="utf-8")
