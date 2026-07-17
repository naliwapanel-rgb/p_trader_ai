from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from app.api.v1.endpoints.exchange_connections import (
    set_exchange_position_tp_sl,
)
from app.schemas.exchange_trade import (
    SetPositionTpSlRequest,
)
@pytest.mark.asyncio
async def test_position_tp_sl_endpoint_calls_client():
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
        "take_profit": 72000.0,
        "stop_loss": 65000.0,
        "tp_trigger_by": "LastPrice",
        "sl_trigger_by": "MarkPrice",
        "dry_run": True,
        "accepted": False,
        "message": (
            "Dry run completed. No TP/SL update was "
            "sent to Bybit."
        ),
    }
    client = MagicMock()
    client.set_position_tp_sl = AsyncMock(
        return_value=expected_result
    )
    data = SetPositionTpSlRequest(
        symbol="btcusdt",
        take_profit=72000,
        stop_loss=65000,
        category="linear",
        settle_coin="usdt",
        position_side="LONG",
        tp_trigger_by="LastPrice",
        sl_trigger_by="MarkPrice",
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
        response = await set_exchange_position_tp_sl(
            account_id=4,
            data=data,
            current_user=current_user,
            db=db,
        )
    service_class.return_value.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=4,
    )
    client.set_position_tp_sl.assert_awaited_once_with(
        symbol="BTCUSDT",
        take_profit=72000.0,
        stop_loss=65000.0,
        category="linear",
        settle_coin="USDT",
        position_side="LONG",
        tp_trigger_by="LastPrice",
        sl_trigger_by="MarkPrice",
        dry_run=True,
    )
    assert response["success"] is True
    assert (
        response["message"]
        == "Position TP/SL processed successfully"
    )
    assert response["data"] == expected_result
@pytest.mark.asyncio
async def test_position_tp_sl_endpoint_allows_tp_only():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=4,
        exchange_name="BYBIT",
    )
    db = MagicMock()
    client = MagicMock()
    client.set_position_tp_sl = AsyncMock(
        return_value={
            "accepted": False,
            "take_profit": 72000.0,
        }
    )
    data = SetPositionTpSlRequest(
        symbol="ethusdt",
        take_profit=72000,
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
        await set_exchange_position_tp_sl(
            account_id=4,
            data=data,
            current_user=current_user,
            db=db,
        )
    client.set_position_tp_sl.assert_awaited_once_with(
        symbol="ETHUSDT",
        take_profit=72000.0,
        stop_loss=None,
        category="linear",
        settle_coin="USDT",
        position_side=None,
        tp_trigger_by="MarkPrice",
        sl_trigger_by="MarkPrice",
        dry_run=True,
    )
@pytest.mark.asyncio
async def test_position_tp_sl_endpoint_allows_sl_only():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=4,
        exchange_name="BYBIT",
    )
    db = MagicMock()
    client = MagicMock()
    client.set_position_tp_sl = AsyncMock(
        return_value={
            "accepted": False,
            "stop_loss": 65000.0,
        }
    )
    data = SetPositionTpSlRequest(
        symbol="BTCUSDT",
        stop_loss=65000,
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
        await set_exchange_position_tp_sl(
            account_id=4,
            data=data,
            current_user=current_user,
            db=db,
        )
    client.set_position_tp_sl.assert_awaited_once_with(
        symbol="BTCUSDT",
        take_profit=None,
        stop_loss=65000.0,
        category="linear",
        settle_coin="USDT",
        position_side=None,
        tp_trigger_by="MarkPrice",
        sl_trigger_by="MarkPrice",
        dry_run=True,
    )
@pytest.mark.asyncio
async def test_position_tp_sl_rejects_unsupported_exchange():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=9,
        exchange_name="BINANCE",
    )
    db = MagicMock()
    client = MagicMock(
        spec=[
            "get_positions",
        ]
    )
    data = SetPositionTpSlRequest(
        symbol="BTCUSDT",
        take_profit=72000,
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
        with pytest.raises(HTTPException) as error:
            await set_exchange_position_tp_sl(
                account_id=9,
                data=data,
                current_user=current_user,
                db=db,
            )
    assert error.value.status_code == 501
    assert (
        error.value.detail
        == (
            "Position TP/SL management is not "
            "supported for this exchange"
        )
    )
def test_position_tp_sl_schema_requires_protection_value():
    with pytest.raises(ValueError):
        SetPositionTpSlRequest(
            symbol="BTCUSDT",
        )
@pytest.mark.parametrize(
    "field, value",
    [
        ("take_profit", 0),
        ("take_profit", -1),
        ("stop_loss", 0),
        ("stop_loss", -1),
    ],
)
def test_position_tp_sl_schema_rejects_invalid_price(
    field,
    value,
):
    payload = {
        "symbol": "BTCUSDT",
        field: value,
    }
    with pytest.raises(ValueError):
        SetPositionTpSlRequest(**payload)
