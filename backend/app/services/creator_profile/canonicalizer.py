"""Canonical serialization for immutable personal Creator Profiles."""

from __future__ import annotations

import json
from hashlib import sha256

from app.services.creator_profile.models import CreatorProfile


class CreatorProfileCanonicalizer:
    """Emit stable compact UTF-8 JSON and SHA-256 content identity."""

    @staticmethod
    def serialize(profile: CreatorProfile) -> bytes:
        """Serialize one typed profile without omitting explicit Unknown values."""
        if not isinstance(profile, CreatorProfile):
            raise TypeError("profile must be CreatorProfile")
        return json.dumps(
            profile.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(cls, profile: CreatorProfile) -> str:
        """Return the SHA-256 digest of canonical profile bytes."""
        return sha256(cls.serialize(profile)).hexdigest()
