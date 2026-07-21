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
from sqlalchemy.exc import (
    IntegrityError,
)
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
    TradingBotUpdateRequest,
)
from app.services.trading_bot_service import (
    TradingBotService,
)
def build_bot(
    *,
    bot_id: int = 10,
    user_id: int = 7,
    name: str = "BTC Bot",
    status: str = "DRAFT",
    exchange_account_id: int | None = 3,
):
    return SimpleNamespace(
        id=bot_id,
        user_id=user_id,
        name=name,
        status=status,
        exchange_account_id=(
            exchange_account_id
        ),
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
    )
def build_create_request(
    **updates,
):
    values = {
        "exchange_account_id": 3,
        "name": "BTC Bot",
        "strategy_type": "MOMENTUM",
        "symbol": "BTCUSDT",
        "category": "linear",
        "timeframe": "5m",
        "paper_trading": True,
        "dry_run": True,
    }
    values.update(updates)
    return TradingBotCreateRequest(
        **values
    )
def build_service():
    db = MagicMock()
    service = TradingBotService(db)
    service.bot_repository = MagicMock()
    service.exchange_account_repository = (
        MagicMock()
    )
    return service, db
def test_list_is_user_scoped():
    service, _ = build_service()
    user = SimpleNamespace(id=7)
    bots = [
        build_bot(),
    ]
    service.bot_repository.list_by_user.return_value = (
        bots
    )
    result = service.list_bots(
        current_user=user,
        bot_status="DRAFT",
        limit=25,
        offset=5,
    )
    assert result == bots
    service.bot_repository.list_by_user.assert_called_once_with(
        user_id=7,
        status="DRAFT",
        limit=25,
        offset=5,
    )
def test_get_missing_bot_is_rejected():
    service, _ = build_service()
    service.bot_repository.get_by_id_and_user.return_value = (
        None
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.get_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "Trading bot not found"
    )
def test_create_validates_account_and_name():
    service, _ = build_service()
    user = SimpleNamespace(id=7)
    request = build_create_request()
    bot = build_bot()
    account = SimpleNamespace(
        id=3,
        user_id=7,
        is_active=True,
    )
    service.exchange_account_repository.get_by_id_and_user.return_value = (
        account
    )
    service.bot_repository.get_by_name_and_user.return_value = (
        None
    )
    service.bot_repository.create.return_value = (
        bot
    )
    result = service.create_bot(
        current_user=user,
        data=request,
    )
    assert result is bot
    service.exchange_account_repository.get_by_id_and_user.assert_called_once_with(
        account_id=3,
        user_id=7,
    )
    service.bot_repository.create.assert_called_once_with(
        user_id=7,
        data=request,
    )
def test_create_rejects_missing_account():
    service, _ = build_service()
    service.exchange_account_repository.get_by_id_and_user.return_value = (
        None
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.create_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            data=build_create_request(),
        )
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "Exchange account not found"
    )
def test_create_rejects_inactive_account():
    service, _ = build_service()
    service.exchange_account_repository.get_by_id_and_user.return_value = (
        SimpleNamespace(
            id=3,
            user_id=7,
            is_active=False,
        )
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.create_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            data=build_create_request(),
        )
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Exchange account is inactive"
    )
def test_create_rejects_duplicate_name():
    service, _ = build_service()
    service.exchange_account_repository.get_by_id_and_user.return_value = (
        SimpleNamespace(
            id=3,
            user_id=7,
            is_active=True,
        )
    )
    service.bot_repository.get_by_name_and_user.return_value = (
        build_bot()
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.create_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            data=build_create_request(),
        )
    assert exc_info.value.status_code == 409
    assert "already exists" in (
        exc_info.value.detail
    )
def test_create_integrity_error_is_sanitized():
    service, db = build_service()
    service.exchange_account_repository.get_by_id_and_user.return_value = (
        SimpleNamespace(
            id=3,
            user_id=7,
            is_active=True,
        )
    )
    service.bot_repository.get_by_name_and_user.return_value = (
        None
    )
    service.bot_repository.create.side_effect = (
        IntegrityError(
            "insert",
            {},
            RuntimeError("duplicate"),
        )
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.create_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            data=build_create_request(),
        )
    assert exc_info.value.status_code == 409
    assert "duplicate" not in (
        exc_info.value.detail.lower()
    )
    db.rollback.assert_called_once()
def test_active_bot_cannot_be_updated():
    service, _ = build_service()
    service.bot_repository.get_by_id_and_user.return_value = (
        build_bot(status="RUNNING")
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.update_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
            data=TradingBotUpdateRequest(
                name="Updated Bot"
            ),
        )
    assert exc_info.value.status_code == 409
    assert (
        exc_info.value.detail
        == (
            "Active trading bots cannot "
            "be modified"
        )
    )
def test_active_status_requires_lifecycle_controls():
    service, _ = build_service()
    service.bot_repository.get_by_id_and_user.return_value = (
        build_bot(status="STOPPED")
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.update_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
            data=TradingBotUpdateRequest(
                status="RUNNING"
            ),
        )
    assert exc_info.value.status_code == 409
    assert "lifecycle controls" in (
        exc_info.value.detail
    )
def test_update_validates_account_and_name():
    service, _ = build_service()
    user = SimpleNamespace(id=7)
    bot = build_bot(
        status="STOPPED"
    )
    account = SimpleNamespace(
        id=4,
        user_id=7,
        is_active=True,
    )
    request = TradingBotUpdateRequest(
        exchange_account_id=4,
        name="Updated Bot",
        paper_trading=False,
        dry_run=True,
    )
    service.bot_repository.get_by_id_and_user.return_value = (
        bot
    )
    service.exchange_account_repository.get_by_id_and_user.return_value = (
        account
    )
    service.bot_repository.get_by_name_and_user.return_value = (
        None
    )
    service.bot_repository.update.return_value = (
        bot
    )
    result = service.update_bot(
        current_user=user,
        bot_id=10,
        data=request,
    )
    assert result is bot
    service.exchange_account_repository.get_by_id_and_user.assert_called_once_with(
        account_id=4,
        user_id=7,
    )
    service.bot_repository.update.assert_called_once_with(
        bot=bot,
        data=request,
    )
def test_active_bot_cannot_be_deleted():
    service, _ = build_service()
    service.bot_repository.get_by_id_and_user.return_value = (
        build_bot(status="PAUSED")
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        service.delete_bot(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
        )
    assert exc_info.value.status_code == 409
    assert "stopped before deletion" in (
        exc_info.value.detail
    )
def test_stopped_bot_can_be_deleted():
    service, _ = build_service()
    bot = build_bot(
        status="STOPPED"
    )
    service.bot_repository.get_by_id_and_user.return_value = (
        bot
    )
    service.delete_bot(
        current_user=(
            SimpleNamespace(id=7)
        ),
        bot_id=10,
    )
    service.bot_repository.delete.assert_called_once_with(
        bot
    )
