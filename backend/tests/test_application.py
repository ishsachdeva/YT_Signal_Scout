from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi import APIRouter, FastAPI, Query
from fastapi.testclient import TestClient

from app.api.router import build_api_router
from app.application import create_application
from app.core.config import Settings
from app.core.exceptions import ApplicationError


def _test_settings() -> Settings:
    return Settings(
        app_name="Test Scout",
        app_version="9.8.7",
        environment="test",
        debug=False,
        api_v1_prefix="/custom/v1",
        log_level="CRITICAL",
    )


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = _test_settings()
        self.application = create_application(self.settings)
        self.client = TestClient(self.application, raise_server_exceptions=False)

    def test_factory_returns_fastapi_with_injected_metadata(self) -> None:
        self.assertIsInstance(self.application, FastAPI)
        self.assertEqual(self.application.title, "Test Scout")
        self.assertEqual(self.application.version, "9.8.7")

    def test_application_can_be_constructed_more_than_once(self) -> None:
        first = create_application(self.settings)
        second = create_application(self.settings)
        self.assertIsNot(first, second)

    def test_liveness_uses_injected_settings(self) -> None:
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "Test Scout", "version": "9.8.7"},
        )

    def test_readiness_uses_injected_settings(self) -> None:
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ready",
                "service": "Test Scout",
                "version": "9.8.7",
                "checks": {},
            },
        )

    def test_root_returns_service_metadata(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "name": "Test Scout",
                "version": "9.8.7",
                "environment": "test",
                "docs": "/docs",
                "health": "/health/live",
            },
        )

    def test_versioned_router_uses_configured_prefix(self) -> None:
        self.assertEqual(self.application.state.api_v1_prefix, "/custom/v1")
        self.assertEqual(build_api_router("/custom/v1").prefix, "/custom/v1")

    def test_unknown_route_uses_normalized_error(self) -> None:
        response = self.client.get("/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Resource not found",
                    "details": None,
                    "request_id": None,
                }
            },
        )

    def test_validation_error_uses_normalized_error(self) -> None:
        router = APIRouter()

        @router.get("/validate")
        async def validate(limit: int = Query(ge=1)) -> dict[str, int]:
            return {"limit": limit}

        self.application.include_router(router)
        response = self.client.get("/validate", params={"limit": "invalid"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "validation_error")
        self.assertIsInstance(response.json()["error"]["details"], list)

    def test_application_error_uses_normalized_error(self) -> None:
        router = APIRouter()

        @router.get("/application-error")
        async def application_error() -> None:
            raise ApplicationError(code="conflict", message="Safe conflict", status_code=409)

        self.application.include_router(router)
        response = self.client.get("/application-error")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "conflict")
        self.assertEqual(response.json()["error"]["message"], "Safe conflict")

    def test_unexpected_error_does_not_leak_original_message(self) -> None:
        router = APIRouter()

        @router.get("/unexpected-error")
        async def unexpected_error() -> None:
            raise RuntimeError("private implementation detail")

        self.application.include_router(router)
        response = self.client.get("/unexpected-error")
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["error"]["code"], "internal_server_error")
        self.assertNotIn("private implementation detail", response.text)

    def test_debug_setting_does_not_enable_traceback_responses(self) -> None:
        debug_application = create_application(
            Settings(environment="test", debug=True, log_level="CRITICAL")
        )
        router = APIRouter()

        @router.get("/debug-error")
        async def debug_error() -> None:
            raise RuntimeError("private debug detail")

        debug_application.include_router(router)
        client = TestClient(debug_application, raise_server_exceptions=False)
        response = client.get("/debug-error")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private debug detail", response.text)
        self.assertNotIn("Traceback", response.text)


class SettingsTests(unittest.TestCase):
    def test_defaults_do_not_depend_on_process_environment_when_mapping_is_injected(self) -> None:
        with patch.dict(os.environ, {"APP_NAME": "Machine-specific"}, clear=True):
            settings = Settings.from_environment({})
        self.assertEqual(settings, Settings())

    def test_supported_environment_values_are_loaded(self) -> None:
        settings = Settings.from_environment(
            {
                "APP_NAME": "Configured Scout",
                "APP_VERSION": "1.2.3",
                "ENVIRONMENT": "staging",
                "DEBUG": "true",
                "API_V1_PREFIX": "/v1",
                "LOG_LEVEL": "warning",
                "YOUTUBE_API_KEY": "test-key",
                "YOUTUBE_TIMEOUT": "4.5",
                "YOUTUBE_MAX_RETRIES": "2",
                "YOUTUBE_PAGE_SIZE": "40",
                "UNRELATED_SECRET": "must-not-be-read",
            }
        )
        self.assertTrue(settings.debug)
        self.assertEqual(settings.log_level, "WARNING")
        self.assertEqual(settings.youtube_api_key, "test-key")
        self.assertEqual(settings.youtube_timeout, 4.5)
        self.assertEqual(settings.youtube_max_retries, 2)
        self.assertEqual(settings.youtube_page_size, 40)

    def test_invalid_boolean_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "DEBUG"):
            Settings.from_environment({"DEBUG": "yes"})

    def test_invalid_environment_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "ENVIRONMENT"):
            Settings(environment="local")

    def test_invalid_log_level_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "LOG_LEVEL"):
            Settings(log_level="verbose")

    def test_invalid_youtube_configuration_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "YOUTUBE_TIMEOUT"):
            Settings.from_environment({"YOUTUBE_TIMEOUT": "never"})
        with self.assertRaisesRegex(ValueError, "YOUTUBE_MAX_RETRIES"):
            Settings(youtube_max_retries=-1)
        with self.assertRaisesRegex(ValueError, "YOUTUBE_PAGE_SIZE"):
            Settings(youtube_page_size=51)


if __name__ == "__main__":
    unittest.main()
