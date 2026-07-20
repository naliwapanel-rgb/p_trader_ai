from fastapi import (
    HTTPException,
    Request,
    status,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
def get_automation_runtime(
    request: Request,
) -> AutomationRuntime:
    runtime = getattr(
        request.app.state,
        "automation_runtime",
        None,
    )
    if not isinstance(
        runtime,
        AutomationRuntime,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Automation runtime is "
                "not available"
            ),
        )
    return runtime
