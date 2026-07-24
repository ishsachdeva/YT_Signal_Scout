"""Canonical serialization for immutable Qualification Contexts."""

from __future__ import annotations

import json
from hashlib import sha256

from app.services.qualification_context.models import QualificationContext


class QualificationContextCanonicalizer:
    """Emit stable compact UTF-8 JSON and SHA-256 content identity."""

    @staticmethod
    def serialize(context: QualificationContext) -> bytes:
        """Serialize one typed Qualification Context using its complete schema."""
        if not isinstance(context, QualificationContext):
            raise TypeError("context must be QualificationContext")
        return json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def calculate_digest(cls, context: QualificationContext) -> str:
        """Return the SHA-256 digest of canonical Qualification Context bytes."""
        return sha256(cls.serialize(context)).hexdigest()
