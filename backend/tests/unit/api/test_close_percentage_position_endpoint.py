from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from app.api.v1.endpoints.exchange_connections import (
    close_percentage_exchange_position,
)
from app.schemas.exchange_trade import (
    ClosePercentagePositionRequest,
)
@pytest.mark.asyncio
async def test_close_percentage_endpoint_calls_exchange_client():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=4,
        exchange_name="BYBIT",
    )
    db = MagicMock()
    expected_result = {
        "exchange": "BYBIT",
        "symbol": "BTCUSDT",
        "requested_percentage": 25.0,
        "requested_quantity": 0.25,
        "accepted": True,
        "dry_run": True,
    }
    client = MagicMock()
    client.close_percentage_position = AsyncMock(
        return_value=expected_result
    )
    data = ClosePercentagePositionRequest(
        symbol="btcusdt",
        percentage=25,
        category="linear",
        settle_coin="usdt",
        position_side="LONG",
        time_in_force="IOC",
        client_order_id="percentage-close-1",
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
        response = await close_percentage_exchange_position(
            account_id=4,
            data=data,
            current_user=current_user,
            db=db,
        )
    service_class.return_value.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=4,
    )
    client.close_percentage_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        percentage=25.0,
        category="linear",
        settle_coin="USDT",
        position_side="LONG",
        time_in_force="IOC",
        client_order_id="percentage-close-1",
        dry_run=True,
    )
    assert response["success"] is True
    assert (
        response["message"]
        == "Percentage position close processed successfully"
    )
    assert response["data"] == expected_result
@pytest.mark.asyncio
async def test_close_percentage_endpoint_allows_automatic_side():
    current_user = SimpleNamespace(id=1)
    account = SimpleNamespace(
        id=4,
        exchange_name="BYBIT",
    )
    db = MagicMock()
    client = MagicMock()
    client.close_percentage_position = AsyncMock(
        return_value={
            "accepted": True,
            "requested_percentage": 50.0,
        }
    )
    data = ClosePercentagePositionRequest(
        symbol="ethusdt",
        percentage=50,
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
        await close_percentage_exchange_position(
            account_id=4,
            data=data,
            current_user=current_user,
            db=db,
        )
    client.close_percentage_position.assert_awaited_once_with(
        symbol="ETHUSDT",
        percentage=50.0,
        category="linear",
        settle_coin="USDT",
        position_side=None,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )
@pytest.mark.asyncio
async def test_close_percentage_endpoint_rejects_unsupported_exchange():
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
    data = ClosePercentagePositionRequest(
        symbol="BTCUSDT",
        percentage=25,
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
            await close_percentage_exchange_position(
                account_id=9,
                data=data,
                current_user=current_user,
                db=db,
            )
    assert error.value.status_code == 501
    assert (
        error.value.detail
        == (
            "Percentage position close is not "
            "supported for this exchange"
        )
    )
@pytest.mark.parametrize(
    "percentage",
    [
        0,
        -1,
        100.01,
        150,
    ],
)
def test_close_percentage_request_rejects_invalid_percentage(
    percentage,
):
    with pytest.raises(ValueError):
        ClosePercentagePositionRequest(
            symbol="BTCUSDT",
            percentage=percentage,
        )
