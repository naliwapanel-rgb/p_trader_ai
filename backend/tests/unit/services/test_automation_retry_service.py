from collections.abc import Iterator
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas.automation import (
    AutomationJobSubmission,
    AutomationRetryPolicy,
)
from app.services.automation_retry_service import (
    AutomationRetryService,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
def build_clock(
    values: list[int],
) -> callable:
    iterator: Iterator[int] = iter(values)
    return lambda: next(iterator)
def test_policy_normalizes_retry_values():
    policy = AutomationRetryPolicy(
        retryable_error_names=[
            " TimeoutError ",
            "TimeoutError",
            "ConnectionError",
        ],
        retryable_http_status_codes=[
            503,
            503,
            429,
        ],
    )
    assert policy.retryable_error_names == [
        "TimeoutError",
        "ConnectionError",
    ]
    assert (
        policy.retryable_http_status_codes
        == [
            503,
            429,
        ]
    )
def test_policy_rejects_invalid_delay_range():
    with pytest.raises(
        ValidationError
    ) as exc_info:
        AutomationRetryPolicy(
            initial_delay_seconds=10,
            maximum_delay_seconds=5,
        )
    assert (
        "maximum_delay_seconds"
        in str(exc_info.value)
    )
def test_fixed_backoff_delay():
    policy = AutomationRetryPolicy(
        max_attempts=5,
        initial_delay_seconds=1.5,
        maximum_delay_seconds=10,
        backoff_strategy="FIXED",
    )
    delay = (
        AutomationRetryService
        .calculate_delay(
            policy=policy,
            attempt_number=3,
        )
    )
    assert delay == 1.5
def test_exponential_backoff_is_capped():
    policy = AutomationRetryPolicy(
        max_attempts=5,
        initial_delay_seconds=2,
        maximum_delay_seconds=10,
        backoff_strategy=(
            "EXPONENTIAL"
        ),
        backoff_multiplier=3,
    )
    delay = (
        AutomationRetryService
        .calculate_delay(
            policy=policy,
            attempt_number=3,
        )
    )
    assert delay == 10
def test_timeout_error_is_retryable():
    policy = AutomationRetryPolicy(
        max_attempts=3,
        initial_delay_seconds=1,
    )
    decision = (
        AutomationRetryService.decide(
            error=TimeoutError(
                "request timed out"
            ),
            attempt_number=1,
            policy=policy,
        )
    )
    assert decision.retry is True
    assert decision.delay_seconds == 1
    assert decision.reason == (
        "Error is retryable and "
        "attempts remain"
    )
def test_retryable_http_status_is_classified():
    policy = AutomationRetryPolicy(
        max_attempts=3,
    )
    decision = (
        AutomationRetryService.decide(
            error=HTTPException(
                status_code=503,
                detail=(
                    "Exchange unavailable"
                ),
            ),
            attempt_number=1,
            policy=policy,
        )
    )
    assert decision.retry is True
def test_non_retryable_error_is_rejected():
    policy = AutomationRetryPolicy(
        max_attempts=3,
    )
    decision = (
        AutomationRetryService.decide(
            error=ValueError(
                "invalid payload"
            ),
            attempt_number=1,
            policy=policy,
        )
    )
    assert decision.retry is False
    assert decision.reason == (
        "Error is not retryable under "
        "the configured policy"
    )
@pytest.mark.asyncio
async def test_worker_retries_until_success():
    attempts = 0
    sleep_delays: list[float] = []
    async def sleep_func(
        delay: float,
    ) -> None:
        sleep_delays.append(delay)
    async def handler(payload):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError(
                "temporary timeout"
            )
        return {
            "attempts": attempts,
        }
    worker = AutomationWorker(
        clock_ms=build_clock(
            [
                100,
                200,
                300,
            ]
        ),
        id_factory=lambda: "job-retry",
        sleep_func=sleep_func,
    )
    worker.register_handler(
        "RETRY_JOB",
        handler,
        retry_policy=(
            AutomationRetryPolicy(
                max_attempts=3,
                initial_delay_seconds=1,
                backoff_multiplier=2,
                maximum_delay_seconds=10,
            )
        ),
    )
    submitted = await worker.submit(
        AutomationJobSubmission(
            job_type="RETRY_JOB",
        )
    )
    completed = await worker.run_once()
    assert submitted.job.max_attempts == 3
    assert completed is not None
    assert completed.status == "SUCCEEDED"
    assert completed.attempt_count == 3
    assert completed.retry_count == 2
    assert completed.retry_delays_seconds == [
        1,
        2,
    ]
    assert sleep_delays == [
        1,
        2,
    ]
    assert completed.result == {
        "attempts": 3,
    }
    snapshot = worker.snapshot()
    assert snapshot.total_attempts == 3
    assert snapshot.retried_job_count == 1
@pytest.mark.asyncio
async def test_worker_stops_after_max_attempts():
    attempts = 0
    async def sleep_func(
        delay: float,
    ) -> None:
        return None
    async def handler(payload):
        nonlocal attempts
        attempts += 1
        raise ConnectionError(
            "exchange unavailable"
        )
    worker = AutomationWorker(
        id_factory=lambda: "job-failed",
        sleep_func=sleep_func,
    )
    worker.register_handler(
        "FAIL_JOB",
        handler,
        retry_policy=(
            AutomationRetryPolicy(
                max_attempts=3,
                initial_delay_seconds=0,
            )
        ),
    )
    await worker.submit(
        AutomationJobSubmission(
            job_type="FAIL_JOB",
        )
    )
    completed = await worker.run_once()
    assert completed is not None
    assert completed.status == "FAILED"
    assert completed.attempt_count == 3
    assert completed.retry_count == 2
    assert completed.retry_delays_seconds == [
        0,
        0,
    ]
    assert completed.error_message == (
        "exchange unavailable"
    )
@pytest.mark.asyncio
async def test_unknown_error_can_be_retried():
    attempts = 0
    async def sleep_func(
        delay: float,
    ) -> None:
        return None
    async def handler(payload):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ValueError(
                "temporary custom error"
            )
        return "recovered"
    worker = AutomationWorker(
        id_factory=lambda: "job-unknown",
        sleep_func=sleep_func,
    )
    worker.register_handler(
        "UNKNOWN_JOB",
        handler,
        retry_policy=(
            AutomationRetryPolicy(
                max_attempts=2,
                retry_on_unknown_errors=True,
            )
        ),
    )
    await worker.submit(
        AutomationJobSubmission(
            job_type="UNKNOWN_JOB",
        )
    )
    completed = await worker.run_once()
    assert completed is not None
    assert completed.status == "SUCCEEDED"
    assert completed.attempt_count == 2
    assert completed.retry_count == 1
    assert completed.result == "recovered"
