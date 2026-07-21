from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
import pytest
from app.schemas.automation import (
    AutomationIntervalSchedule,
    AutomationScheduleState,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
from app.services.trading_bot_runtime_service import (
    TradingBotRuntimeService,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
FIXED_TIME = datetime(
    2026,
    7,
    21,
    15,
    0,
    tzinfo=UTC,
)
def build_bot(
    *,
    status: str = "RUNNING",
    strategy_type: str = "RULE_BASED",
):
    return SimpleNamespace(
        id=10,
        user_id=7,
        exchange_account_id=3,
        strategy_type=strategy_type,
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        strategy_config={},
        status=status,
        last_run_at=None,
        last_error=None,
        updated_at=None,
    )
def build_account(
    *,
    exchange_name: str = "BYBIT",
    is_active: bool = True,
    is_testnet: bool = True,
):
    return SimpleNamespace(
        id=3,
        user_id=7,
        exchange_name=exchange_name,
        is_active=is_active,
        is_testnet=is_testnet,
    )
def build_ticker(
    *,
    change_percent: float = 2.5,
):
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="linear",
        symbol="BTCUSDT",
        last_price=60000,
        bid_price=59999,
        ask_price=60001,
        spread=2,
        spread_percent=0.003333,
        price_change_percent_24h=(
            change_percent
        ),
        volume_24h=100,
        turnover_24h=6000000,
        observed_at_ms=123456789,
    )
def build_decision(
    *,
    action: str = "BUY",
):
    return TradingBotStrategyDecision(
        action=action,
        confidence=0.5,
        reason="Configured threshold reached",
        reference_price=60000,
        evaluated_at=FIXED_TIME,
        metadata={
            "source": "unit-test",
        },
    )
def build_state(
    *,
    running: bool,
):
    return AutomationScheduleState(
        schedule_id="trading-bot:7:10",
        job_type="TRADING_BOT_TICK",
        enabled=True,
        running=running,
        interval_seconds=60,
    )
def build_scheduler():
    scheduler = MagicMock()
    scheduler.get_schedule.return_value = (
        None
    )
    scheduler.register_schedule.return_value = (
        build_state(
            running=False
        )
    )
    scheduler.start_schedule = AsyncMock(
        return_value=True
    )
    scheduler.stop_schedule = AsyncMock(
        return_value=True
    )
    scheduler.get_state.return_value = (
        build_state(
            running=True
        )
    )
    return scheduler
def build_dependencies(
    *,
    bot,
    account=None,
):
    db = MagicMock()
    repository = MagicMock()
    repository.get_by_id_and_user.return_value = (
        bot
    )
    def save_lifecycle(
        *,
        bot,
        status,
        updated_at,
        **fields,
    ):
        bot.status = status
        bot.updated_at = updated_at
        for key, value in fields.items():
            setattr(bot, key, value)
        return bot
    repository.save_lifecycle.side_effect = (
        save_lifecycle
    )
    account_repository = MagicMock()
    account_repository.get_by_id_and_user.return_value = (
        account
        if account is not None
        else build_account()
    )
    return (
        db,
        repository,
        account_repository,
    )
def build_strategy_runner(
    *,
    decision=None,
):
    runner = MagicMock()
    runner.validate_bot.return_value = {}
    runner.run = AsyncMock(
        return_value=(
            decision
            if decision is not None
            else build_decision()
        )
    )
    return runner
def build_market_scanner(
    *,
    ticker=None,
):
    scanner = MagicMock()
    scanner.get_tickers = AsyncMock(
        return_value=SimpleNamespace(
            tickers=[
                ticker
                if ticker is not None
                else build_ticker()
            ]
        )
    )
    return scanner
def test_schedule_identifiers_are_stable():
    assert (
        TradingBotRuntimeService
        .schedule_id(
            user_id=7,
            bot_id=10,
        )
        == "trading-bot:7:10"
    )
    assert (
        TradingBotRuntimeService
        .deduplication_key(
            user_id=7,
            bot_id=10,
        )
        == "trading-bot-tick:7:10"
    )
def test_runtime_handler_registration():
    scheduler = build_scheduler()
    service = TradingBotRuntimeService(
        scheduler=scheduler
    )
    worker = AutomationWorker()
    service.register_handler(worker)
    assert (
        TradingBotRuntimeService.JOB_TYPE
        in (
            worker.snapshot()
            .registered_job_types
        )
    )
def test_duplicate_handler_is_rejected():
    scheduler = build_scheduler()
    service = TradingBotRuntimeService(
        scheduler=scheduler
    )
    worker = AutomationWorker()
    service.register_handler(worker)
    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        service.register_handler(worker)
@pytest.mark.asyncio
async def test_start_registers_and_starts_schedule():
    scheduler = build_scheduler()
    strategy_runner = (
        build_strategy_runner()
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        strategy_runner=strategy_runner,
    )
    bot = build_bot()
    result = await service.start_for_bot(
        bot
    )
    assert result.registered is True
    assert result.changed is True
    assert result.running is True
    strategy_runner.validate_bot.assert_called_once_with(
        bot
    )
    scheduler.register_schedule.assert_called_once()
    definition = (
        scheduler.register_schedule
        .call_args.args[0]
    )
    assert isinstance(
        definition,
        AutomationIntervalSchedule,
    )
    assert (
        definition.job_type
        == "TRADING_BOT_TICK"
    )
    assert definition.payload == {
        "user_id": 7,
        "bot_id": 10,
    }
@pytest.mark.asyncio
async def test_start_reuses_existing_schedule():
    scheduler = build_scheduler()
    scheduler.get_schedule.return_value = (
        AutomationIntervalSchedule(
            schedule_id=(
                "trading-bot:7:10"
            ),
            job_type=(
                "TRADING_BOT_TICK"
            ),
            interval_seconds=60,
            initial_delay_seconds=60,
            payload={
                "user_id": 7,
                "bot_id": 10,
            },
            deduplication_key=(
                "trading-bot-tick:7:10"
            ),
        )
    )
    scheduler.start_schedule.return_value = (
        False
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        strategy_runner=(
            build_strategy_runner()
        ),
    )
    result = await service.start_for_bot(
        build_bot()
    )
    assert result.registered is False
    assert result.changed is False
    scheduler.register_schedule.assert_not_called()
@pytest.mark.asyncio
async def test_invalid_strategy_prevents_start():
    scheduler = build_scheduler()
    strategy_runner = (
        build_strategy_runner()
    )
    strategy_runner.validate_bot.side_effect = (
        ValueError(
            "Unsupported trading bot strategy"
        )
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        strategy_runner=strategy_runner,
    )
    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        await service.start_for_bot(
            build_bot(
                strategy_type="MOMENTUM"
            )
        )
    scheduler.register_schedule.assert_not_called()
    scheduler.start_schedule.assert_not_awaited()
@pytest.mark.asyncio
async def test_conflicting_schedule_is_rejected():
    scheduler = build_scheduler()
    scheduler.get_schedule.return_value = (
        AutomationIntervalSchedule(
            schedule_id=(
                "trading-bot:7:10"
            ),
            job_type="OTHER_JOB",
            interval_seconds=60,
            payload={
                "user_id": 7,
                "bot_id": 10,
            },
        )
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        strategy_runner=(
            build_strategy_runner()
        ),
    )
    with pytest.raises(
        RuntimeError,
        match="conflicts",
    ):
        await service.start_for_bot(
            build_bot()
        )
@pytest.mark.asyncio
async def test_stop_missing_schedule_is_safe():
    scheduler = build_scheduler()
    scheduler.get_schedule.return_value = (
        None
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler
    )
    result = await service.stop_for_bot(
        build_bot()
    )
    assert result.registered is False
    assert result.changed is False
    assert result.running is False
    scheduler.stop_schedule.assert_not_awaited()
@pytest.mark.asyncio
async def test_tick_evaluates_running_bot():
    scheduler = build_scheduler()
    bot = build_bot(
        status="RUNNING"
    )
    (
        db,
        repository,
        account_repository,
    ) = build_dependencies(
        bot=bot
    )
    ticker = build_ticker()
    scanner = build_market_scanner(
        ticker=ticker
    )
    strategy_runner = (
        build_strategy_runner(
            decision=build_decision(
                action="BUY"
            )
        )
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        account_repository_factory=(
            lambda session:
            account_repository
        ),
        market_scanner_service=scanner,
        strategy_runner=strategy_runner,
        clock=lambda: FIXED_TIME,
    )
    result = await service.execute_tick({
        "user_id": 7,
        "bot_id": 10,
    })
    assert result["outcome"] == "EVALUATED"
    assert result["bot_status"] == "RUNNING"
    assert result["decision"]["action"] == "BUY"
    assert bot.last_run_at == FIXED_TIME
    assert bot.last_error is None
    scanner.get_tickers.assert_awaited_once_with(
        category="linear",
        is_testnet=True,
    )
    strategy_runner.run.assert_awaited_once_with(
        bot=bot,
        ticker=ticker,
    )
    db.close.assert_called_once()
@pytest.mark.asyncio
async def test_tick_skips_non_running_bot():
    scheduler = build_scheduler()
    bot = build_bot(
        status="PAUSED"
    )
    (
        db,
        repository,
        account_repository,
    ) = build_dependencies(
        bot=bot
    )
    scanner = build_market_scanner()
    strategy_runner = (
        build_strategy_runner()
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        account_repository_factory=(
            lambda session:
            account_repository
        ),
        market_scanner_service=scanner,
        strategy_runner=strategy_runner,
        clock=lambda: FIXED_TIME,
    )
    result = await service.execute_tick({
        "user_id": 7,
        "bot_id": 10,
    })
    assert result["outcome"] == "SKIPPED"
    assert result["bot_status"] == "PAUSED"
    assert result["decision"] is None
    repository.save_lifecycle.assert_not_called()
    scanner.get_tickers.assert_not_awaited()
    strategy_runner.run.assert_not_awaited()
@pytest.mark.asyncio
async def test_missing_tick_target_fails():
    scheduler = build_scheduler()
    db = MagicMock()
    repository = MagicMock()
    account_repository = MagicMock()
    repository.get_by_id_and_user.return_value = (
        None
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        account_repository_factory=(
            lambda session:
            account_repository
        ),
        strategy_runner=(
            build_strategy_runner()
        ),
    )
    with pytest.raises(
        ValueError,
        match="was not found",
    ):
        await service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
    db.rollback.assert_called_once()
    db.close.assert_called_once()
@pytest.mark.asyncio
async def test_missing_exchange_account_marks_error():
    scheduler = build_scheduler()
    bot = build_bot()
    (
        db,
        repository,
        account_repository,
    ) = build_dependencies(
        bot=bot,
        account=None,
    )
    account_repository.get_by_id_and_user.return_value = (
        None
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        account_repository_factory=(
            lambda session:
            account_repository
        ),
        strategy_runner=(
            build_strategy_runner()
        ),
        clock=lambda: FIXED_TIME,
    )
    with pytest.raises(
        ValueError,
        match="exchange account",
    ):
        await service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
    assert bot.status == "ERROR"
    assert (
        "exchange account"
        in bot.last_error.lower()
    )
@pytest.mark.asyncio
async def test_unsupported_exchange_marks_error():
    scheduler = build_scheduler()
    bot = build_bot()
    (
        db,
        repository,
        account_repository,
    ) = build_dependencies(
        bot=bot,
        account=build_account(
            exchange_name="BINANCE"
        ),
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        account_repository_factory=(
            lambda session:
            account_repository
        ),
        strategy_runner=(
            build_strategy_runner()
        ),
        clock=lambda: FIXED_TIME,
    )
    with pytest.raises(
        ValueError,
        match="BYBIT only",
    ):
        await service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
    assert bot.status == "ERROR"
    assert "BYBIT only" in bot.last_error
@pytest.mark.asyncio
async def test_missing_symbol_ticker_marks_error():
    scheduler = build_scheduler()
    bot = build_bot()
    (
        db,
        repository,
        account_repository,
    ) = build_dependencies(
        bot=bot
    )
    scanner = MagicMock()
    scanner.get_tickers = AsyncMock(
        return_value=SimpleNamespace(
            tickers=[
                MarketTickerSnapshot(
                    exchange="BYBIT",
                    category="linear",
                    symbol="ETHUSDT",
                    last_price=3000,
                    observed_at_ms=123456789,
                )
            ]
        )
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        account_repository_factory=(
            lambda session:
            account_repository
        ),
        market_scanner_service=scanner,
        strategy_runner=(
            build_strategy_runner()
        ),
        clock=lambda: FIXED_TIME,
    )
    with pytest.raises(
        ValueError,
        match="was not found",
    ):
        await service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
    assert bot.status == "ERROR"
    assert "BTCUSDT" in bot.last_error
def test_mark_runtime_error():
    scheduler = build_scheduler()
    bot = build_bot()
    (
        db,
        repository,
        _,
    ) = build_dependencies(
        bot=bot
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        strategy_runner=(
            build_strategy_runner()
        ),
        clock=lambda: FIXED_TIME,
    )
    changed = service.mark_runtime_error(
        user_id=7,
        bot_id=10,
        error=RuntimeError(
            "schedule failure"
        ),
    )
    assert changed is True
    assert bot.status == "ERROR"
    assert bot.last_error == "schedule failure"
@pytest.mark.asyncio
async def test_restore_running_bots():
    scheduler = build_scheduler()
    db = MagicMock()
    repository = MagicMock()
    bots = [
        build_bot(),
        SimpleNamespace(
            id=11,
            user_id=7,
            status="RUNNING",
        ),
    ]
    repository.list_by_status.return_value = (
        bots
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        strategy_runner=(
            build_strategy_runner()
        ),
    )
    service.start_for_bot = AsyncMock(
        side_effect=[
            SimpleNamespace(),
            RuntimeError(
                "restore failure"
            ),
        ]
    )
    service.mark_runtime_error = (
        MagicMock(
            return_value=True
        )
    )
    result = (
        await service
        .restore_running_bots()
    )
    assert result.scanned_count == 2
    assert result.restored_count == 1
    assert result.failed_count == 1
    assert len(result.errors) == 1
    service.mark_runtime_error.assert_called_once()
