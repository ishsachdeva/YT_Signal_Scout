"""Canonical serialization for immutable Product Opportunities."""

from __future__ import annotations

import json
from hashlib import sha256

from app.services.opportunity.models import Opportunity


class OpportunityCanonicalizer:
    """Emit stable compact UTF-8 JSON and SHA-256 content identity."""

    @staticmethod
    def serialize(opportunity: Opportunity) -> bytes:
        """Serialize one typed Opportunity using its complete schema."""
        if not isinstance(opportunity, Opportunity):
            raise TypeError("opportunity must be Opportunity")
        return json.dumps(
            opportunity.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(cls, opportunity: Opportunity) -> str:
        """Return the SHA-256 digest of canonical Opportunity bytes."""
        return sha256(cls.serialize(opportunity)).hexdigest()
