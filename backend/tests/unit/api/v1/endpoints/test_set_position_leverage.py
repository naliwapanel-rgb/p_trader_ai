from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.api.v1.endpoints import exchange_connections
from app.schemas.exchange_trade import (
    SetPositionLeverageRequest,
)
def test_position_leverage_schema_normalizes_symbol():
    request = SetPositionLeverageRequest(
        symbol=" btcusdt ",
        buy_leverage=10,
        sell_leverage=10,
    )
    assert request.symbol == "BTCUSDT"
    assert request.category == "linear"
    assert request.dry_run is True
@pytest.mark.parametrize(
    "field,value",
    [
        ("buy_leverage", 0),
        ("buy_leverage", -1),
        ("sell_leverage", 0),
        ("sell_leverage", -1),
    ],
)
def test_position_leverage_schema_rejects_invalid_values(
    field,
    value,
):
    data = {
        "symbol": "BTCUSDT",
        "buy_leverage": 10,
        "sell_leverage": 10,
    }
    data[field] = value
    with pytest.raises(ValidationError):
        SetPositionLeverageRequest(**data)
def test_position_leverage_schema_rejects_spot():
    with pytest.raises(ValidationError):
        SetPositionLeverageRequest(
            symbol="BTCUSDT",
            buy_leverage=10,
            sell_leverage=10,
            category="spot",
        )
@pytest.mark.asyncio
async def test_set_position_leverage_endpoint_success(
    monkeypatch,
):
    expected_result = {
        "exchange": "BYBIT",
        "category": "linear",
        "symbol": "BTCUSDT",
        "buy_leverage": 10.0,
        "sell_leverage": 10.0,
        "dry_run": True,
        "accepted": False,
        "message": (
            "Dry run completed. No leverage update was "
            "sent to Bybit."
        ),
    }
    account = SimpleNamespace(id=1)
    client = SimpleNamespace(
        set_position_leverage=AsyncMock(
            return_value=expected_result
        )
    )
    service_instance = Mock()
    service_instance.get_account.return_value = account
    service_class = Mock(
        return_value=service_instance
    )
    factory = Mock()
    factory.create_client.return_value = client
    monkeypatch.setattr(
        exchange_connections,
        "ExchangeAccountService",
        service_class,
    )
    monkeypatch.setattr(
        exchange_connections,
        "ExchangeFactory",
        factory,
    )
    current_user = SimpleNamespace(id=7)
    db = Mock()
    data = SetPositionLeverageRequest(
        symbol="btcusdt",
        buy_leverage=10,
        sell_leverage=10,
        category="linear",
        dry_run=True,
    )
    response = await (
        exchange_connections
        .set_exchange_position_leverage(
            account_id=1,
            data=data,
            current_user=current_user,
            db=db,
        )
    )
    service_class.assert_called_once_with(db)
    service_instance.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=1,
    )
    factory.create_client.assert_called_once_with(account)
    client.set_position_leverage.assert_awaited_once_with(
        symbol="BTCUSDT",
        buy_leverage=10.0,
        sell_leverage=10.0,
        category="linear",
        dry_run=True,
    )
    assert response["success"] is True
    assert response["message"] == (
        "Position leverage update processed successfully"
    )
    assert response["data"] == expected_result
@pytest.mark.asyncio
async def test_set_position_leverage_endpoint_live_request(
    monkeypatch,
):
    account = SimpleNamespace(id=1)
    client = SimpleNamespace(
        set_position_leverage=AsyncMock(
            return_value={
                "exchange": "BYBIT",
                "category": "inverse",
                "symbol": "BTCUSD",
                "buy_leverage": 5.0,
                "sell_leverage": 8.0,
                "dry_run": False,
                "accepted": True,
                "message": (
                    "Position leverage update accepted "
                    "by Bybit."
                ),
            }
        )
    )
    service_instance = Mock()
    service_instance.get_account.return_value = account
    monkeypatch.setattr(
        exchange_connections,
        "ExchangeAccountService",
        Mock(return_value=service_instance),
    )
    factory = Mock()
    factory.create_client.return_value = client
    monkeypatch.setattr(
        exchange_connections,
        "ExchangeFactory",
        factory,
    )
    data = SetPositionLeverageRequest(
        symbol="BTCUSD",
        buy_leverage=5,
        sell_leverage=8,
        category="inverse",
        dry_run=False,
    )
    response = await (
        exchange_connections
        .set_exchange_position_leverage(
            account_id=1,
            data=data,
            current_user=SimpleNamespace(id=7),
            db=Mock(),
        )
    )
    client.set_position_leverage.assert_awaited_once_with(
        symbol="BTCUSD",
        buy_leverage=5.0,
        sell_leverage=8.0,
        category="inverse",
        dry_run=False,
    )
    assert response["success"] is True
    assert response["data"]["accepted"] is True
@pytest.mark.asyncio
async def test_set_position_leverage_unsupported_exchange(
    monkeypatch,
):
    account = SimpleNamespace(id=1)
    unsupported_client = SimpleNamespace()
    service_instance = Mock()
    service_instance.get_account.return_value = account
    monkeypatch.setattr(
        exchange_connections,
        "ExchangeAccountService",
        Mock(return_value=service_instance),
    )
    factory = Mock()
    factory.create_client.return_value = unsupported_client
    monkeypatch.setattr(
        exchange_connections,
        "ExchangeFactory",
        factory,
    )
    data = SetPositionLeverageRequest(
        symbol="BTCUSDT",
        buy_leverage=10,
        sell_leverage=10,
    )
    with pytest.raises(HTTPException) as exc_info:
        await (
            exchange_connections
            .set_exchange_position_leverage(
                account_id=1,
                data=data,
                current_user=SimpleNamespace(id=7),
                db=Mock(),
            )
        )
    assert exc_info.value.status_code == 501
    assert exc_info.value.detail == (
        "Position leverage management is not "
        "supported for this exchange"
    )
