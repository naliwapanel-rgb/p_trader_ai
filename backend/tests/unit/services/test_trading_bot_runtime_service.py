import asyncio
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
    14,
    0,
    tzinfo=UTC,
)
def build_bot(
    *,
    status: str = "RUNNING",
):
    return SimpleNamespace(
        id=10,
        user_id=7,
        status=status,
        last_run_at=None,
        last_error=None,
        updated_at=None,
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
def build_session_repository(
    *,
    bot,
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
    return db, repository
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
def test_start_registers_and_starts_schedule():
    async def scenario():
        scheduler = build_scheduler()
        service = TradingBotRuntimeService(
            scheduler=scheduler
        )
        result = await service.start_for_bot(
            build_bot()
        )
        assert result.registered is True
        assert result.changed is True
        assert result.running is True
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
    asyncio.run(scenario())
def test_start_reuses_existing_schedule():
    async def scenario():
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
            scheduler=scheduler
        )
        result = await service.start_for_bot(
            build_bot()
        )
        assert result.registered is False
        assert result.changed is False
        scheduler.register_schedule.assert_not_called()
    asyncio.run(scenario())
def test_conflicting_schedule_is_rejected():
    async def scenario():
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
            scheduler=scheduler
        )
        with pytest.raises(
            RuntimeError,
            match="conflicts",
        ):
            await service.start_for_bot(
                build_bot()
            )
    asyncio.run(scenario())
def test_stop_missing_schedule_is_safe():
    async def scenario():
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
        scheduler.stop_schedule.assert_not_called()
    asyncio.run(scenario())
def test_tick_updates_running_bot():
    async def scenario():
        scheduler = build_scheduler()
        bot = build_bot(
            status="RUNNING"
        )
        db, repository = (
            build_session_repository(
                bot=bot
            )
        )
        service = TradingBotRuntimeService(
            scheduler=scheduler,
            session_factory=lambda: db,
            repository_factory=(
                lambda session: repository
            ),
            clock=lambda: FIXED_TIME,
        )
        result = await service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
        assert result["outcome"] == "HEARTBEAT"
        assert result["bot_status"] == "RUNNING"
        assert bot.last_run_at == FIXED_TIME
        assert bot.last_error is None
        db.close.assert_called_once()
    asyncio.run(scenario())
def test_tick_skips_non_running_bot():
    async def scenario():
        scheduler = build_scheduler()
        bot = build_bot(
            status="PAUSED"
        )
        db, repository = (
            build_session_repository(
                bot=bot
            )
        )
        service = TradingBotRuntimeService(
            scheduler=scheduler,
            session_factory=lambda: db,
            repository_factory=(
                lambda session: repository
            ),
            clock=lambda: FIXED_TIME,
        )
        result = await service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
        assert result["outcome"] == "SKIPPED"
        assert result["bot_status"] == "PAUSED"
        repository.save_lifecycle.assert_not_called()
    asyncio.run(scenario())
def test_missing_tick_target_fails():
    async def scenario():
        scheduler = build_scheduler()
        db = MagicMock()
        repository = MagicMock()
        repository.get_by_id_and_user.return_value = (
            None
        )
        service = TradingBotRuntimeService(
            scheduler=scheduler,
            session_factory=lambda: db,
            repository_factory=(
                lambda session: repository
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
    asyncio.run(scenario())
def test_mark_runtime_error():
    scheduler = build_scheduler()
    bot = build_bot()
    db, repository = (
        build_session_repository(
            bot=bot
        )
    )
    service = TradingBotRuntimeService(
        scheduler=scheduler,
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
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
def test_restore_running_bots():
    async def scenario():
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
    asyncio.run(scenario())
