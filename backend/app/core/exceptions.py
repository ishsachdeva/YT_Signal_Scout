"""Application exception types and normalized HTTP handlers."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """A safe, intentional application failure suitable for an API response."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def install_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(ApplicationError, _application_error_handler)
    application.add_exception_handler(RequestValidationError, _validation_error_handler)
    application.add_exception_handler(StarletteHTTPException, _http_error_handler)
    application.add_exception_handler(Exception, _unexpected_error_handler)


async def _application_error_handler(
    request: Request, exception: Exception
) -> JSONResponse:
    del request
    error = exception
    if not isinstance(error, ApplicationError):
        raise TypeError("Expected ApplicationError")
    return _error_response(
        status_code=error.status_code,
        code=error.code,
        message=error.message,
        details=error.details,
    )


async def _validation_error_handler(
    request: Request, exception: Exception
) -> JSONResponse:
    del request
    error = exception
    if not isinstance(error, RequestValidationError):
        raise TypeError("Expected RequestValidationError")
    details = [
        {"type": item["type"], "location": list(item["loc"]), "message": item["msg"]}
        for item in error.errors()
    ]
    return _error_response(
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        details=details,
    )


async def _http_error_handler(request: Request, exception: Exception) -> JSONResponse:
    del request
    error = exception
    if not isinstance(error, StarletteHTTPException):
        raise TypeError("Expected HTTPException")
    code = "not_found" if error.status_code == 404 else "http_error"
    message = "Resource not found" if error.status_code == 404 else str(error.detail)
    return _error_response(status_code=error.status_code, code=code, message=message)


async def _unexpected_error_handler(
    request: Request, exception: Exception
) -> JSONResponse:
    logger.exception(
        "Unhandled request exception",
        exc_info=exception,
        extra={"request_method": request.method, "request_path": request.url.path},
    )
    return _error_response(
        status_code=500,
        code="internal_server_error",
        message="An unexpected error occurred",
    )


def _error_response(
    *, status_code: int, code: str, message: str, details: Any = None
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details, request_id=None)
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
