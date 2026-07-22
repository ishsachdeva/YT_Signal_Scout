"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import build_operational_router
from app.api.router import build_api_router
from app.core.config import Settings
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging
from app.services.analytics.composition import (
    build_subscriber_relative_analytics_service,
)

logger = logging.getLogger(__name__)


def create_application(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    configure_logging(resolved_settings.log_level)

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        description="Backend API for YT Signal Scout.",
        # Starlette debug responses may contain tracebacks; API errors must stay safe.
        debug=False,
        lifespan=_build_lifespan(resolved_settings),
    )
    application.state.settings = resolved_settings
    application.state.api_v1_prefix = resolved_settings.api_v1_prefix
    application.state.subscriber_relative_analytics_service = (
        build_subscriber_relative_analytics_service()
    )

    install_exception_handlers(application)
    application.include_router(build_operational_router())
    application.include_router(build_api_router(resolved_settings.api_v1_prefix))
    return application


def _build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        del application
        logger.info(
            "Service starting",
            extra={
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "environment": settings.environment,
            },
        )
        yield
        logger.info(
            "Service stopped",
            extra={
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "environment": settings.environment,
            },
        )

    return lifespan
