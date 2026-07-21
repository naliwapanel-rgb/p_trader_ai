from typing import Any
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
from app.utils.responses import (
    error_response,
)
def _make_json_safe(
    value: Any,
) -> Any:
    """
    Convert exception objects and nested validation
    context into JSON-safe response values.
    """
    if isinstance(
        value,
        BaseException,
    ):
        return str(value)
    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _make_json_safe(item)
            for key, item in value.items()
        }
    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            _make_json_safe(item)
            for item in value
        ]
    return value
async def http_exception_handler(
    request: Request,
    exc,
):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            errors=None,
        ),
    )
async def validation_exception_handler(
    request: Request,
    exc,
):
    safe_errors = jsonable_encoder(
        _make_json_safe(
            exc.errors()
        )
    )
    return JSONResponse(
        status_code=(
            status
            .HTTP_422_UNPROCESSABLE_CONTENT
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
    return JSONResponse(
        status_code=(
            status
            .HTTP_500_INTERNAL_SERVER_ERROR
        ),
        content=error_response(
            message="Internal server error",
            errors=None,
        ),
    )
