"""Canonical serialization for immutable Evidence Snapshots."""

from __future__ import annotations

import json
from hashlib import sha256

from app.services.evidence_snapshot.models import EvidenceSnapshot


class EvidenceSnapshotCanonicalizer:
    """Emit stable compact UTF-8 JSON and SHA-256 content identity."""

    @staticmethod
    def serialize(snapshot: EvidenceSnapshot) -> bytes:
        """Serialize one typed Evidence Snapshot using its complete schema."""
        if not isinstance(snapshot, EvidenceSnapshot):
            raise TypeError("snapshot must be EvidenceSnapshot")
        return json.dumps(
            snapshot.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(cls, snapshot: EvidenceSnapshot) -> str:
        """Return the SHA-256 digest of canonical Evidence Snapshot bytes."""
        return sha256(cls.serialize(snapshot)).hexdigest()
