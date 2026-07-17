from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.api.v1.endpoints.exchange_connections import (
    remove_exchange_position_tp_sl,
)
from app.schemas.exchange_trade import (
    RemovePositionTpSlRequest,
)
@pytest.mark.asyncio
async def test_remove_position_tp_sl_endpoint_calls_client():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=4,
        exchange_name="BYBIT",
    )
    db = MagicMock()
    expected_result = {
        "exchange": "BYBIT",
        "category": "linear",
        "symbol": "BTCUSDT",
        "position_side": "LONG",
        "position_index": 0,
        "take_profit": None,
        "stop_loss": 64000.0,
        "dry_run": True,
        "accepted": False,
        "message": (
            "Dry run completed. No TP/SL update was "
            "sent to Bybit."
        ),
    }
    client = MagicMock()
    client.remove_position_tp_sl = AsyncMock(
        return_value=expected_result
    )
    data = RemovePositionTpSlRequest(
        symbol="btcusdt",
        remove_take_profit=True,
        category="linear",
        settle_coin="usdt",
        position_side="LONG",
        dry_run=True,
    )
    with (
        patch(
            "app.api.v1.endpoints.exchange_connections."
            "ExchangeAccountService"
        ) as service_class,
        patch(
            "app.api.v1.endpoints.exchange_connections."
            "ExchangeFactory.create_client",
            return_value=client,
        ),
    ):
        service_class.return_value.get_account.return_value = (
            account
        )
        response = await remove_exchange_position_tp_sl(
            account_id=4,
            data=data,
            current_user=current_user,
            db=db,
        )
    service_class.return_value.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=4,
    )
    client.remove_position_tp_sl.assert_awaited_once_with(
        symbol="BTCUSDT",
        remove_take_profit=True,
        remove_stop_loss=False,
        category="linear",
        settle_coin="USDT",
        position_side="LONG",
        dry_run=True,
    )
    assert response["success"] is True
    assert (
        response["message"]
        == (
            "Position TP/SL removal processed "
            "successfully"
        )
    )
    assert response["data"] == expected_result
@pytest.mark.asyncio
async def test_remove_position_tp_sl_allows_both():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=4,
        exchange_name="BYBIT",
    )
    db = MagicMock()
    client = MagicMock()
    client.remove_position_tp_sl = AsyncMock(
        return_value={
            "take_profit": None,
            "stop_loss": None,
            "accepted": False,
        }
    )
    data = RemovePositionTpSlRequest(
        symbol="ETHUSDT",
        remove_take_profit=True,
        remove_stop_loss=True,
    )
    with (
        patch(
            "app.api.v1.endpoints.exchange_connections."
            "ExchangeAccountService"
        ) as service_class,
        patch(
            "app.api.v1.endpoints.exchange_connections."
            "ExchangeFactory.create_client",
            return_value=client,
        ),
    ):
        service_class.return_value.get_account.return_value = (
            account
        )
        await remove_exchange_position_tp_sl(
            account_id=4,
            data=data,
            current_user=current_user,
            db=db,
        )
    client.remove_position_tp_sl.assert_awaited_once_with(
        symbol="ETHUSDT",
        remove_take_profit=True,
        remove_stop_loss=True,
        category="linear",
        settle_coin="USDT",
        position_side=None,
        dry_run=True,
    )
@pytest.mark.asyncio
async def test_remove_position_tp_sl_rejects_unsupported_exchange():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=4,
        exchange_name="BINANCE",
    )
    db = MagicMock()
    client = MagicMock(spec=[])
    data = RemovePositionTpSlRequest(
        symbol="BTCUSDT",
        remove_stop_loss=True,
    )
    with (
        patch(
            "app.api.v1.endpoints.exchange_connections."
            "ExchangeAccountService"
        ) as service_class,
        patch(
            "app.api.v1.endpoints.exchange_connections."
            "ExchangeFactory.create_client",
            return_value=client,
        ),
    ):
        service_class.return_value.get_account.return_value = (
            account
        )
        with pytest.raises(HTTPException) as exc_info:
            await remove_exchange_position_tp_sl(
                account_id=4,
                data=data,
                current_user=current_user,
                db=db,
            )
    assert exc_info.value.status_code == 501
    assert (
        exc_info.value.detail
        == (
            "Position TP/SL removal is not "
            "supported for this exchange"
        )
    )
def test_remove_position_tp_sl_schema_requires_selection():
    with pytest.raises(ValidationError) as exc_info:
        RemovePositionTpSlRequest(
            symbol="BTCUSDT",
        )
    assert (
        "At least one of remove_take_profit"
        in str(exc_info.value)
    )
def test_remove_position_tp_sl_schema_normalizes_values():
    data = RemovePositionTpSlRequest(
        symbol="btcusdt",
        settle_coin="usdt",
        remove_stop_loss=True,
    )
    assert data.symbol == "BTCUSDT"
    assert data.settle_coin == "USDT"
