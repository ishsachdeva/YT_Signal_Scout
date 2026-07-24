"""Canonical serialization for immutable Evidence Manifests."""

from __future__ import annotations

import json
from hashlib import sha256

from app.services.evidence_manifest.models import EvidenceManifest


class EvidenceManifestCanonicalizer:
    """Emit stable compact UTF-8 JSON and SHA-256 content identity."""

    @staticmethod
    def serialize(manifest: EvidenceManifest) -> bytes:
        """Serialize one typed Evidence Manifest using its complete schema."""
        if not isinstance(manifest, EvidenceManifest):
            raise TypeError("manifest must be EvidenceManifest")
        return json.dumps(
            manifest.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(cls, manifest: EvidenceManifest) -> str:
        """Return the SHA-256 digest of canonical Evidence Manifest bytes."""
        return sha256(cls.serialize(manifest)).hexdigest()
