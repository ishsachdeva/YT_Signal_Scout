"""Central application logging configuration."""

from __future__ import annotations

import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Render predictable structured logs without an external dependency."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in (
            "app_name",
            "app_version",
            "environment",
            "request_method",
            "request_path",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_level: str) -> None:
    """Configure the root logger idempotently at the requested level."""
    normalized_level = log_level.upper()
    if normalized_level not in logging.getLevelNamesMapping():
        raise ValueError(f"Invalid log level: {log_level}")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "level": normalized_level,
                }
            },
            "root": {"handlers": ["console"], "level": normalized_level},
        }
    )
