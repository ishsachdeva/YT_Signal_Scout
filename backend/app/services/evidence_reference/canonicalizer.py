"""Canonical serialization for immutable Evidence References."""

from __future__ import annotations

import json
from hashlib import sha256

from app.services.evidence_reference.models import EvidenceReference


class EvidenceReferenceCanonicalizer:
    """Emit stable compact UTF-8 JSON and SHA-256 content identity."""

    @staticmethod
    def serialize(reference: EvidenceReference) -> bytes:
        """Serialize one typed Evidence Reference using its complete schema."""
        if not isinstance(reference, EvidenceReference):
            raise TypeError("reference must be EvidenceReference")
        return json.dumps(
            reference.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(cls, reference: EvidenceReference) -> str:
        """Return the SHA-256 digest of canonical Evidence Reference bytes."""
        return sha256(cls.serialize(reference)).hexdigest()
