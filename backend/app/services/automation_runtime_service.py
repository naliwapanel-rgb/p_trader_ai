from app.schemas.automation import (
    AutomationRuntimeHealth,
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
class AutomationRuntime:
    """
    Shared in-memory automation runtime.
    The runtime owns one worker and one interval scheduler.
    Automated trade handlers are registered once during
    runtime construction.
    Starting the runtime starts only the worker. Registered
    schedules must still be started explicitly.
    """
    def __init__(
        self,
        *,
        worker: AutomationWorker | None = None,
        scheduler: (
            AutomationIntervalScheduler | None
        ) = None,
        trade_execution_service: (
            AutomatedTradeExecutionService
            | None
        ) = None,
    ):
        self.worker = (
            worker
            or AutomationWorker()
        )
        if (
            scheduler is not None
            and scheduler.worker
            is not self.worker
        ):
            raise ValueError(
                "Automation scheduler must use "
                "the runtime worker"
            )
        self.scheduler = (
            scheduler
            or AutomationIntervalScheduler(
                worker=self.worker
            )
        )
        self.trade_execution_service = (
            trade_execution_service
            or AutomatedTradeExecutionService()
        )
        self._handlers_registered = False
        self._started = False
        self.register_handlers_once()
    @property
    def started(self) -> bool:
        return self._started
    @property
    def handlers_registered(self) -> bool:
        return self._handlers_registered
    def register_handlers_once(
        self,
    ) -> bool:
        """
        Register the automated market-order and
        limit-order handlers exactly once.
        """
        if self._handlers_registered:
            return False
        self.trade_execution_service.register_handlers(
            self.worker
        )
        self._handlers_registered = True
        return True
    async def start(self) -> bool:
        """
        Start the shared worker.
        Schedules are intentionally not started
        automatically.
        """
        if (
            self._started
            and self.worker.is_running
        ):
            return False
        worker_started = (
            await self.worker.start()
        )
        self._started = True
        return worker_started
    async def stop(
        self,
        *,
        drain: bool = True,
    ) -> bool:
        """
        Stop schedules first and then stop the worker.
        With drain enabled, already queued work is allowed
        to finish before the worker exits.
        """
        scheduler_snapshot = (
            self.scheduler.snapshot()
        )
        was_active = (
            self._started
            or self.worker.is_running
            or (
                scheduler_snapshot
                .running_schedule_count
                > 0
            )
        )
        if not was_active:
            self._started = False
            return False
        await self.scheduler.stop_all()
        await self.worker.stop(
            drain=drain
        )
        self._started = False
        return True
    def health(
        self,
    ) -> AutomationRuntimeHealth:
        worker_snapshot = (
            self.worker.snapshot()
        )
        scheduler_snapshot = (
            self.scheduler.snapshot()
        )
        healthy = (
            self._started
            and self._handlers_registered
            and worker_snapshot.running
            and worker_snapshot.accepting_jobs
        )
        return AutomationRuntimeHealth(
            healthy=healthy,
            started=self._started,
            handlers_registered=(
                self._handlers_registered
            ),
            worker=worker_snapshot,
            scheduler=scheduler_snapshot,
        )
