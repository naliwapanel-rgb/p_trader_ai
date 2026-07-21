from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.services.trading_bot_lifecycle_service import (
    TradingBotLifecycleService,
)
FIXED_TIME = datetime(
    2026,
    7,
    21,
    13,
    0,
    tzinfo=UTC,
)
def build_bot(
    *,
    status: str = "DRAFT",
    exchange_account_id: int | None = 3,
    paper_trading: bool = True,
    dry_run: bool = True,
):
    timestamp = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )
    return SimpleNamespace(
        id=10,
        user_id=7,
        exchange_account_id=(
            exchange_account_id
        ),
        name="Lifecycle Bot",
        description="Lifecycle test bot",
        strategy_type="MOMENTUM",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status=status,
        paper_trading=paper_trading,
        dry_run=dry_run,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=2.0,
        take_profit_percent=4.0,
        strategy_config={
            "period": 14,
        },
        last_error=None,
        started_at=None,
        stopped_at=None,
        last_run_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )
def build_service(
    *,
    bot,
    account_active: bool = True,
    account_exists: bool = True,
):
    service = TradingBotLifecycleService(
        MagicMock(),
        clock=lambda: FIXED_TIME,
    )
    service.bot_repository = MagicMock()
    service.exchange_account_repository = (
        MagicMock()
    )
    service.bot_repository.get_by_id_and_user.return_value = (
        bot
    )
    if account_exists:
        account = SimpleNamespace(
            id=3,
            user_id=7,
            is_active=account_active,
        )
    else:
        account = None
    service.exchange_account_repository.get_by_id_and_user.return_value = (
        account
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
    service.bot_repository.save_lifecycle.side_effect = (
        save_lifecycle
    )
    return service
def test_prepare_moves_draft_to_stopped():
    bot = build_bot(
        status="DRAFT"
    )
    service = build_service(bot=bot)
    result = service.prepare_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.changed is True
    assert result.previous_status == "DRAFT"
    assert result.status == "STOPPED"
    assert result.bot.stopped_at == FIXED_TIME
def test_prepare_is_idempotent():
    bot = build_bot(
        status="STOPPED"
    )
    service = build_service(bot=bot)
    result = service.prepare_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.changed is False
    assert result.status == "STOPPED"
    service.bot_repository.save_lifecycle.assert_not_called()
def test_prepare_rejects_running_bot():
    service = build_service(
        bot=build_bot(
            status="RUNNING"
        )
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.prepare_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 409
def test_start_draft_uses_safe_transitions():
    bot = build_bot(
        status="DRAFT"
    )
    service = build_service(bot=bot)
    result = service.start_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    statuses = [
        call.kwargs["status"]
        for call
        in (
            service.bot_repository
            .save_lifecycle.call_args_list
        )
    ]
    assert statuses == [
        "STOPPED",
        "STARTING",
        "RUNNING",
    ]
    assert result.previous_status == "DRAFT"
    assert result.status == "RUNNING"
    assert result.bot.started_at == FIXED_TIME
def test_start_stopped_bot():
    bot = build_bot(
        status="STOPPED"
    )
    service = build_service(bot=bot)
    result = service.start_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    statuses = [
        call.kwargs["status"]
        for call
        in (
            service.bot_repository
            .save_lifecycle.call_args_list
        )
    ]
    assert statuses == [
        "STARTING",
        "RUNNING",
    ]
    assert result.status == "RUNNING"
def test_start_is_idempotent():
    service = build_service(
        bot=build_bot(
            status="RUNNING"
        )
    )
    result = service.start_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.changed is False
    service.bot_repository.save_lifecycle.assert_not_called()
def test_start_requires_exchange_account():
    service = build_service(
        bot=build_bot(
            status="STOPPED",
            exchange_account_id=None,
        )
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.start_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 400
    assert "requires an exchange account" in (
        exc_info.value.detail
    )
def test_start_rejects_missing_account():
    service = build_service(
        bot=build_bot(
            status="STOPPED"
        ),
        account_exists=False,
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.start_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 404
def test_start_rejects_inactive_account():
    service = build_service(
        bot=build_bot(
            status="STOPPED"
        ),
        account_active=False,
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.start_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Exchange account is inactive"
    )
def test_start_rejects_unsafe_execution():
    service = build_service(
        bot=build_bot(
            status="STOPPED",
            paper_trading=False,
            dry_run=False,
        )
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.start_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 409
    assert "execution safety" in (
        exc_info.value.detail
    )
def test_pause_running_bot():
    service = build_service(
        bot=build_bot(
            status="RUNNING"
        )
    )
    result = service.pause_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.status == "PAUSED"
    assert result.changed is True
def test_pause_rejects_stopped_bot():
    service = build_service(
        bot=build_bot(
            status="STOPPED"
        )
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.pause_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 409
def test_resume_paused_bot():
    service = build_service(
        bot=build_bot(
            status="PAUSED"
        )
    )
    result = service.resume_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.status == "RUNNING"
    assert result.changed is True
def test_resume_revalidates_account():
    service = build_service(
        bot=build_bot(
            status="PAUSED"
        ),
        account_active=False,
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.resume_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 400
def test_stop_running_bot():
    service = build_service(
        bot=build_bot(
            status="RUNNING"
        )
    )
    result = service.stop_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.status == "STOPPED"
    assert result.bot.stopped_at == FIXED_TIME
def test_stop_error_bot():
    service = build_service(
        bot=build_bot(
            status="ERROR"
        )
    )
    result = service.stop_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.previous_status == "ERROR"
    assert result.status == "STOPPED"
def test_stop_is_idempotent():
    service = build_service(
        bot=build_bot(
            status="STOPPED"
        )
    )
    result = service.stop_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    assert result.changed is False
    service.bot_repository.save_lifecycle.assert_not_called()
