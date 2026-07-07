from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.utils.responses import error_response


async def http_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            errors=None,
        ),
    )


async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            message="Validation error",
            errors=exc.errors(),
        ),
    )


async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="Internal server error",
            errors=None,
        ),
    )