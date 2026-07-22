import logging
from typing import (
    Any,
)
from fastapi import (
    Request,
    status,
)
from fastapi.encoders import (
    jsonable_encoder,
)
from fastapi.responses import (
    JSONResponse,
)
from app.core.security.redaction import (
    REDACTED,
    is_sensitive_key,
    redact_sensitive_data,
    redact_sensitive_text,
)
from app.utils.responses import (
    error_response,
)
logger = logging.getLogger(
    "app.exceptions"
)
def _make_json_safe(
    value: Any,
) -> Any:
    """
    Preserve the established helper while
    applying recursive credential redaction.
    """
    return redact_sensitive_data(
        value
    )
def _request_id(
    request: Request,
) -> str | None:
    return getattr(
        request.state,
        "request_id",
        None,
    )
def _response_headers(
    request: Request,
    existing: (
        dict[str, str] | None
    ) = None,
) -> dict[str, str]:
    headers = dict(
        existing or {}
    )
    request_id = _request_id(
        request
    )
    if request_id:
        headers[
            "X-Request-ID"
        ] = request_id
    return headers
def _location_is_sensitive(
    location,
) -> bool:
    return any(
        is_sensitive_key(part)
        for part in (
            location or ()
        )
    )
def sanitize_validation_errors(
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sanitized = []
    for error in errors:
        item = dict(error)
        location = item.get(
            "loc",
            (),
        )
        sensitive_location = (
            _location_is_sensitive(
                location
            )
        )
        if "input" in item:
            if sensitive_location:
                item["input"] = REDACTED
            else:
                item["input"] = (
                    redact_sensitive_data(
                        item["input"]
                    )
                )
        if "ctx" in item:
            item["ctx"] = (
                redact_sensitive_data(
                    item["ctx"]
                )
            )
        if "msg" in item:
            item["msg"] = (
                redact_sensitive_text(
                    str(item["msg"])
                )
            )
        sanitized.append(
            redact_sensitive_data(
                item
            )
        )
    return sanitized
async def http_exception_handler(
    request: Request,
    exc,
):
    safe_detail = (
        redact_sensitive_data(
            exc.detail
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        headers=_response_headers(
            request,
            getattr(
                exc,
                "headers",
                None,
            ),
        ),
        content=error_response(
            message=safe_detail,
            errors=None,
        ),
    )
async def validation_exception_handler(
    request: Request,
    exc,
):
    safe_errors = jsonable_encoder(
        sanitize_validation_errors(
            exc.errors()
        )
    )
    return JSONResponse(
        status_code=(
            status
            .HTTP_422_UNPROCESSABLE_CONTENT
        ),
        headers=_response_headers(
            request
        ),
        content=error_response(
            message="Validation error",
            errors=safe_errors,
        ),
    )
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.error(
        (
            "unhandled_exception "
            "method=%s "
            "path=%s "
            "request_id=%s "
            "exception_type=%s"
        ),
        request.method,
        request.url.path,
        _request_id(request)
        or "unavailable",
        exc.__class__.__name__,
    )
    return JSONResponse(
        status_code=(
            status
            .HTTP_500_INTERNAL_SERVER_ERROR
        ),
        headers=_response_headers(
            request
        ),
        content=error_response(
            message=(
                "Internal server error"
            ),
            errors=None,
        ),
    )
