"""Operational and root endpoints."""

from fastapi import APIRouter, Request

from app.core.config import Settings
from app.schemas.common import RootResponse
from app.schemas.health import LivenessResponse, ReadinessResponse


def build_operational_router() -> APIRouter:
    router = APIRouter()

    @router.get("/", response_model=RootResponse)
    async def root(request: Request) -> RootResponse:
        settings = _settings(request)
        return RootResponse(
            name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
            docs="/docs",
            health="/health/live",
        )

    @router.get("/health/live", response_model=LivenessResponse)
    async def live(request: Request) -> LivenessResponse:
        settings = _settings(request)
        return LivenessResponse(service=settings.app_name, version=settings.app_version)

    @router.get("/health/ready", response_model=ReadinessResponse)
    async def ready(request: Request) -> ReadinessResponse:
        settings = _settings(request)
        return ReadinessResponse(service=settings.app_name, version=settings.app_version)

    return router


def _settings(request: Request) -> Settings:
    settings = request.app.state.settings
    if not isinstance(settings, Settings):
        raise RuntimeError("Application settings are not configured")
    return settings
