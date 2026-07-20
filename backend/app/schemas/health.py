"""Operational health response contracts."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: Literal["ready"] = "ready"
    service: str
    version: str
    checks: dict[str, Any] = Field(default_factory=dict)
