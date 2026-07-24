"""Behavior-focused tests for the canonical Opportunity Candidate boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

import app.services.opportunity_candidate as opportunity_candidate
from app.services.opportunity_candidate import (
    CandidateSourcePlatform,
    OpportunityCandidate,
    OpportunityCandidateCanonicalizer,
)

COMPLETE_CANDIDATE_JSON = (
    b'{"acquisition_timestamp":"2026-07-24T10:30:15Z",'
    b'"candidate_id":"candidate.espresso",'
    b'"discovery_source_id":"discovery.query.espresso",'
    b'"discovery_version":1,'
    b'"evidence_reference_ids":["evidence.channel.alpha","evidence.video.beta"],'
    b'"provenance_reference_ids":['
    b'"provenance.search.001","provenance.enrichment.001"],'
    b'"schema_version":1,'
    b'"source_platform":"youtube"}'
)
COMPLETE_CANDIDATE_DIGEST = (
    "8a21cbc5c9dd6298bf359f964a5887ac74cf6d7e02f5a1c6eb88ec676d8c4b57"
)


def complete_candidate() -> OpportunityCandidate:
    return OpportunityCandidate(
        schema_version=1,
        candidate_id="candidate.espresso",
        discovery_version=1,
        source_platform=CandidateSourcePlatform.YOUTUBE,
        discovery_source_id="discovery.query.espresso",
        evidence_reference_ids=(
            "evidence.channel.alpha",
            "evidence.video.beta",
        ),
        acquisition_timestamp=datetime(2026, 7, 24, 10, 30, 15, tzinfo=timezone.utc),
        provenance_reference_ids=(
            "provenance.search.001",
            "provenance.enrichment.001",
        ),
    )


def test_valid_candidate_preserves_prequalification_facts() -> None:
    candidate = complete_candidate()

    assert candidate.candidate_id == "candidate.espresso"
    assert candidate.source_platform is CandidateSourcePlatform.YOUTUBE
    assert candidate.evidence_reference_ids == (
        "evidence.channel.alpha",
        "evidence.video.beta",
    )
    assert candidate.acquisition_timestamp.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "missing",
    (
        "schema_version",
        "candidate_id",
        "discovery_version",
        "source_platform",
        "discovery_source_id",
        "evidence_reference_ids",
        "acquisition_timestamp",
        "provenance_reference_ids",
    ),
)
def test_every_contract_field_is_required(missing: str) -> None:
    values = complete_candidate().model_dump(mode="python")
    del values[missing]

    with pytest.raises(ValidationError):
        OpportunityCandidate(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("candidate_id", ""),
        ("candidate_id", "Candidate One"),
        ("discovery_version", 0),
        ("discovery_version", True),
        ("discovery_version", 1.0),
        ("discovery_version", "1"),
        ("source_platform", "tiktok"),
        ("source_platform", 1),
        ("discovery_source_id", ""),
        ("discovery_source_id", 1),
        ("evidence_reference_ids", ()),
        ("evidence_reference_ids", ["evidence.channel.alpha"]),
        ("evidence_reference_ids", "evidence.channel.alpha"),
        ("provenance_reference_ids", ()),
        ("provenance_reference_ids", ["provenance.search.001"]),
        ("acquisition_timestamp", "2026-07-24T10:30:15Z"),
        ("acquisition_timestamp", 1_753_352_415),
        ("unexpected_field", "value"),
    ),
)
def test_invalid_values_and_wrong_primitive_types_are_rejected(
    field: str, value: object
) -> None:
    values = complete_candidate().model_dump(mode="python")
    values[field] = value

    with pytest.raises(ValidationError):
        OpportunityCandidate(**values)


@pytest.mark.parametrize(
    "prohibited_field",
    (
        "score",
        "confidence",
        "recommendation",
        "rank",
        "qualification",
        "lifecycle_status",
        "priority",
        "ai_output",
        "explanation",
        "heuristic",
    ),
)
def test_interpretive_and_product_policy_fields_are_rejected(
    prohibited_field: str,
) -> None:
    values = complete_candidate().model_dump(mode="python")
    values[prohibited_field] = "not-authorized"

    with pytest.raises(ValidationError):
        OpportunityCandidate(**values)


def test_naive_timestamp_is_rejected() -> None:
    values = complete_candidate().model_dump(mode="python")
    values["acquisition_timestamp"] = datetime(2026, 7, 24, 10, 30, 15)

    with pytest.raises(ValidationError, match="timezone-aware"):
        OpportunityCandidate(**values)


def test_equivalent_timestamp_is_normalized_to_utc() -> None:
    values = complete_candidate().model_dump(mode="python")
    values["acquisition_timestamp"] = datetime(
        2026,
        7,
        24,
        16,
        0,
        15,
        tzinfo=timezone(timedelta(hours=5, minutes=30)),
    )
    candidate = OpportunityCandidate(**values)

    assert candidate == complete_candidate()
    assert OpportunityCandidateCanonicalizer.serialize(candidate) == COMPLETE_CANDIDATE_JSON


@pytest.mark.parametrize(
    ("field", "duplicate"),
    (
        ("evidence_reference_ids", "evidence.channel.alpha"),
        ("provenance_reference_ids", "provenance.search.001"),
    ),
)
def test_duplicate_reference_identities_are_rejected(
    field: str, duplicate: str
) -> None:
    values = complete_candidate().model_dump(mode="python")
    values[field] = (duplicate, duplicate)

    with pytest.raises(ValidationError, match="identities must be unique"):
        OpportunityCandidate(**values)


def test_candidate_is_recursively_immutable() -> None:
    candidate = complete_candidate()

    with pytest.raises(ValidationError):
        candidate.discovery_version = 2
    with pytest.raises(TypeError):
        candidate.evidence_reference_ids[0] = "evidence.changed"  # type: ignore[index]


def test_structural_equality_and_hashing_are_stable() -> None:
    first = complete_candidate()
    second = complete_candidate()
    values = first.model_dump(mode="python")
    values["discovery_version"] = 2
    changed = OpportunityCandidate(**values)

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second, changed}) == 2
    assert first != changed


def test_canonical_serialization_and_digest_are_order_independent() -> None:
    first = complete_candidate()
    second = OpportunityCandidate(
        provenance_reference_ids=(
            "provenance.search.001",
            "provenance.enrichment.001",
        ),
        acquisition_timestamp=datetime(2026, 7, 24, 10, 30, 15, tzinfo=timezone.utc),
        evidence_reference_ids=(
            "evidence.channel.alpha",
            "evidence.video.beta",
        ),
        discovery_source_id="discovery.query.espresso",
        source_platform=CandidateSourcePlatform.YOUTUBE,
        discovery_version=1,
        candidate_id="candidate.espresso",
        schema_version=1,
    )

    first_bytes = OpportunityCandidateCanonicalizer.serialize(first)
    second_bytes = OpportunityCandidateCanonicalizer.serialize(second)
    assert first_bytes == COMPLETE_CANDIDATE_JSON
    assert first_bytes == second_bytes
    assert b"\n" not in first_bytes
    assert b": " not in first_bytes and b", " not in first_bytes
    assert (
        OpportunityCandidateCanonicalizer.calculate_digest(first)
        == COMPLETE_CANDIDATE_DIGEST
    )
    assert (
        OpportunityCandidateCanonicalizer.calculate_digest(second)
        == COMPLETE_CANDIDATE_DIGEST
    )


def test_reference_order_is_preserved_as_part_of_candidate_identity() -> None:
    values = complete_candidate().model_dump(mode="python")
    values["evidence_reference_ids"] = tuple(
        reversed(values["evidence_reference_ids"])
    )
    reordered = OpportunityCandidate(**values)

    assert reordered != complete_candidate()
    assert (
        OpportunityCandidateCanonicalizer.serialize(reordered)
        != COMPLETE_CANDIDATE_JSON
    )


def test_canonicalizer_rejects_untyped_input() -> None:
    with pytest.raises(TypeError, match="candidate must be OpportunityCandidate"):
        OpportunityCandidateCanonicalizer.serialize({})  # type: ignore[arg-type]


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(opportunity_candidate.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(opportunity_candidate, name) for name in exported)


def test_candidate_dependency_boundary_and_startup_isolation() -> None:
    package = Path(opportunity_candidate.__file__).parent
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )
    prohibited_dependencies = (
        "app.api",
        "app.application",
        "app.db",
        "app.services.analytics",
        "app.services.backtesting",
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

    application = package.parents[1] / "application.py"
    assert "services.opportunity_candidate" not in application.read_text(encoding="utf-8")
