from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas.automation import (
    AutomationJobSubmission,
)
from app.schemas.automation_trade import (
    AutomatedLimitOrderJob,
    AutomatedMarketOrderJob,
)
from app.services.automation_trade_execution_service import (
    AutomatedTradeExecutionService,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
def build_risk_context(
    *,
    estimated_entry_price=100,
):
    return {
        "account_equity": 10000,
        "requested_leverage": 5,
        "estimated_entry_price": (
            estimated_entry_price
        ),
        "stop_loss_price": 95,
        "take_profit_price": 110,
        "current_open_positions": 0,
        "current_total_exposure_percent": 10,
        "current_daily_loss_percent": 0,
        "current_drawdown_percent": 0,
    }
def build_market_payload():
    return {
        "user_id": 1,
        "account_id": 2,
        "order": {
            "symbol": "btcusdt",
            "side": "BUY",
            "quantity": 0.01,
            "risk_context": (
                build_risk_context()
            ),
        },
    }
def build_limit_payload():
    return {
        "user_id": 1,
        "account_id": 2,
        "order": {
            "symbol": "ethusdt",
            "side": "SELL",
            "quantity": 0.1,
            "price": 2000,
            "risk_context": (
                build_risk_context(
                    estimated_entry_price=2000
                )
            ),
        },
    }
def build_service(
    *,
    user=None,
    market_result=None,
    limit_result=None,
):
    db = MagicMock()
    repository = MagicMock()
    repository.get_by_id.return_value = (
        user
        or SimpleNamespace(
            id=1,
            is_active=True,
        )
    )
    trading_service = MagicMock()
    trading_service.place_market_order = (
        AsyncMock(
            return_value=(
                market_result
                or {
                    "exchange": "BYBIT",
                    "dry_run": True,
                    "accepted": False,
                }
            )
        )
    )
    trading_service.place_limit_order = (
        AsyncMock(
            return_value=(
                limit_result
                or {
                    "exchange": "BYBIT",
                    "dry_run": True,
                    "accepted": False,
                }
            )
        )
    )
    service = (
        AutomatedTradeExecutionService(
            session_factory=lambda: db,
            user_repository_factory=(
                lambda current_db:
                repository
            ),
            trading_service_factory=(
                lambda current_db:
                trading_service
            ),
        )
    )
    return (
        service,
        db,
        repository,
        trading_service,
    )
def test_market_job_normalizes_symbol():
    job = AutomatedMarketOrderJob(
        **build_market_payload()
    )
    assert job.order.symbol == (
        "BTCUSDT"
    )
def test_limit_job_rejects_invalid_user_id():
    payload = build_limit_payload()
    payload["user_id"] = 0
    with pytest.raises(
        ValidationError
    ):
        AutomatedLimitOrderJob(
            **payload
        )
def test_register_handlers():
    service, _, _, _ = (
        build_service()
    )
    worker = AutomationWorker()
    service.register_handlers(
        worker
    )
    assert (
        worker
        .snapshot()
        .registered_job_types
        == [
            "TRADE_LIMIT_ORDER",
            "TRADE_MARKET_ORDER",
        ]
    )
def test_duplicate_registration_is_rejected():
    service, _, _, _ = (
        build_service()
    )
    worker = AutomationWorker()
    service.register_handlers(
        worker
    )
    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        service.register_handlers(
            worker
        )
@pytest.mark.asyncio
async def test_market_order_execution():
    service, db, repository, trading = (
        build_service()
    )
    result = (
        await service
        .execute_market_order(
            build_market_payload()
        )
    )
    assert result["execution_type"] == (
        "MARKET_ORDER"
    )
    assert result["symbol"] == (
        "BTCUSDT"
    )
    assert result["account_id"] == 2
    repository.get_by_id.assert_called_once_with(
        1
    )
    (
        trading
        .place_market_order
        .assert_awaited_once()
    )
    db.close.assert_called_once()
@pytest.mark.asyncio
async def test_limit_order_execution():
    service, db, _, trading = (
        build_service()
    )
    result = (
        await service
        .execute_limit_order(
            build_limit_payload()
        )
    )
    assert result["execution_type"] == (
        "LIMIT_ORDER"
    )
    assert result["symbol"] == (
        "ETHUSDT"
    )
    assert result["side"] == "SELL"
    (
        trading
        .place_limit_order
        .assert_awaited_once()
    )
    db.close.assert_called_once()
@pytest.mark.asyncio
async def test_missing_user_is_rejected():
    service, db, repository, trading = (
        build_service()
    )
    repository.get_by_id.return_value = None
    with pytest.raises(
        HTTPException
    ) as exc_info:
        await service.execute_market_order(
            build_market_payload()
        )
    assert exc_info.value.status_code == 404
    assert (
        "was not found"
        in str(exc_info.value.detail)
    )
    (
        trading
        .place_market_order
        .assert_not_awaited()
    )
    db.rollback.assert_called_once()
    db.close.assert_called_once()
@pytest.mark.asyncio
async def test_inactive_user_is_rejected():
    inactive_user = SimpleNamespace(
        id=1,
        is_active=False,
    )
    service, db, _, trading = (
        build_service(
            user=inactive_user
        )
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        await service.execute_limit_order(
            build_limit_payload()
        )
    assert exc_info.value.status_code == 403
    (
        trading
        .place_limit_order
        .assert_not_awaited()
    )
    db.rollback.assert_called_once()
    db.close.assert_called_once()
@pytest.mark.asyncio
async def test_service_failure_rolls_back():
    service, db, _, trading = (
        build_service()
    )
    (
        trading
        .place_market_order
        .side_effect
    ) = RuntimeError(
        "exchange failure"
    )
    with pytest.raises(
        RuntimeError,
        match="exchange failure",
    ):
        await service.execute_market_order(
            build_market_payload()
        )
    db.rollback.assert_called_once()
    db.close.assert_called_once()
@pytest.mark.asyncio
async def test_worker_executes_trade_handler():
    service, _, _, trading = (
        build_service()
    )
    worker = AutomationWorker(
        id_factory=lambda: "trade-job-1"
    )
    service.register_handlers(
        worker
    )
    submitted = await worker.submit(
        AutomationJobSubmission(
            job_type=(
                "TRADE_MARKET_ORDER"
            ),
            payload=(
                build_market_payload()
            ),
            deduplication_key=(
                "trade:user-1:btc-1"
            ),
        )
    )
    completed = await worker.run_once()
    assert submitted.created is True
    assert completed is not None
    assert completed.status == (
        "SUCCEEDED"
    )
    assert completed.attempt_count == 1
    assert completed.retry_count == 0
    assert (
        completed.result[
            "execution_type"
        ]
        == "MARKET_ORDER"
    )
    (
        trading
        .place_market_order
        .assert_awaited_once()
    )
