"""Version 1 product endpoint composition point."""

from fastapi import APIRouter


def build_v1_router() -> APIRouter:
    return APIRouter()
