"""Typed application configuration loaded from an explicit environment allowlist."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "YT Signal Scout"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    youtube_api_key: str = ""
    youtube_timeout: float = 10.0
    youtube_max_retries: int = 3
    youtube_page_size: int = 25

    def __post_init__(self) -> None:
        if not self.app_name.strip():
            raise ValueError("APP_NAME must not be empty")
        if not self.app_version.strip():
            raise ValueError("APP_VERSION must not be empty")
        if self.environment not in {"development", "test", "staging", "production"}:
            raise ValueError(
                "ENVIRONMENT must be one of: development, test, staging, production"
            )
        if not self.api_v1_prefix.startswith("/") or self.api_v1_prefix.endswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/' and must not end with '/'")
        if self.api_v1_prefix == "/":
            raise ValueError("API_V1_PREFIX must not be '/' ")
        if self.log_level.upper() not in logging.getLevelNamesMapping():
            raise ValueError(f"Invalid LOG_LEVEL: {self.log_level}")
        if self.youtube_timeout <= 0:
            raise ValueError("YOUTUBE_TIMEOUT must be greater than zero")
        if self.youtube_max_retries < 0:
            raise ValueError("YOUTUBE_MAX_RETRIES must be zero or greater")
        if not 1 <= self.youtube_page_size <= 50:
            raise ValueError("YOUTUBE_PAGE_SIZE must be between 1 and 50")

        object.__setattr__(self, "log_level", self.log_level.upper())

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if environ is None else environ
        defaults = cls()
        return cls(
            app_name=source.get("APP_NAME", defaults.app_name),
            app_version=source.get("APP_VERSION", defaults.app_version),
            environment=source.get("ENVIRONMENT", defaults.environment),
            debug=_parse_boolean(source.get("DEBUG", "false")),
            api_v1_prefix=source.get("API_V1_PREFIX", defaults.api_v1_prefix),
            log_level=source.get("LOG_LEVEL", defaults.log_level),
            youtube_api_key=source.get("YOUTUBE_API_KEY", defaults.youtube_api_key),
            youtube_timeout=_parse_float(
                source.get("YOUTUBE_TIMEOUT", str(defaults.youtube_timeout)),
                name="YOUTUBE_TIMEOUT",
            ),
            youtube_max_retries=_parse_integer(
                source.get("YOUTUBE_MAX_RETRIES", str(defaults.youtube_max_retries)),
                name="YOUTUBE_MAX_RETRIES",
            ),
            youtube_page_size=_parse_integer(
                source.get("YOUTUBE_PAGE_SIZE", str(defaults.youtube_page_size)),
                name="YOUTUBE_PAGE_SIZE",
            ),
        )


def _parse_boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError("DEBUG must be either 'true' or 'false'")


def _parse_float(value: str, *, name: str) -> float:
    try:
        return float(value)
    except ValueError as exception:
        raise ValueError(f"{name} must be a number") from exception


def _parse_integer(value: str, *, name: str) -> int:
    try:
        return int(value)
    except ValueError as exception:
        raise ValueError(f"{name} must be an integer") from exception
