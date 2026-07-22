import logging
import re
import time
from uuid import (
    uuid4,
)
from fastapi import (
    Request,
)
from app.core.security.redaction import (
    sanitize_request_target,
)
logger = logging.getLogger(
    "app.request"
)
_REQUEST_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9._-]{1,128}$"
)
def resolve_request_id(
    request: Request,
) -> str:
    candidate = (
        request.headers.get(
            "x-request-id",
            "",
        )
        .strip()
    )
    if (
        candidate
        and _REQUEST_ID_PATTERN.fullmatch(
            candidate
        )
    ):
        return candidate
    return uuid4().hex
async def request_logger_middleware(
    request: Request,
    call_next,
):
    request_id = resolve_request_id(
        request
    )
    request.state.request_id = (
        request_id
    )
    target = sanitize_request_target(
        request.url.path,
        request.url.query,
    )
    started_at = (
        time.perf_counter()
    )
    try:
        response = await call_next(
            request
        )
    except Exception as error:
        duration_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000,
            2,
        )
        logger.error(
            (
                "request_failed "
                "method=%s "
                "target=%s "
                "status=500 "
                "duration_ms=%s "
                "request_id=%s "
                "exception_type=%s"
            ),
            request.method,
            target,
            duration_ms,
            request_id,
            error.__class__.__name__,
        )
        raise
    duration_ms = round(
        (
            time.perf_counter()
            - started_at
        )
        * 1000,
        2,
    )
    response.headers[
        "X-Request-ID"
    ] = request_id
    logger.info(
        (
            "request_completed "
            "method=%s "
            "target=%s "
            "status=%s "
            "duration_ms=%s "
            "request_id=%s"
        ),
        request.method,
        target,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response
