"""Canonical serialization for immutable Opportunity Candidates."""

from __future__ import annotations

import json
from hashlib import sha256

from app.services.opportunity_candidate.models import OpportunityCandidate


class OpportunityCandidateCanonicalizer:
    """Emit stable compact UTF-8 JSON and SHA-256 content identity."""

    @staticmethod
    def serialize(candidate: OpportunityCandidate) -> bytes:
        """Serialize one typed Candidate using its complete schema."""
        if not isinstance(candidate, OpportunityCandidate):
            raise TypeError("candidate must be OpportunityCandidate")
        return json.dumps(
            candidate.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(cls, candidate: OpportunityCandidate) -> str:
        """Return the SHA-256 digest of canonical Candidate bytes."""
        return sha256(cls.serialize(candidate)).hexdigest()
