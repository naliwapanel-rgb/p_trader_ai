import asyncio
import time
from collections.abc import (
    Awaitable,
    Callable,
)
from app.schemas.automation import (
    AutomationIntervalSchedule,
    AutomationJobSubmission,
    AutomationScheduleState,
    AutomationSchedulerSnapshot,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
AutomationSchedulerSleepFunction = Callable[
    [float],
    Awaitable[None],
]
class AutomationIntervalScheduler:
    def __init__(
        self,
        *,
        worker: AutomationWorker,
        clock_ms: Callable[[], int] | None = None,
        sleep_func: (
            AutomationSchedulerSleepFunction
            | None
        ) = None,
    ):
        self.worker = worker
        self.clock_ms = (
            clock_ms
            or (
                lambda:
                int(time.time() * 1000)
            )
        )
        self.sleep_func = (
            sleep_func
            or asyncio.sleep
        )
        self._definitions: dict[
            str,
            AutomationIntervalSchedule,
        ] = {}
        self._states: dict[
            str,
            AutomationScheduleState,
        ] = {}
        self._tasks: dict[
            str,
            asyncio.Task[None],
        ] = {}
    @staticmethod
    def _copy_state(
        state: AutomationScheduleState,
    ) -> AutomationScheduleState:
        return state.model_copy(deep=True)
    def register_schedule(
        self,
        data: AutomationIntervalSchedule,
    ) -> AutomationScheduleState:
        if data.schedule_id in self._definitions:
            raise ValueError(
                "A schedule is already registered "
                f"with ID {data.schedule_id}"
            )
        registered_job_types = set(
            self.worker
            .snapshot()
            .registered_job_types
        )
        if data.job_type not in registered_job_types:
            raise ValueError(
                "No worker handler is registered "
                f"for {data.job_type}"
            )
        definition = data.model_copy(
            deep=True
        )
        state = AutomationScheduleState(
            schedule_id=definition.schedule_id,
            job_type=definition.job_type,
            enabled=definition.enabled,
            running=False,
            interval_seconds=(
                definition.interval_seconds
            ),
            max_runs=definition.max_runs,
        )
        self._definitions[
            definition.schedule_id
        ] = definition
        self._states[
            definition.schedule_id
        ] = state
        return self._copy_state(state)
    def get_schedule(
        self,
        schedule_id: str,
    ) -> AutomationIntervalSchedule | None:
        definition = self._definitions.get(
            schedule_id
        )
        if definition is None:
            return None
        return definition.model_copy(
            deep=True
        )
    def get_state(
        self,
        schedule_id: str,
    ) -> AutomationScheduleState | None:
        state = self._states.get(
            schedule_id
        )
        if state is None:
            return None
        return self._copy_state(state)
    def list_states(
        self,
    ) -> list[AutomationScheduleState]:
        return [
            self._copy_state(
                self._states[schedule_id]
            )
            for schedule_id in sorted(
                self._states
            )
        ]
    @staticmethod
    def _effective_deduplication_key(
        definition: AutomationIntervalSchedule,
    ) -> str:
        return (
            definition.deduplication_key
            or (
                "automation-schedule:"
                f"{definition.schedule_id}"
            )
        )
    async def run_once(
        self,
        schedule_id: str,
    ):
        definition = self._definitions.get(
            schedule_id
        )
        state = self._states.get(
            schedule_id
        )
        if definition is None or state is None:
            raise KeyError(
                f"Schedule {schedule_id} "
                "is not registered"
            )
        if not state.enabled:
            raise RuntimeError(
                f"Schedule {schedule_id} "
                "is disabled"
            )
        state.submission_count += 1
        state.last_submitted_at_ms = (
            self.clock_ms()
        )
        try:
            result = await self.worker.submit(
                AutomationJobSubmission(
                    job_type=(
                        definition.job_type
                    ),
                    payload=dict(
                        definition.payload
                    ),
                    deduplication_key=(
                        self
                        ._effective_deduplication_key(
                            definition
                        )
                    ),
                )
            )
            state.last_job_id = (
                result.job.id
            )
            state.last_error = None
            if result.created:
                state.created_job_count += 1
            else:
                (
                    state
                    .duplicate_submission_count
                ) += 1
            state.next_run_at_ms = (
                state.last_submitted_at_ms
                + int(
                    definition.interval_seconds
                    * 1000
                )
            )
            return result
        except Exception as exc:
            state.failure_count += 1
            message = str(exc).strip()
            state.last_error = (
                message
                or exc.__class__.__name__
            )
            state.next_run_at_ms = (
                state.last_submitted_at_ms
                + int(
                    definition.interval_seconds
                    * 1000
                )
            )
            raise
    async def _run_schedule(
        self,
        schedule_id: str,
    ) -> None:
        definition = self._definitions[
            schedule_id
        ]
        state = self._states[
            schedule_id
        ]
        try:
            if (
                definition.initial_delay_seconds
                > 0
            ):
                state.next_run_at_ms = (
                    self.clock_ms()
                    + int(
                        definition
                        .initial_delay_seconds
                        * 1000
                    )
                )
                await self.sleep_func(
                    definition
                    .initial_delay_seconds
                )
            while state.enabled:
                if (
                    definition.max_runs
                    is not None
                    and state.submission_count
                    >= definition.max_runs
                ):
                    break
                try:
                    await self.run_once(
                        schedule_id
                    )
                except Exception:
                    pass
                if (
                    definition.max_runs
                    is not None
                    and state.submission_count
                    >= definition.max_runs
                ):
                    break
                state.next_run_at_ms = (
                    self.clock_ms()
                    + int(
                        definition.interval_seconds
                        * 1000
                    )
                )
                await self.sleep_func(
                    definition.interval_seconds
                )
        except asyncio.CancelledError:
            raise
        finally:
            state.running = False
            state.stopped_at_ms = (
                self.clock_ms()
            )
            state.next_run_at_ms = 0
    async def start_schedule(
        self,
        schedule_id: str,
    ) -> bool:
        definition = self._definitions.get(
            schedule_id
        )
        state = self._states.get(
            schedule_id
        )
        if definition is None or state is None:
            raise KeyError(
                f"Schedule {schedule_id} "
                "is not registered"
            )
        if not state.enabled:
            return False
        existing_task = self._tasks.get(
            schedule_id
        )
        if (
            existing_task is not None
            and not existing_task.done()
        ):
            return False
        state.running = True
        state.started_at_ms = (
            self.clock_ms()
        )
        state.stopped_at_ms = 0
        task = asyncio.create_task(
            self._run_schedule(
                schedule_id
            ),
            name=(
                "automation-schedule-"
                f"{schedule_id}"
            ),
        )
        self._tasks[schedule_id] = task
        return True
    async def start_all(self) -> int:
        started_count = 0
        for schedule_id in sorted(
            self._definitions
        ):
            if await self.start_schedule(
                schedule_id
            ):
                started_count += 1
        return started_count
    async def stop_schedule(
        self,
        schedule_id: str,
    ) -> bool:
        if schedule_id not in self._definitions:
            raise KeyError(
                f"Schedule {schedule_id} "
                "is not registered"
            )
        state = self._states[
            schedule_id
        ]
        task = self._tasks.get(
            schedule_id
        )
        if task is None or task.done():
            if state.running:
                state.running = False
                state.stopped_at_ms = (
                    self.clock_ms()
                )
                state.next_run_at_ms = 0
            return False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            # A task may be cancelled before
            # _run_schedule() begins executing.
            # Normalize state here as well as in
            # _run_schedule() to close that race.
            state.running = False
            state.stopped_at_ms = (
                self.clock_ms()
            )
            state.next_run_at_ms = 0
            self._tasks.pop(
                schedule_id,
                None,
            )
        return True

    async def stop_all(self) -> int:
        stopped_count = 0
        for schedule_id in sorted(
            self._definitions
        ):
            if await self.stop_schedule(
                schedule_id
            ):
                stopped_count += 1
        return stopped_count
    async def wait_until_stopped(
        self,
    ) -> None:
        tasks = list(
            self._tasks.values()
        )
        if not tasks:
            return
        await asyncio.gather(
            *tasks
        )
    def snapshot(
        self,
    ) -> AutomationSchedulerSnapshot:
        states = self.list_states()
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
                (
                    state
                    .duplicate_submission_count
                )
                for state in states
            ),
            total_failures=sum(
                state.failure_count
                for state in states
            ),
            schedules=states,
        )
