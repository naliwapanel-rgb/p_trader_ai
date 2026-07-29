import time

from fastapi import (
    Request,
)
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import (
    Response,
)


REQUESTS_TOTAL = Counter(
    "p_trader_ai_http_requests_total",
    (
        "Total number of HTTP requests "
        "processed."
    ),
    (
        "method",
        "route",
        "status_code",
    ),
)

REQUEST_DURATION_SECONDS = Histogram(
    (
        "p_trader_ai_http_request_"
        "duration_seconds"
    ),
    (
        "HTTP request processing duration "
        "in seconds."
    ),
    (
        "method",
        "route",
    ),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
)

REQUESTS_IN_PROGRESS = Gauge(
    (
        "p_trader_ai_http_requests_"
        "in_progress"
    ),
    (
        "Current number of HTTP requests "
        "being processed."
    ),
    ("method",),
)

READINESS_COMPONENT = Gauge(
    (
        "p_trader_ai_readiness_"
        "component"
    ),
    (
        "Readiness state of an application "
        "component."
    ),
    ("component",),
)


def resolve_route_template(
    request: Request,
) -> str:
    route = request.scope.get(
        "route"
    )
    route_path = getattr(
        route,
        "path",
        None,
    )

    if (
        isinstance(route_path, str)
        and route_path
    ):
        return route_path

    return "unmatched"


def set_readiness_component(
    component: str,
    healthy: bool,
) -> None:
    READINESS_COMPONENT.labels(
        component=component
    ).set(
        1 if healthy else 0
    )


async def metrics_middleware(
    request: Request,
    call_next,
):
    method = request.method.upper()
    started_at = time.perf_counter()
    status_code = 500

    REQUESTS_IN_PROGRESS.labels(
        method=method
    ).inc()

    try:
        response = await call_next(
            request
        )
        status_code = (
            response.status_code
        )
        return response
    finally:
        duration = (
            time.perf_counter()
            - started_at
        )
        route = resolve_route_template(
            request
        )

        REQUESTS_TOTAL.labels(
            method=method,
            route=route,
            status_code=str(
                status_code
            ),
        ).inc()

        REQUEST_DURATION_SECONDS.labels(
            method=method,
            route=route,
        ).observe(duration)

        REQUESTS_IN_PROGRESS.labels(
            method=method
        ).dec()


def metrics_response() -> Response:
    return Response(
        content=generate_latest(),
        headers={
            "Content-Type": (
                CONTENT_TYPE_LATEST
            ),
        },
    )
