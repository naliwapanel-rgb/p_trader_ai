import asyncio
import inspect
import time
from collections.abc import (
    Awaitable,
    Callable,
)
from typing import Any
from uuid import uuid4
from app.schemas.automation import (
    AutomationJob,
    AutomationJobSubmission,
    AutomationJobSubmissionResult,
    AutomationWorkerSnapshot,
)
AutomationJobHandler = Callable[
    [dict[str, Any]],
    Awaitable[Any],
]
class AutomationWorker:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int] | None = None,
        id_factory: Callable[[], str] | None = None,
    ):
        self.clock_ms = (
            clock_ms
            or (
                lambda:
                int(time.time() * 1000)
            )
        )
        self.id_factory = (
            id_factory
            or (
                lambda:
                uuid4().hex
            )
        )
        self._queue: asyncio.Queue[
            str | None
        ] = asyncio.Queue()
        self._handlers: dict[
            str,
            AutomationJobHandler,
        ] = {}
        self._jobs: dict[
            str,
            AutomationJob,
        ] = {}
        self._active_deduplication_keys: dict[
            str,
            str,
        ] = {}
        self._runner_task: (
            asyncio.Task[None] | None
        ) = None
        self._accepting_jobs = True
    @staticmethod
    def _normalize_job_type(
        job_type: str,
    ) -> str:
        normalized = job_type.strip().upper()
        if not normalized:
            raise ValueError(
                "job_type cannot be blank"
            )
        return normalized
    @staticmethod
    def _copy_job(
        job: AutomationJob,
    ) -> AutomationJob:
        return job.model_copy(deep=True)
    @property
    def is_running(self) -> bool:
        return (
            self._runner_task is not None
            and not self._runner_task.done()
        )
    def register_handler(
        self,
        job_type: str,
        handler: AutomationJobHandler,
    ) -> None:
        normalized_job_type = (
            self._normalize_job_type(
                job_type
            )
        )
        if not callable(handler):
            raise TypeError(
                "handler must be callable"
            )
        if normalized_job_type in self._handlers:
            raise ValueError(
                "A handler is already registered "
                f"for {normalized_job_type}"
            )
        self._handlers[
            normalized_job_type
        ] = handler
    async def submit(
        self,
        data: AutomationJobSubmission,
    ) -> AutomationJobSubmissionResult:
        if not self._accepting_jobs:
            raise RuntimeError(
                "Automation worker is not "
                "accepting jobs"
            )
        if data.job_type not in self._handlers:
            raise ValueError(
                "No handler is registered for "
                f"{data.job_type}"
            )
        deduplication_key = (
            data.deduplication_key
        )
        if deduplication_key is not None:
            active_job_id = (
                self
                ._active_deduplication_keys
                .get(deduplication_key)
            )
            if active_job_id is not None:
                active_job = self._jobs.get(
                    active_job_id
                )
                if (
                    active_job is not None
                    and active_job.status
                    in {
                        "QUEUED",
                        "RUNNING",
                    }
                ):
                    return (
                        AutomationJobSubmissionResult(
                            job=self._copy_job(
                                active_job
                            ),
                            created=False,
                        )
                    )
                self._active_deduplication_keys.pop(
                    deduplication_key,
                    None,
                )
        job_id = self.id_factory()
        if not job_id or job_id in self._jobs:
            raise ValueError(
                "id_factory returned an invalid "
                "or duplicate job ID"
            )
        job = AutomationJob(
            id=job_id,
            job_type=data.job_type,
            payload=dict(data.payload),
            deduplication_key=(
                deduplication_key
            ),
            status="QUEUED",
            created_at_ms=self.clock_ms(),
        )
        self._jobs[job.id] = job
        if deduplication_key is not None:
            self._active_deduplication_keys[
                deduplication_key
            ] = job.id
        await self._queue.put(job.id)
        return AutomationJobSubmissionResult(
            job=self._copy_job(job),
            created=True,
        )
    def get_job(
        self,
        job_id: str,
    ) -> AutomationJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        return self._copy_job(job)
    def list_jobs(
        self,
    ) -> list[AutomationJob]:
        return [
            self._copy_job(job)
            for job in self._jobs.values()
        ]
    def snapshot(
        self,
    ) -> AutomationWorkerSnapshot:
        counts = {
            "QUEUED": 0,
            "RUNNING": 0,
            "SUCCEEDED": 0,
            "FAILED": 0,
            "CANCELLED": 0,
        }
        for job in self._jobs.values():
            counts[job.status] += 1
        return AutomationWorkerSnapshot(
            running=self.is_running,
            accepting_jobs=(
                self._accepting_jobs
            ),
            queue_size=self._queue.qsize(),
            total_jobs=len(self._jobs),
            queued_count=counts["QUEUED"],
            running_count=counts["RUNNING"],
            succeeded_count=counts[
                "SUCCEEDED"
            ],
            failed_count=counts["FAILED"],
            cancelled_count=counts[
                "CANCELLED"
            ],
            registered_job_types=sorted(
                self._handlers
            ),
        )
    async def _execute_job(
        self,
        job: AutomationJob,
    ) -> None:
        handler = self._handlers.get(
            job.job_type
        )
        job.status = "RUNNING"
        job.started_at_ms = self.clock_ms()
        job.error_message = None
        try:
            if handler is None:
                raise RuntimeError(
                    "Registered handler is missing"
                )
            pending_result = handler(
                dict(job.payload)
            )
            if not inspect.isawaitable(
                pending_result
            ):
                raise TypeError(
                    "Automation job handler must "
                    "return an awaitable"
                )
            job.result = await pending_result
            job.status = "SUCCEEDED"
        except asyncio.CancelledError:
            job.status = "CANCELLED"
            job.error_message = (
                "Automation job was cancelled"
            )
            raise
        except Exception as exc:
            job.status = "FAILED"
            message = str(exc).strip()
            job.error_message = (
                message
                or exc.__class__.__name__
            )
        finally:
            job.completed_at_ms = (
                self.clock_ms()
            )
            if job.deduplication_key:
                current_job_id = (
                    self
                    ._active_deduplication_keys
                    .get(
                        job.deduplication_key
                    )
                )
                if current_job_id == job.id:
                    (
                        self
                        ._active_deduplication_keys
                        .pop(
                            job.deduplication_key,
                            None,
                        )
                    )
    async def run_once(
        self,
    ) -> AutomationJob | None:
        job_id = await self._queue.get()
        try:
            if job_id is None:
                return None
            job = self._jobs.get(job_id)
            if job is None:
                return None
            await self._execute_job(job)
            return self._copy_job(job)
        finally:
            self._queue.task_done()
    async def _run_forever(
        self,
    ) -> None:
        while True:
            result = await self.run_once()
            if result is None:
                return
    async def start(self) -> bool:
        if self.is_running:
            return False
        self._accepting_jobs = True
        self._runner_task = asyncio.create_task(
            self._run_forever(),
            name="automation-worker",
        )
        return True
    async def wait_until_idle(self) -> None:
        await self._queue.join()
    async def stop(
        self,
        *,
        drain: bool = True,
    ) -> bool:
        if not self.is_running:
            self._accepting_jobs = False
            return False
        self._accepting_jobs = False
        if drain:
            await self.wait_until_idle()
            await self._queue.put(None)
            await self._runner_task
        else:
            self._runner_task.cancel()
            try:
                await self._runner_task
            except asyncio.CancelledError:
                pass
        self._runner_task = None
        return True
