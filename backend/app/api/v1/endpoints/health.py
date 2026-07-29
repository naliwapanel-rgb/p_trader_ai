from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import (
    JSONResponse,
)
from sqlalchemy import (
    text,
)

from app.core.config import (
    get_settings,
)
from app.database.session import (
    engine,
)
from app.monitoring.metrics import (
    metrics_response,
    set_readiness_component,
)


router = APIRouter()
settings = get_settings()


def database_is_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )
        return True
    except Exception:
        return False


def automation_is_ready(
    request: Request,
) -> tuple[bool, str]:
    if not (
        settings
        .automation_runtime_enabled
    ):
        return True, "disabled"

    runtime = getattr(
        request.app.state,
        "automation_runtime",
        None,
    )

    if runtime is None:
        return False, "unavailable"

    try:
        runtime_health = (
            runtime.health()
        )
    except Exception:
        return False, "unhealthy"

    if runtime_health.healthy:
        return True, "healthy"

    return False, "unhealthy"


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": (
            settings.environment
        ),
        "version": settings.app_version,
    }


@router.get("/live")
async def liveness_check():
    return {
        "status": "alive",
        "environment": (
            settings.environment
        ),
        "version": settings.app_version,
    }


@router.get("/ready")
async def readiness_check(
    request: Request,
):
    database_ready = (
        database_is_ready()
    )
    (
        automation_ready,
        automation_status,
    ) = automation_is_ready(
        request
    )

    set_readiness_component(
        "database",
        database_ready,
    )
    set_readiness_component(
        "automation",
        automation_ready,
    )

    ready = (
        database_ready
        and automation_ready
    )

    payload = {
        "status": (
            "ready"
            if ready
            else "not_ready"
        ),
        "environment": (
            settings.environment
        ),
        "version": settings.app_version,
        "components": {
            "database": (
                "healthy"
                if database_ready
                else "unhealthy"
            ),
            "automation": (
                automation_status
            ),
        },
    }

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if ready
            else (
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            )
        ),
        content=payload,
    )


@router.get(
    "/metrics",
    include_in_schema=False,
)
async def prometheus_metrics():
    if not settings.metrics_enabled:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Not found",
        )

    return metrics_response()
