"""Behavior-focused tests for the canonical Opportunity domain boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import app.services.opportunity as opportunity
from app.services.opportunity import (
    KnownOpportunityContext,
    Opportunity,
    OpportunityCanonicalizer,
    SourcePlatform,
    UnknownOpportunityContext,
)

COMPLETE_OPPORTUNITY_JSON = (
    b'{"language":{"state":"known","value":"en"},'
    b'"market_id":"market.india-en",'
    b'"niche_id":"niche.home-espresso",'
    b'"opportunity_id":"opportunity.espresso",'
    b'"opportunity_version":1,'
    b'"proposition":"Beginner home espresso education for cost-conscious creators",'
    b'"region":{"state":"unknown"},'
    b'"schema_version":1,'
    b'"source_platform":"youtube"}'
)
COMPLETE_OPPORTUNITY_DIGEST = (
    "892e97ed86c953b7b6758bd2a70bbdc5b89179a23e502b964adcfb9f224421b9"
)
UNKNOWN_CONTEXT_OPPORTUNITY_JSON = (
    b'{"language":{"state":"unknown"},'
    b'"market_id":"market.india-en",'
    b'"niche_id":"niche.home-espresso",'
    b'"opportunity_id":"opportunity.espresso",'
    b'"opportunity_version":1,'
    b'"proposition":"Beginner home espresso education for cost-conscious creators",'
    b'"region":{"state":"unknown"},'
    b'"schema_version":1,'
    b'"source_platform":"youtube"}'
)
UNKNOWN_CONTEXT_OPPORTUNITY_DIGEST = (
    "6c826d30b69f6ddb13c1ef19650685e6a37d1c80de70f398b42ffb91ecf27133"
)


def complete_opportunity() -> Opportunity:
    return Opportunity(
        schema_version=1,
        opportunity_id="opportunity.espresso",
        opportunity_version=1,
        market_id="market.india-en",
        niche_id="niche.home-espresso",
        source_platform=SourcePlatform.YOUTUBE,
        proposition="Beginner home espresso education for cost-conscious creators",
        language=KnownOpportunityContext(state="known", value="en"),
        region=UnknownOpportunityContext(state="unknown"),
    )


def test_valid_opportunity_creation_preserves_canonical_identity() -> None:
    value = complete_opportunity()

    assert value.opportunity_id == "opportunity.espresso"
    assert value.source_platform is SourcePlatform.YOUTUBE
    assert value.language == KnownOpportunityContext(state="known", value="en")
    assert value.region == UnknownOpportunityContext(state="unknown")


@pytest.mark.parametrize(
    "missing",
    (
        "schema_version",
        "opportunity_id",
        "opportunity_version",
        "market_id",
        "niche_id",
        "source_platform",
        "proposition",
        "language",
        "region",
    ),
)
def test_every_contract_field_is_required(missing: str) -> None:
    values = complete_opportunity().model_dump(mode="python")
    del values[missing]

    with pytest.raises(ValidationError):
        Opportunity(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("opportunity_id", ""),
        ("opportunity_id", "Opportunity One"),
        ("opportunity_version", 0),
        ("opportunity_version", True),
        ("opportunity_version", 1.0),
        ("opportunity_version", "1"),
        ("market_id", " "),
        ("niche_id", "Niche.One"),
        ("source_platform", "tiktok"),
        ("proposition", ""),
        ("proposition", " padded proposition "),
        ("language", {"state": "known", "value": ""}),
        ("language", {"state": "inferred", "value": "en"}),
        ("region", {"state": "unknown", "value": "IN"}),
        ("unexpected_field", "value"),
    ),
)
def test_invalid_values_and_schema_versions_are_rejected(
    field: str, value: object
) -> None:
    values = complete_opportunity().model_dump(mode="python")
    values[field] = value

    with pytest.raises(ValidationError):
        Opportunity(**values)


@pytest.mark.parametrize(
    ("left", "right"),
    (
        ("opportunity_id", "market_id"),
        ("opportunity_id", "niche_id"),
        ("market_id", "niche_id"),
    ),
)
def test_duplicate_identifiers_are_rejected(left: str, right: str) -> None:
    values = complete_opportunity().model_dump(mode="python")
    values[right] = values[left]

    with pytest.raises(ValidationError, match="identifiers must be unique"):
        Opportunity(**values)


def test_unknown_context_is_explicit_and_serializable() -> None:
    values = complete_opportunity().model_dump(mode="python")
    values["language"] = {"state": "unknown"}
    value = Opportunity(**values)

    assert value.language == UnknownOpportunityContext(state="unknown")
    assert OpportunityCanonicalizer.serialize(value) == UNKNOWN_CONTEXT_OPPORTUNITY_JSON
    assert (
        OpportunityCanonicalizer.calculate_digest(value)
        == UNKNOWN_CONTEXT_OPPORTUNITY_DIGEST
    )


def test_opportunity_and_nested_context_are_immutable() -> None:
    value = complete_opportunity()

    with pytest.raises(ValidationError):
        value.proposition = "A different proposition"
    with pytest.raises(ValidationError):
        value.language.value = "hi"  # type: ignore[union-attr]


def test_structural_equality_and_hashing_are_stable() -> None:
    first = complete_opportunity()
    second = complete_opportunity()
    changed = first.model_copy(update={"opportunity_version": 2})

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second, changed}) == 2
    assert first != changed


def test_canonical_serialization_and_digest_are_order_independent() -> None:
    first = complete_opportunity()
    second = Opportunity(
        region=UnknownOpportunityContext(state="unknown"),
        language=KnownOpportunityContext(value="en", state="known"),
        proposition="Beginner home espresso education for cost-conscious creators",
        source_platform=SourcePlatform.YOUTUBE,
        niche_id="niche.home-espresso",
        market_id="market.india-en",
        opportunity_version=1,
        opportunity_id="opportunity.espresso",
        schema_version=1,
    )

    first_bytes = OpportunityCanonicalizer.serialize(first)
    second_bytes = OpportunityCanonicalizer.serialize(second)
    assert first_bytes == COMPLETE_OPPORTUNITY_JSON
    assert first_bytes == second_bytes
    assert b"\n" not in first_bytes
    assert b": " not in first_bytes and b", " not in first_bytes
    assert OpportunityCanonicalizer.calculate_digest(first) == COMPLETE_OPPORTUNITY_DIGEST
    assert OpportunityCanonicalizer.calculate_digest(second) == COMPLETE_OPPORTUNITY_DIGEST


def test_canonicalizer_rejects_untyped_input() -> None:
    with pytest.raises(TypeError, match="opportunity must be Opportunity"):
        OpportunityCanonicalizer.serialize({})  # type: ignore[arg-type]


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(opportunity.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(opportunity, name) for name in exported)


def test_opportunity_dependency_boundary_and_startup_isolation() -> None:
    package = Path(opportunity.__file__).parent
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )
    prohibited_dependencies = (
        "app.api",
        "app.application",
        "app.db",
        "app.services.analytics",
        "app.services.backtesting",
        "app.services.creator_profile",
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
    assert "services.opportunity" not in application.read_text(encoding="utf-8")
