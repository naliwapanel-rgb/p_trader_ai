import asyncio
import pytest
from pydantic import ValidationError
from app.schemas.automation import (
    AutomationIntervalSchedule,
)
from app.services.automation_scheduler_service import (
    AutomationIntervalScheduler,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
def build_worker() -> AutomationWorker:
    worker = AutomationWorker(
        id_factory=build_id_factory()
    )
    async def handler(payload):
        return payload
    worker.register_handler(
        "MARKET_SCAN",
        handler,
    )
    return worker
def build_id_factory():
    counter = 0
    def create_id():
        nonlocal counter
        counter += 1
        return f"job-{counter}"
    return create_id
def build_schedule(
    **updates,
) -> AutomationIntervalSchedule:
    values = {
        "schedule_id": "market-scan",
        "job_type": "market_scan",
        "interval_seconds": 5,
        "payload": {
            "category": "spot",
        },
    }
    values.update(updates)
    return AutomationIntervalSchedule(
        **values
    )
def test_schedule_normalizes_identifiers():
    schedule = AutomationIntervalSchedule(
        schedule_id=" market-scan ",
        job_type=" market_scan ",
        interval_seconds=5,
        deduplication_key=(
            " scanner:spot "
        ),
    )
    assert schedule.schedule_id == (
        "market-scan"
    )
    assert schedule.job_type == (
        "MARKET_SCAN"
    )
    assert schedule.deduplication_key == (
        "scanner:spot"
    )
def test_schedule_rejects_invalid_interval():
    with pytest.raises(
        ValidationError
    ):
        AutomationIntervalSchedule(
            schedule_id="market-scan",
            job_type="MARKET_SCAN",
            interval_seconds=0,
        )
def test_registration_requires_worker_handler():
    worker = AutomationWorker()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker
        )
    )
    with pytest.raises(
        ValueError,
        match="No worker handler",
    ):
        scheduler.register_schedule(
            build_schedule()
        )
def test_duplicate_schedule_is_rejected():
    worker = build_worker()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker
        )
    )
    scheduler.register_schedule(
        build_schedule()
    )
    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        scheduler.register_schedule(
            build_schedule()
        )
@pytest.mark.asyncio
async def test_run_once_submits_and_tracks_job():
    worker = build_worker()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker,
            clock_ms=lambda: 1000,
        )
    )
    scheduler.register_schedule(
        build_schedule()
    )
    result = await scheduler.run_once(
        "market-scan"
    )
    assert result.created is True
    assert result.job.id == "job-1"
    state = scheduler.get_state(
        "market-scan"
    )
    assert state is not None
    assert state.submission_count == 1
    assert state.created_job_count == 1
    assert (
        state.duplicate_submission_count
        == 0
    )
    assert state.last_job_id == "job-1"
    assert state.last_submitted_at_ms == 1000
    assert state.next_run_at_ms == 6000
@pytest.mark.asyncio
async def test_default_key_prevents_overlap():
    worker = build_worker()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker,
            clock_ms=lambda: 1000,
        )
    )
    scheduler.register_schedule(
        build_schedule()
    )
    first = await scheduler.run_once(
        "market-scan"
    )
    duplicate = await scheduler.run_once(
        "market-scan"
    )
    assert first.created is True
    assert duplicate.created is False
    assert duplicate.job.id == (
        first.job.id
    )
    state = scheduler.get_state(
        "market-scan"
    )
    assert state is not None
    assert state.submission_count == 2
    assert state.created_job_count == 1
    assert (
        state.duplicate_submission_count
        == 1
    )
@pytest.mark.asyncio
async def test_interval_loop_honors_max_runs():
    sleep_delays: list[float] = []
    async def sleep_func(
        delay: float,
    ) -> None:
        sleep_delays.append(delay)
    worker = build_worker()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker,
            clock_ms=lambda: 1000,
            sleep_func=sleep_func,
        )
    )
    scheduler.register_schedule(
        build_schedule(
            initial_delay_seconds=2,
            max_runs=2,
        )
    )
    assert (
        await scheduler.start_schedule(
            "market-scan"
        )
        is True
    )
    await scheduler.wait_until_stopped()
    state = scheduler.get_state(
        "market-scan"
    )
    assert state is not None
    assert state.running is False
    assert state.submission_count == 2
    assert sleep_delays == [
        2,
        5,
    ]
    snapshot = scheduler.snapshot()
    assert snapshot.total_submissions == 2
    assert snapshot.total_created_jobs == 1
    assert (
        snapshot
        .total_duplicate_submissions
        == 1
    )
@pytest.mark.asyncio
async def test_disabled_schedule_does_not_start():
    worker = build_worker()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker
        )
    )
    scheduler.register_schedule(
        build_schedule(
            enabled=False
        )
    )
    started = (
        await scheduler.start_schedule(
            "market-scan"
        )
    )
    assert started is False
    snapshot = scheduler.snapshot()
    assert snapshot.running_schedule_count == 0
    assert snapshot.total_submissions == 0
@pytest.mark.asyncio
async def test_start_all_runs_enabled_schedules():
    worker = build_worker()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker,
            clock_ms=lambda: 1000,
            sleep_func=(
                lambda delay:
                asyncio.sleep(0)
            ),
        )
    )
    scheduler.register_schedule(
        build_schedule(
            schedule_id="spot-scan",
            max_runs=1,
        )
    )
    scheduler.register_schedule(
        build_schedule(
            schedule_id="linear-scan",
            payload={
                "category": "linear",
            },
            max_runs=1,
        )
    )
    started_count = (
        await scheduler.start_all()
    )
    assert started_count == 2
    await scheduler.wait_until_stopped()
    snapshot = scheduler.snapshot()
    assert (
        snapshot.registered_schedule_count
        == 2
    )
    assert snapshot.total_submissions == 2
    assert snapshot.total_created_jobs == 2
@pytest.mark.asyncio
async def test_submission_failure_is_recorded():
    worker = build_worker()
    await worker.stop()
    scheduler = (
        AutomationIntervalScheduler(
            worker=worker,
            clock_ms=lambda: 1000,
        )
    )
    scheduler.register_schedule(
        build_schedule()
    )
    with pytest.raises(
        RuntimeError,
        match="not accepting jobs",
    ):
        await scheduler.run_once(
            "market-scan"
        )
    state = scheduler.get_state(
        "market-scan"
    )
    assert state is not None
    assert state.submission_count == 1
    assert state.failure_count == 1
    assert state.last_error == (
        "Automation worker is not "
        "accepting jobs"
    )
    snapshot = scheduler.snapshot()
    assert snapshot.total_failures == 1
