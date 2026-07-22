from collections.abc import (
    Callable,
)
from datetime import (
    UTC,
    datetime,
)
from typing import (
    Any,
)
from sqlalchemy.orm import (
    Session,
)
from app.database.session import (
    SessionLocal,
)
from app.repositories.exchange_account_repository import (
    ExchangeAccountRepository,
)
from app.repositories.trading_bot_repository import (
    TradingBotRepository,
)
from app.schemas.automation import (
    AutomationIntervalSchedule,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_runtime import (
    TradingBotRuntimeRestoreResult,
    TradingBotRuntimeScheduleResult,
    TradingBotTickJob,
    TradingBotTickResult,
)
from app.services.automation_scheduler_service import (
    AutomationIntervalScheduler,
)
from app.services.market_scanner_service import (
    MarketScannerService,
)
from app.services.paper_trading_engine import (
    PaperTradingEngine,
)
from app.services.trading_bot_runtime_market_history_service import (
    TradingBotRuntimeMarketHistoryService,
)
from app.services.trading_bot_strategy_runner import (
    TradingBotStrategyRunner,
)
from app.services.trading_bot_strategy_state_service import (
    TradingBotStrategyStateService,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
SessionFactory = Callable[[], Session]
RepositoryFactory = Callable[
    [Session],
    TradingBotRepository,
]
AccountRepositoryFactory = Callable[
    [Session],
    ExchangeAccountRepository,
]
PaperEngineFactory = Callable[
    [Session],
    PaperTradingEngine,
]
StrategyStateServiceFactory = Callable[
    [Session],
    TradingBotStrategyStateService,
]
RuntimeClock = Callable[[], datetime]
class TradingBotRuntimeService:
    JOB_TYPE = "TRADING_BOT_TICK"
    INTERVAL_SECONDS = 60.0
    STATEFUL_STRATEGIES = frozenset({
        "DCA",
        "GRID",
        "TREND",
        "MEAN_REVERSION",
        "SCALPING",
    })
    HISTORY_STRATEGIES = frozenset({
        "TREND",
        "MEAN_REVERSION",
        "SCALPING",
    })
    def __init__(
        self,
        *,
        scheduler: (
            AutomationIntervalScheduler
        ),
        session_factory: (
            SessionFactory | None
        ) = None,
        repository_factory: (
            RepositoryFactory | None
        ) = None,
        account_repository_factory: (
            AccountRepositoryFactory
            | None
        ) = None,
        market_scanner_service: (
            MarketScannerService | None
        ) = None,
        strategy_runner: (
            TradingBotStrategyRunner | None
        ) = None,
        paper_engine_factory: (
            PaperEngineFactory | None
        ) = None,
        strategy_state_service_factory: (
            StrategyStateServiceFactory
            | None
        ) = None,
        market_history_service: (
            TradingBotRuntimeMarketHistoryService
            | None
        ) = None,
        clock: RuntimeClock | None = None,
    ):
        self.scheduler = scheduler
        self.session_factory = (
            session_factory
            or SessionLocal
        )
        self.repository_factory = (
            repository_factory
            or TradingBotRepository
        )
        self.account_repository_factory = (
            account_repository_factory
            or ExchangeAccountRepository
        )
        self.market_scanner_service = (
            market_scanner_service
            or MarketScannerService()
        )
        self.clock = (
            clock
            or (
                lambda: datetime.now(UTC)
            )
        )
        self.paper_engine_factory = (
            paper_engine_factory
            or (
                lambda db:
                PaperTradingEngine(
                    db,
                    clock=self.clock,
                )
            )
        )
        self.strategy_state_service_factory = (
            strategy_state_service_factory
            or TradingBotStrategyStateService
        )
        self.market_history_service = (
            market_history_service
            or TradingBotRuntimeMarketHistoryService()
        )
        self.strategy_runner = (
            strategy_runner
            or TradingBotStrategyRunner(
                clock=self.clock
            )
        )
    @staticmethod
    def schedule_id(
        *,
        user_id: int,
        bot_id: int,
    ) -> str:
        return (
            f"trading-bot:{user_id}:{bot_id}"
        )
    @staticmethod
    def deduplication_key(
        *,
        user_id: int,
        bot_id: int,
    ) -> str:
        return (
            "trading-bot-tick:"
            f"{user_id}:{bot_id}"
        )
    @staticmethod
    def _error_text(
        error: BaseException,
    ) -> str:
        message = str(error).strip()
        return (
            message
            or error.__class__.__name__
        )[:4000]
    @staticmethod
    def _rollback_safely(
        db: Session,
    ) -> None:
        rollback = getattr(
            db,
            "rollback",
            None,
        )
        if callable(rollback):
            try:
                rollback()
            except Exception:
                pass
    @staticmethod
    def _close_safely(
        db: Session,
    ) -> None:
        close = getattr(
            db,
            "close",
            None,
        )
        if callable(close):
            try:
                close()
            except Exception:
                pass
    def register_handler(
        self,
        worker: AutomationWorker,
    ) -> None:
        registered = set(
            worker.snapshot()
            .registered_job_types
        )
        if self.JOB_TYPE in registered:
            raise ValueError(
                "Trading bot runtime handler "
                "is already registered"
            )
        worker.register_handler(
            self.JOB_TYPE,
            self.execute_tick,
        )
    def _schedule_definition(
        self,
        bot,
    ) -> AutomationIntervalSchedule:
        return AutomationIntervalSchedule(
            schedule_id=(
                self.schedule_id(
                    user_id=bot.user_id,
                    bot_id=bot.id,
                )
            ),
            job_type=self.JOB_TYPE,
            interval_seconds=(
                self.INTERVAL_SECONDS
            ),
            initial_delay_seconds=(
                self.INTERVAL_SECONDS
            ),
            payload={
                "user_id": bot.user_id,
                "bot_id": bot.id,
            },
            deduplication_key=(
                self.deduplication_key(
                    user_id=bot.user_id,
                    bot_id=bot.id,
                )
            ),
            enabled=True,
        )
    @staticmethod
    def _validate_existing_schedule(
        *,
        existing: AutomationIntervalSchedule,
        expected: AutomationIntervalSchedule,
    ) -> None:
        if (
            existing.job_type
            != expected.job_type
            or existing.payload
            != expected.payload
            or existing.interval_seconds
            != expected.interval_seconds
        ):
            raise RuntimeError(
                "Existing trading bot runtime "
                "schedule conflicts with the "
                "expected definition"
            )
    async def start_for_bot(
        self,
        bot,
    ) -> TradingBotRuntimeScheduleResult:
        self.strategy_runner.validate_bot(
            bot
        )
        definition = (
            self._schedule_definition(bot)
        )
        existing = (
            self.scheduler.get_schedule(
                definition.schedule_id
            )
        )
        registered = False
        if existing is None:
            self.scheduler.register_schedule(
                definition
            )
            registered = True
        else:
            self._validate_existing_schedule(
                existing=existing,
                expected=definition,
            )
        changed = (
            await self.scheduler
            .start_schedule(
                definition.schedule_id
            )
        )
        state = self.scheduler.get_state(
            definition.schedule_id
        )
        if state is None:
            raise RuntimeError(
                "Trading bot runtime schedule "
                "state is unavailable"
            )
        return (
            TradingBotRuntimeScheduleResult(
                schedule_id=(
                    definition.schedule_id
                ),
                registered=registered,
                changed=changed,
                running=state.running,
            )
        )
    async def stop_for_bot(
        self,
        bot,
    ) -> TradingBotRuntimeScheduleResult:
        schedule_id = self.schedule_id(
            user_id=bot.user_id,
            bot_id=bot.id,
        )
        definition = (
            self.scheduler.get_schedule(
                schedule_id
            )
        )
        if definition is None:
            return (
                TradingBotRuntimeScheduleResult(
                    schedule_id=schedule_id,
                    registered=False,
                    changed=False,
                    running=False,
                )
            )
        changed = (
            await self.scheduler
            .stop_schedule(schedule_id)
        )
        state = self.scheduler.get_state(
            schedule_id
        )
        return (
            TradingBotRuntimeScheduleResult(
                schedule_id=schedule_id,
                registered=True,
                changed=changed,
                running=(
                    state.running
                    if state is not None
                    else False
                ),
            )
        )
    async def _load_ticker(
        self,
        *,
        bot,
        account_repository: (
            ExchangeAccountRepository
        ),
    ) -> MarketTickerSnapshot:
        if bot.exchange_account_id is None:
            raise ValueError(
                "Trading bot requires an "
                "exchange account"
            )
        account = (
            account_repository
            .get_by_id_and_user(
                account_id=(
                    bot.exchange_account_id
                ),
                user_id=bot.user_id,
            )
        )
        if account is None:
            raise ValueError(
                "Trading bot exchange account "
                "was not found"
            )
        if not account.is_active:
            raise ValueError(
                "Trading bot exchange account "
                "is inactive"
            )
        exchange_name = (
            account.exchange_name
            .strip()
            .upper()
        )
        if exchange_name != "BYBIT":
            raise ValueError(
                "Phase 12E strategy market "
                "context currently supports "
                "BYBIT only"
            )
        batch = await (
            self.market_scanner_service
            .get_tickers(
                category=bot.category,
                is_testnet=(
                    account.is_testnet
                ),
            )
        )
        symbol = bot.symbol.strip().upper()
        for ticker in batch.tickers:
            if ticker.symbol == symbol:
                return ticker
        raise ValueError(
            "Trading bot market ticker "
            f"was not found for {symbol}"
        )
    async def execute_tick(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = TradingBotTickJob.model_validate(
            payload
        )
        db = self.session_factory()
        repository = (
            self.repository_factory(db)
        )
        account_repository = (
            self.account_repository_factory(
                db
            )
        )
        bot = None
        try:
            bot = (
                repository
                .get_by_id_and_user(
                    bot_id=data.bot_id,
                    user_id=data.user_id,
                )
            )
            if bot is None:
                raise ValueError(
                    "Trading bot runtime target "
                    "was not found"
                )
            if bot.status != "RUNNING":
                result = TradingBotTickResult(
                    user_id=data.user_id,
                    bot_id=data.bot_id,
                    outcome="SKIPPED",
                    bot_status=bot.status,
                    ran_at=None,
                    decision=None,
                    paper_execution=None,
                )
                return result.model_dump(
                    mode="json"
                )
            ticker = await self._load_ticker(
                bot=bot,
                account_repository=(
                    account_repository
                ),
            )
            strategy_arguments = {
                "bot": bot,
                "ticker": ticker,
            }
            strategy_type = (
                str(bot.strategy_type)
                .strip()
                .upper()
            )
            if (
                strategy_type
                in self.HISTORY_STRATEGIES
            ):
                market_history = []
                if ticker.last_price > 0:
                    market_history = (
                        self
                        .market_history_service
                        .append_ticker(
                            bot=bot,
                            ticker=ticker,
                            observed_at=(
                                self.clock()
                            ),
                        )
                    )
                strategy_arguments[
                    "market_history"
                ] = market_history
            if (
                strategy_type
                in self.STATEFUL_STRATEGIES
            ):
                state_service = (
                    self
                    .strategy_state_service_factory(
                        db
                    )
                )
                strategy_arguments["state"] = (
                    state_service
                    .build_from_paper_ledger(
                        bot=bot,
                        current_price=(
                            ticker.last_price
                        ),
                    )
                )
            decision = await (
                self.strategy_runner.run(
                    **strategy_arguments
                )
            )
            paper_execution = None
            if bot.paper_trading:
                paper_engine = (
                    self.paper_engine_factory(
                        db
                    )
                )
                paper_execution = (
                    paper_engine.execute(
                        bot=bot,
                        decision=decision,
                    )
                )
            now = decision.evaluated_at
            repository.save_lifecycle(
                bot=bot,
                status="RUNNING",
                updated_at=now,
                last_run_at=now,
                last_error=None,
            )
            result = TradingBotTickResult(
                user_id=data.user_id,
                bot_id=data.bot_id,
                outcome="EVALUATED",
                bot_status="RUNNING",
                ran_at=now,
                decision=decision,
                paper_execution=(
                    paper_execution
                ),
            )
            return result.model_dump(
                mode="json"
            )
        except Exception as error:
            self._rollback_safely(db)
            if bot is not None:
                try:
                    now = self.clock()
                    repository.save_lifecycle(
                        bot=bot,
                        status="ERROR",
                        updated_at=now,
                        last_error=(
                            self._error_text(error)
                        ),
                    )
                except Exception:
                    self._rollback_safely(db)
            raise
        finally:
            self._close_safely(db)
    def mark_runtime_error(
        self,
        *,
        user_id: int,
        bot_id: int,
        error: BaseException,
    ) -> bool:
        db = self.session_factory()
        repository = (
            self.repository_factory(db)
        )
        try:
            bot = (
                repository
                .get_by_id_and_user(
                    bot_id=bot_id,
                    user_id=user_id,
                )
            )
            if bot is None:
                return False
            now = self.clock()
            repository.save_lifecycle(
                bot=bot,
                status="ERROR",
                updated_at=now,
                last_error=(
                    self._error_text(error)
                ),
            )
            return True
        except Exception:
            self._rollback_safely(db)
            return False
        finally:
            self._close_safely(db)
    async def restore_running_bots(
        self,
    ) -> TradingBotRuntimeRestoreResult:
        db = self.session_factory()
        repository = (
            self.repository_factory(db)
        )
        try:
            bots = repository.list_by_status(
                status="RUNNING"
            )
        except Exception as error:
            self._rollback_safely(db)
            return (
                TradingBotRuntimeRestoreResult(
                    scanned_count=0,
                    restored_count=0,
                    failed_count=1,
                    errors=[
                        self._error_text(error)
                    ],
                )
            )
        finally:
            self._close_safely(db)
        restored_count = 0
        failed_count = 0
        errors: list[str] = []
        for bot in bots:
            try:
                await self.start_for_bot(bot)
                restored_count += 1
            except Exception as error:
                failed_count += 1
                error_text = self._error_text(
                    error
                )
                errors.append(
                    (
                        f"Bot {bot.id}: "
                        f"{error_text}"
                    )
                )
                self.mark_runtime_error(
                    user_id=bot.user_id,
                    bot_id=bot.id,
                    error=error,
                )
        return TradingBotRuntimeRestoreResult(
            scanned_count=len(bots),
            restored_count=restored_count,
            failed_count=failed_count,
            errors=errors,
        )
