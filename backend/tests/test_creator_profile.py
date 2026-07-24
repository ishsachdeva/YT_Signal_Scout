"""Behavior-focused tests for deterministic Personal Creator Profile facts."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import app.services.creator_profile as creator_profile
from app.services.creator_profile import (
    AIAssistancePreference,
    CreatorProfile,
    CreatorProfileCanonicalizer,
    EditingCapability,
    NarrationPreference,
    PresentationStyle,
    ProductionBudgetCategory,
    UploadCadenceGoal,
)

COMPLETE_PROFILE_JSON = (
    b'{"ai_assistance_preference":"open",'
    b'"available_production_hours_per_week":12,'
    b'"editing_capability":"intermediate",'
    b'"language_preference":"en-in",'
    b'"narration_preference":"own_voice",'
    b'"preferred_presentation_style":"faceless",'
    b'"production_budget_category":"low",'
    b'"profile_id":"owner.default",'
    b'"profile_version":1,'
    b'"schema_version":1,'
    b'"target_geography":"IN",'
    b'"upload_cadence_goal":"weekly"}'
)
COMPLETE_PROFILE_DIGEST = (
    "890dd0b2cc6e67f90d39f518fa6d9137db3c6c04ccc298a2b2b4add0f9cb2094"
)
UNKNOWN_PROFILE_JSON = (
    b'{"ai_assistance_preference":null,'
    b'"available_production_hours_per_week":null,'
    b'"editing_capability":null,'
    b'"language_preference":null,'
    b'"narration_preference":null,'
    b'"preferred_presentation_style":null,'
    b'"production_budget_category":null,'
    b'"profile_id":"owner.default",'
    b'"profile_version":1,'
    b'"schema_version":1,'
    b'"target_geography":null,'
    b'"upload_cadence_goal":null}'
)


def complete_profile() -> CreatorProfile:
    return CreatorProfile(
        schema_version=1,
        profile_id="owner.default",
        profile_version=1,
        preferred_presentation_style=PresentationStyle.FACELESS,
        ai_assistance_preference=AIAssistancePreference.OPEN,
        language_preference="en-in",
        target_geography="IN",
        available_production_hours_per_week=12,
        editing_capability=EditingCapability.INTERMEDIATE,
        narration_preference=NarrationPreference.OWN_VOICE,
        production_budget_category=ProductionBudgetCategory.LOW,
        upload_cadence_goal=UploadCadenceGoal.WEEKLY,
    )


def test_valid_profile_creation_preserves_explicit_facts() -> None:
    profile = complete_profile()

    assert profile.profile_id == "owner.default"
    assert profile.preferred_presentation_style is PresentationStyle.FACELESS
    assert profile.available_production_hours_per_week == 12
    assert profile.target_geography == "IN"


@pytest.mark.parametrize("missing", ("schema_version", "profile_id", "profile_version"))
def test_required_identity_and_version_fields_cannot_be_omitted(missing: str) -> None:
    values = {
        "schema_version": 1,
        "profile_id": "owner.default",
        "profile_version": 1,
    }
    del values[missing]

    with pytest.raises(ValidationError):
        CreatorProfile(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("profile_id", "Owner Profile"),
        ("profile_version", 0),
        ("profile_version", True),
        ("profile_version", 1.0),
        ("profile_version", "1"),
        ("preferred_presentation_style", "sometimes_visible"),
        ("ai_assistance_preference", "delegate_everything"),
        ("language_preference", "EN_in"),
        ("target_geography", "India"),
        ("available_production_hours_per_week", -1),
        ("available_production_hours_per_week", 169),
        ("available_production_hours_per_week", True),
        ("available_production_hours_per_week", 12.0),
        ("available_production_hours_per_week", "12"),
        ("editing_capability", "expert"),
        ("narration_preference", "celebrity_clone"),
        ("production_budget_category", "unlimited"),
        ("upload_cadence_goal", "whenever_algorithm_demands"),
        ("unexpected_preference", "value"),
    ),
)
def test_invalid_or_unknown_values_are_rejected(field: str, value: object) -> None:
    values: dict[str, object] = {
        "schema_version": 1,
        "profile_id": "owner.default",
        "profile_version": 1,
        field: value,
    }

    with pytest.raises(ValidationError):
        CreatorProfile(**values)


def test_missing_optional_facts_remain_explicitly_unknown() -> None:
    profile = CreatorProfile(
        schema_version=1,
        profile_id="owner.default",
        profile_version=1,
    )

    assert profile.preferred_presentation_style is None
    assert profile.ai_assistance_preference is None
    assert profile.language_preference is None
    assert profile.target_geography is None
    assert profile.available_production_hours_per_week is None
    assert profile.editing_capability is None
    assert profile.narration_preference is None
    assert profile.production_budget_category is None
    assert profile.upload_cadence_goal is None

    assert CreatorProfileCanonicalizer.serialize(profile) == UNKNOWN_PROFILE_JSON


def test_explicit_zero_effort_is_distinct_from_unknown() -> None:
    profile = CreatorProfile(
        schema_version=1,
        profile_id="owner.default",
        profile_version=1,
        available_production_hours_per_week=0,
    )

    assert profile.available_production_hours_per_week == 0


def test_profile_is_immutable() -> None:
    profile = complete_profile()

    with pytest.raises(ValidationError):
        profile.language_preference = "hi"


def test_structurally_equal_profiles_are_equal() -> None:
    assert complete_profile() == complete_profile()


def test_serialization_and_digest_are_stable() -> None:
    first = complete_profile()
    second = CreatorProfile(
        upload_cadence_goal=UploadCadenceGoal.WEEKLY,
        production_budget_category=ProductionBudgetCategory.LOW,
        narration_preference=NarrationPreference.OWN_VOICE,
        editing_capability=EditingCapability.INTERMEDIATE,
        available_production_hours_per_week=12,
        target_geography="IN",
        language_preference="en-in",
        ai_assistance_preference=AIAssistancePreference.OPEN,
        preferred_presentation_style=PresentationStyle.FACELESS,
        profile_version=1,
        profile_id="owner.default",
        schema_version=1,
    )

    first_bytes = CreatorProfileCanonicalizer.serialize(first)
    second_bytes = CreatorProfileCanonicalizer.serialize(second)
    assert first_bytes == COMPLETE_PROFILE_JSON
    assert first_bytes == second_bytes
    assert b"\n" not in first_bytes and b" " not in first_bytes
    assert CreatorProfileCanonicalizer.calculate_digest(first) == COMPLETE_PROFILE_DIGEST
    assert CreatorProfileCanonicalizer.calculate_digest(second) == COMPLETE_PROFILE_DIGEST


def test_canonicalizer_rejects_untyped_input() -> None:
    with pytest.raises(TypeError, match="profile must be CreatorProfile"):
        CreatorProfileCanonicalizer.serialize({})  # type: ignore[arg-type]


def test_public_exports_are_complete_unique_and_importable() -> None:
    exported = tuple(creator_profile.__all__)
    assert len(exported) == len(set(exported))
    assert all(hasattr(creator_profile, name) for name in exported)


def test_creator_profile_dependency_boundary_and_startup_isolation() -> None:
    package = Path(creator_profile.__file__).parent
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )
    prohibited_dependencies = (
        "app.api",
        "app.application",
        "app.db",
        "app.services.analytics",
        "app.services.backtesting",
        "app.services.signals",
        "app.services.youtube",
        "fastapi",
        "sqlalchemy",
        "httpx",
        "openai",
    )
    assert all(name not in source for name in prohibited_dependencies)

    application = package.parents[1] / "application.py"
    assert "services.creator_profile" not in application.read_text(encoding="utf-8")
