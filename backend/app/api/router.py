"""Top-level product API router composition."""

from fastapi import APIRouter

from app.api.v1.router import build_v1_router


def build_api_router(prefix: str) -> APIRouter:
    router = APIRouter(prefix=prefix)
    router.include_router(build_v1_router())
    return router
