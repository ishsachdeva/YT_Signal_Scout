"""Shared API response contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class RootResponse(BaseModel):
    name: str
    version: str
    environment: str
    docs: str
    health: str
