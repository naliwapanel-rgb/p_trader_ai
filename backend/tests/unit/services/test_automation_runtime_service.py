import asyncio
import pytest
from app.schemas.automation import (
    AutomationIntervalSchedule,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
from app.services.automation_scheduler_service import (
    AutomationIntervalScheduler,
)
from app.services.automation_trade_execution_service import (
    AutomatedTradeExecutionService,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
def test_runtime_owns_worker_and_scheduler():
    runtime = AutomationRuntime()
    assert runtime.scheduler.worker is runtime.worker
    assert runtime.started is False
    assert runtime.handlers_registered is True
def test_runtime_registers_trade_handlers_once():
    runtime = AutomationRuntime()
    snapshot = runtime.worker.snapshot()
    assert snapshot.registered_job_types == [
        AutomatedTradeExecutionService
        .LIMIT_ORDER_JOB_TYPE,
        AutomatedTradeExecutionService
        .MARKET_ORDER_JOB_TYPE,
    ]
    assert (
        runtime.register_handlers_once()
        is False
    )
    assert (
        runtime.worker
        .snapshot()
        .registered_job_types
        == snapshot.registered_job_types
    )
def test_runtime_rejects_scheduler_with_other_worker():
    runtime_worker = AutomationWorker()
    other_worker = AutomationWorker()
    scheduler = AutomationIntervalScheduler(
        worker=other_worker
    )
    with pytest.raises(
        ValueError,
        match=(
            "Automation scheduler must use "
            "the runtime worker"
        ),
    ):
        AutomationRuntime(
            worker=runtime_worker,
            scheduler=scheduler,
        )
def test_runtime_start_and_stop_are_idempotent():
    async def scenario():
        runtime = AutomationRuntime()
        initial_health = runtime.health()
        assert initial_health.healthy is False
        assert initial_health.started is False
        assert (
            initial_health
            .handlers_registered
            is True
        )
        assert (
            initial_health.worker.running
            is False
        )
        assert await runtime.start() is True
        assert await runtime.start() is False
        running_health = runtime.health()
        assert running_health.healthy is True
        assert running_health.started is True
        assert (
            running_health.worker.running
            is True
        )
        assert (
            running_health
            .worker
            .accepting_jobs
            is True
        )
        assert await runtime.stop() is True
        assert await runtime.stop() is False
        stopped_health = runtime.health()
        assert stopped_health.healthy is False
        assert stopped_health.started is False
        assert (
            stopped_health.worker.running
            is False
        )
        assert (
            stopped_health
            .worker
            .accepting_jobs
            is False
        )
    asyncio.run(scenario())
def test_runtime_does_not_start_schedules_automatically():
    async def scenario():
        runtime = AutomationRuntime()
        runtime.scheduler.register_schedule(
            AutomationIntervalSchedule(
                schedule_id=(
                    "manual-start-only"
                ),
                job_type=(
                    AutomatedTradeExecutionService
                    .MARKET_ORDER_JOB_TYPE
                ),
                interval_seconds=60,
                initial_delay_seconds=60,
                payload={},
            )
        )
        assert await runtime.start() is True
        snapshot = runtime.scheduler.snapshot()
        assert (
            snapshot
            .registered_schedule_count
            == 1
        )
        assert (
            snapshot
            .running_schedule_count
            == 0
        )
        await runtime.stop()
    asyncio.run(scenario())
def test_runtime_gracefully_stops_running_schedules():
    async def scenario():
        runtime = AutomationRuntime()
        runtime.scheduler.register_schedule(
            AutomationIntervalSchedule(
                schedule_id=(
                    "graceful-stop-test"
                ),
                job_type=(
                    AutomatedTradeExecutionService
                    .LIMIT_ORDER_JOB_TYPE
                ),
                interval_seconds=60,
                initial_delay_seconds=60,
                payload={},
            )
        )
        await runtime.start()
        assert (
            await runtime.scheduler
            .start_schedule(
                "graceful-stop-test"
            )
            is True
        )
        assert (
            runtime.scheduler
            .snapshot()
            .running_schedule_count
            == 1
        )
        assert await runtime.stop() is True
        stopped_snapshot = (
            runtime.scheduler.snapshot()
        )
        assert (
            stopped_snapshot
            .running_schedule_count
            == 0
        )
        assert runtime.worker.is_running is False
    asyncio.run(scenario())
