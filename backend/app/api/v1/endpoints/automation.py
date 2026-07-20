from typing import Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import ValidationError
from app.api.automation_dependencies import (
    get_automation_runtime,
)
from app.api.dependencies import (
    get_current_user,
)
from app.models.user import User
from app.schemas.automation import (
    AutomationIntervalSchedule,
    AutomationJob,
    AutomationJobSubmission,
    AutomationJobSubmissionResult,
    AutomationRuntimeHealth,
    AutomationScheduleActionResult,
    AutomationScheduleState,
    AutomationSchedulerSnapshot,
    AutomationWorkerSnapshot,
)
from app.schemas.automation_trade import (
    AutomatedLimitOrderJob,
    AutomatedMarketOrderJob,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
from app.services.automation_trade_execution_service import (
    AutomatedTradeExecutionService,
)
router = APIRouter(
    prefix="/automation",
    tags=["Automation"],
)
_TRADE_JOB_MODELS = {
    (
        AutomatedTradeExecutionService
        .MARKET_ORDER_JOB_TYPE
    ): AutomatedMarketOrderJob,
    (
        AutomatedTradeExecutionService
        .LIMIT_ORDER_JOB_TYPE
    ): AutomatedLimitOrderJob,
}
def _user_prefix(
    user_id: int,
) -> str:
    return f"user:{user_id}:"
def _internal_deduplication_key(
    *,
    user_id: int,
    key: str | None,
) -> str | None:
    if key is None:
        return None
    return (
        _user_prefix(user_id)
        + key
    )
def _internal_schedule_id(
    *,
    user_id: int,
    schedule_id: str,
) -> str:
    return (
        _user_prefix(user_id)
        + schedule_id
    )
def _public_job(
    *,
    job: AutomationJob,
    user_id: int,
) -> AutomationJob:
    prefix = _user_prefix(user_id)
    deduplication_key = (
        job.deduplication_key
    )
    if (
        deduplication_key is not None
        and deduplication_key.startswith(
            prefix
        )
    ):
        deduplication_key = (
            deduplication_key[
                len(prefix):
            ]
        )
    return job.model_copy(
        deep=True,
        update={
            "deduplication_key": (
                deduplication_key
            ),
        },
    )
def _public_schedule_state(
    *,
    state: AutomationScheduleState,
    user_id: int,
) -> AutomationScheduleState:
    prefix = _user_prefix(user_id)
    schedule_id = state.schedule_id
    if schedule_id.startswith(prefix):
        schedule_id = schedule_id[
            len(prefix):
        ]
    return state.model_copy(
        deep=True,
        update={
            "schedule_id": schedule_id,
        },
    )
def _job_belongs_to_user(
    *,
    job: AutomationJob,
    user_id: int,
) -> bool:
    return (
        job.payload.get("user_id")
        == user_id
    )
def _normalize_trade_submission(
    *,
    data: AutomationJobSubmission,
    current_user: User,
) -> AutomationJobSubmission:
    model = _TRADE_JOB_MODELS.get(
        data.job_type
    )
    if model is None:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Unsupported automation "
                f"job type: {data.job_type}"
            ),
        )
    payload = dict(data.payload)
    supplied_user_id = payload.get(
        "user_id"
    )
    if (
        supplied_user_id is not None
        and supplied_user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Automation jobs cannot be "
                "submitted for another user"
            ),
        )
    payload["user_id"] = (
        current_user.id
    )
    try:
        validated_payload = (
            model.model_validate(
                payload
            )
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "message": (
                    "Invalid automation "
                    "trade payload"
                ),
                "errors": exc.errors(
                    include_url=False
                ),
            },
        ) from exc
    return AutomationJobSubmission(
        job_type=data.job_type,
        payload=(
            validated_payload.model_dump(
                mode="json"
            )
        ),
        deduplication_key=(
            _internal_deduplication_key(
                user_id=current_user.id,
                key=data.deduplication_key,
            )
        ),
    )
def _user_jobs(
    *,
    runtime: AutomationRuntime,
    user_id: int,
) -> list[AutomationJob]:
    jobs = [
        job
        for job
        in runtime.worker.list_jobs()
        if _job_belongs_to_user(
            job=job,
            user_id=user_id,
        )
    ]
    jobs.sort(
        key=lambda job: (
            job.created_at_ms,
            job.id,
        ),
        reverse=True,
    )
    return jobs
def _user_worker_snapshot(
    *,
    runtime: AutomationRuntime,
    user_id: int,
) -> AutomationWorkerSnapshot:
    global_snapshot = (
        runtime.worker.snapshot()
    )
    jobs = _user_jobs(
        runtime=runtime,
        user_id=user_id,
    )
    counts = {
        "QUEUED": 0,
        "RUNNING": 0,
        "SUCCEEDED": 0,
        "FAILED": 0,
        "CANCELLED": 0,
    }
    for job in jobs:
        counts[job.status] += 1
    return AutomationWorkerSnapshot(
        running=global_snapshot.running,
        accepting_jobs=(
            global_snapshot
            .accepting_jobs
        ),
        queue_size=counts["QUEUED"],
        total_jobs=len(jobs),
        queued_count=counts["QUEUED"],
        running_count=counts["RUNNING"],
        succeeded_count=(
            counts["SUCCEEDED"]
        ),
        failed_count=counts["FAILED"],
        cancelled_count=(
            counts["CANCELLED"]
        ),
        total_attempts=sum(
            job.attempt_count
            for job in jobs
        ),
        retried_job_count=sum(
            1
            for job in jobs
            if job.retry_count > 0
        ),
        registered_job_types=(
            global_snapshot
            .registered_job_types
        ),
    )
def _user_scheduler_snapshot(
    *,
    runtime: AutomationRuntime,
    user_id: int,
) -> AutomationSchedulerSnapshot:
    prefix = _user_prefix(user_id)
    states = [
        _public_schedule_state(
            state=state,
            user_id=user_id,
        )
        for state
        in runtime.scheduler.list_states()
        if state.schedule_id.startswith(
            prefix
        )
    ]
    return AutomationSchedulerSnapshot(
        registered_schedule_count=(
            len(states)
        ),
        running_schedule_count=sum(
            1
            for state in states
            if state.running
        ),
        total_submissions=sum(
            state.submission_count
            for state in states
        ),
        total_created_jobs=sum(
            state.created_job_count
            for state in states
        ),
        total_duplicate_submissions=sum(
            state
            .duplicate_submission_count
            for state in states
        ),
        total_failures=sum(
            state.failure_count
            for state in states
        ),
        schedules=states,
    )
def _require_user_schedule(
    *,
    runtime: AutomationRuntime,
    current_user: User,
    schedule_id: str,
) -> str:
    internal_id = (
        _internal_schedule_id(
            user_id=current_user.id,
            schedule_id=schedule_id,
        )
    )
    definition = (
        runtime.scheduler.get_schedule(
            internal_id
        )
    )
    if definition is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Automation schedule "
                "was not found"
            ),
        )
    return internal_id
@router.get(
    "/health",
    response_model=AutomationRuntimeHealth,
)
async def automation_runtime_health(
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationRuntimeHealth:
    runtime_health = runtime.health()
    return AutomationRuntimeHealth(
        healthy=runtime_health.healthy,
        started=runtime_health.started,
        handlers_registered=(
            runtime_health
            .handlers_registered
        ),
        worker=_user_worker_snapshot(
            runtime=runtime,
            user_id=current_user.id,
        ),
        scheduler=(
            _user_scheduler_snapshot(
                runtime=runtime,
                user_id=current_user.id,
            )
        ),
    )
@router.get(
    "/worker",
    response_model=AutomationWorkerSnapshot,
)
async def automation_worker_snapshot(
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationWorkerSnapshot:
    return _user_worker_snapshot(
        runtime=runtime,
        user_id=current_user.id,
    )
@router.get(
    "/scheduler",
    response_model=(
        AutomationSchedulerSnapshot
    ),
)
async def automation_scheduler_snapshot(
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationSchedulerSnapshot:
    return _user_scheduler_snapshot(
        runtime=runtime,
        user_id=current_user.id,
    )
@router.post(
    "/jobs",
    response_model=(
        AutomationJobSubmissionResult
    ),
    status_code=(
        status.HTTP_202_ACCEPTED
    ),
)
async def submit_automation_job(
    data: AutomationJobSubmission,
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationJobSubmissionResult:
    normalized = (
        _normalize_trade_submission(
            data=data,
            current_user=current_user,
        )
    )
    try:
        result = await runtime.worker.submit(
            normalized
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc
    return AutomationJobSubmissionResult(
        job=_public_job(
            job=result.job,
            user_id=current_user.id,
        ),
        created=result.created,
    )
@router.get(
    "/jobs",
    response_model=list[AutomationJob],
)
async def list_automation_jobs(
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> list[AutomationJob]:
    return [
        _public_job(
            job=job,
            user_id=current_user.id,
        )
        for job
        in _user_jobs(
            runtime=runtime,
            user_id=current_user.id,
        )
    ]
@router.get(
    "/jobs/{job_id}",
    response_model=AutomationJob,
)
async def get_automation_job(
    job_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationJob:
    job = runtime.worker.get_job(
        job_id
    )
    if (
        job is None
        or not _job_belongs_to_user(
            job=job,
            user_id=current_user.id,
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Automation job "
                "was not found"
            ),
        )
    return _public_job(
        job=job,
        user_id=current_user.id,
    )
@router.post(
    "/schedules",
    response_model=AutomationScheduleState,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def register_automation_schedule(
    data: AutomationIntervalSchedule,
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationScheduleState:
    normalized_job = (
        _normalize_trade_submission(
            data=AutomationJobSubmission(
                job_type=data.job_type,
                payload=dict(data.payload),
                deduplication_key=(
                    data.deduplication_key
                ),
            ),
            current_user=current_user,
        )
    )
    internal_schedule = (
        data.model_copy(
            deep=True,
            update={
                "schedule_id": (
                    _internal_schedule_id(
                        user_id=(
                            current_user.id
                        ),
                        schedule_id=(
                            data.schedule_id
                        ),
                    )
                ),
                "job_type": (
                    normalized_job.job_type
                ),
                "payload": (
                    normalized_job.payload
                ),
                "deduplication_key": (
                    normalized_job
                    .deduplication_key
                ),
            },
        )
    )
    try:
        state = (
            runtime.scheduler
            .register_schedule(
                internal_schedule
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(exc),
        ) from exc
    return _public_schedule_state(
        state=state,
        user_id=current_user.id,
    )
@router.post(
    "/schedules/{schedule_id}/start",
    response_model=(
        AutomationScheduleActionResult
    ),
)
async def start_automation_schedule(
    schedule_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationScheduleActionResult:
    internal_id = _require_user_schedule(
        runtime=runtime,
        current_user=current_user,
        schedule_id=schedule_id,
    )
    changed = (
        await runtime.scheduler
        .start_schedule(internal_id)
    )
    state = runtime.scheduler.get_state(
        internal_id
    )
    if state is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Automation schedule "
                "was not found"
            ),
        )
    return AutomationScheduleActionResult(
        changed=changed,
        schedule=_public_schedule_state(
            state=state,
            user_id=current_user.id,
        ),
    )
@router.post(
    "/schedules/{schedule_id}/stop",
    response_model=(
        AutomationScheduleActionResult
    ),
)
async def stop_automation_schedule(
    schedule_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AutomationScheduleActionResult:
    internal_id = _require_user_schedule(
        runtime=runtime,
        current_user=current_user,
        schedule_id=schedule_id,
    )
    changed = (
        await runtime.scheduler
        .stop_schedule(internal_id)
    )
    state = runtime.scheduler.get_state(
        internal_id
    )
    if state is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Automation schedule "
                "was not found"
            ),
        )
    return AutomationScheduleActionResult(
        changed=changed,
        schedule=_public_schedule_state(
            state=state,
            user_id=current_user.id,
        ),
    )
