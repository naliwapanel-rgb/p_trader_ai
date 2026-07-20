import asyncio
from collections.abc import Iterator
import pytest
from pydantic import ValidationError
from app.schemas.automation import (
    AutomationJobSubmission,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
def build_clock(
    values: list[int],
) -> callable:
    iterator: Iterator[int] = iter(values)
    return lambda: next(iterator)
def test_submission_normalizes_job_type_and_key():
    submission = AutomationJobSubmission(
        job_type=" portfolio_sync ",
        payload={
            "portfolio_id": 1,
        },
        deduplication_key=(
            " user-1:portfolio-1 "
        ),
    )
    assert submission.job_type == (
        "PORTFOLIO_SYNC"
    )
    assert submission.deduplication_key == (
        "user-1:portfolio-1"
    )
def test_submission_rejects_blank_deduplication_key():
    with pytest.raises(ValidationError):
        AutomationJobSubmission(
            job_type="MARKET_SCAN",
            deduplication_key=" ",
        )
@pytest.mark.asyncio
async def test_submit_requires_registered_handler():
    worker = AutomationWorker()
    with pytest.raises(
        ValueError,
        match="No handler is registered",
    ):
        await worker.submit(
            AutomationJobSubmission(
                job_type="MARKET_SCAN",
            )
        )
def test_duplicate_handler_registration_is_rejected():
    worker = AutomationWorker()
    async def handler(payload):
        return payload
    worker.register_handler(
        "market_scan",
        handler,
    )
    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        worker.register_handler(
            "MARKET_SCAN",
            handler,
        )
@pytest.mark.asyncio
async def test_run_once_completes_job():
    worker = AutomationWorker(
        clock_ms=build_clock(
            [
                100,
                200,
                300,
            ]
        ),
        id_factory=lambda: "job-1",
    )
    async def handler(payload):
        return {
            "received": payload["value"],
        }
    worker.register_handler(
        "TEST_JOB",
        handler,
    )
    submitted = await worker.submit(
        AutomationJobSubmission(
            job_type="TEST_JOB",
            payload={
                "value": 7,
            },
        )
    )
    completed = await worker.run_once()
    assert submitted.created is True
    assert completed is not None
    assert completed.id == "job-1"
    assert completed.status == "SUCCEEDED"
    assert completed.created_at_ms == 100
    assert completed.started_at_ms == 200
    assert completed.completed_at_ms == 300
    assert completed.result == {
        "received": 7,
    }
    assert completed.error_message is None
@pytest.mark.asyncio
async def test_handler_failure_is_recorded():
    worker = AutomationWorker(
        id_factory=lambda: "job-failed",
    )
    async def failing_handler(payload):
        raise RuntimeError("temporary failure")
    worker.register_handler(
        "FAIL_JOB",
        failing_handler,
    )
    await worker.submit(
        AutomationJobSubmission(
            job_type="FAIL_JOB",
        )
    )
    completed = await worker.run_once()
    assert completed is not None
    assert completed.status == "FAILED"
    assert completed.error_message == (
        "temporary failure"
    )
    assert completed.result is None
@pytest.mark.asyncio
async def test_active_duplicate_returns_existing_job():
    ids = iter(
        [
            "job-1",
            "job-2",
        ]
    )
    worker = AutomationWorker(
        id_factory=lambda: next(ids),
    )
    async def handler(payload):
        return payload
    worker.register_handler(
        "PORTFOLIO_SYNC",
        handler,
    )
    submission = AutomationJobSubmission(
        job_type="PORTFOLIO_SYNC",
        deduplication_key="portfolio-1",
    )
    first = await worker.submit(
        submission
    )
    duplicate = await worker.submit(
        submission
    )
    assert first.created is True
    assert duplicate.created is False
    assert duplicate.job.id == first.job.id
    assert worker.snapshot().queue_size == 1
    assert worker.snapshot().total_jobs == 1
@pytest.mark.asyncio
async def test_deduplication_key_is_released():
    ids = iter(
        [
            "job-1",
            "job-2",
        ]
    )
    worker = AutomationWorker(
        id_factory=lambda: next(ids),
    )
    async def handler(payload):
        return {
            "ok": True,
        }
    worker.register_handler(
        "PORTFOLIO_SYNC",
        handler,
    )
    submission = AutomationJobSubmission(
        job_type="PORTFOLIO_SYNC",
        deduplication_key="portfolio-1",
    )
    first = await worker.submit(
        submission
    )
    await worker.run_once()
    second = await worker.submit(
        submission
    )
    assert first.job.id == "job-1"
    assert second.created is True
    assert second.job.id == "job-2"
@pytest.mark.asyncio
async def test_background_worker_drains_and_stops():
    ids = iter(
        [
            "job-1",
            "job-2",
        ]
    )
    worker = AutomationWorker(
        id_factory=lambda: next(ids),
    )
    async def handler(payload):
        await asyncio.sleep(0)
        return payload["value"] * 2
    worker.register_handler(
        "DOUBLE",
        handler,
    )
    await worker.submit(
        AutomationJobSubmission(
            job_type="DOUBLE",
            payload={
                "value": 2,
            },
        )
    )
    await worker.submit(
        AutomationJobSubmission(
            job_type="DOUBLE",
            payload={
                "value": 3,
            },
        )
    )
    assert await worker.start() is True
    assert await worker.start() is False
    await worker.wait_until_idle()
    assert await worker.stop() is True
    snapshot = worker.snapshot()
    assert snapshot.running is False
    assert snapshot.accepting_jobs is False
    assert snapshot.succeeded_count == 2
    assert snapshot.failed_count == 0
    assert snapshot.queue_size == 0
    jobs = worker.list_jobs()
    assert [
        job.result
        for job in jobs
    ] == [
        4,
        6,
    ]
@pytest.mark.asyncio
async def test_snapshot_tracks_failed_and_queued_jobs():
    ids = iter(
        [
            "job-1",
            "job-2",
        ]
    )
    worker = AutomationWorker(
        id_factory=lambda: next(ids),
    )
    async def handler(payload):
        if payload.get("fail"):
            raise ValueError("failed")
        return "ok"
    worker.register_handler(
        "SNAPSHOT_JOB",
        handler,
    )
    await worker.submit(
        AutomationJobSubmission(
            job_type="SNAPSHOT_JOB",
            payload={
                "fail": True,
            },
        )
    )
    await worker.submit(
        AutomationJobSubmission(
            job_type="SNAPSHOT_JOB",
        )
    )
    await worker.run_once()
    snapshot = worker.snapshot()
    assert snapshot.total_jobs == 2
    assert snapshot.failed_count == 1
    assert snapshot.queued_count == 1
    assert snapshot.running_count == 0
    assert snapshot.registered_job_types == [
        "SNAPSHOT_JOB"
    ]
