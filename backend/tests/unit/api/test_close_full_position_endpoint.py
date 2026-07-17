from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.v1.endpoints.exchange_connections import (
    close_full_exchange_position,
)
from app.schemas.exchange_trade import CloseFullPositionRequest


@pytest.mark.asyncio
async def test_close_full_endpoint_calls_exchange_client():
    current_user = Mock()
    current_user.id = 1

    account = Mock()
    account.id = 7
    account.exchange_name = "BYBIT"

    db = Mock()

    client = Mock()
    client.close_full_position = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "order_id": "",
            "client_order_id": "",
            "symbol": "BTCUSDT",
            "position_side": "LONG",
            "closing_side": "SELL",
            "position_index": 0,
            "requested_quantity": 0.01,
            "status": "PENDING",
            "reduce_only": True,
            "dry_run": True,
            "accepted": True,
            "verified": False,
            "message": "Dry-run position close validated",
        }
    )

    request = CloseFullPositionRequest(
        symbol="btcusdt",
        position_side="LONG",
        category="linear",
        settle_coin="usdt",
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
        service = service_class.return_value
        service.get_account.return_value = account

        response = await close_full_exchange_position(
            account_id=7,
            data=request,
            current_user=current_user,
            db=db,
        )

    service.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=7,
    )

    client.close_full_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        category="linear",
        settle_coin="USDT",
        position_side="LONG",
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )

    assert response["success"] is True
    assert (
        response["message"]
        == "Full position close processed successfully"
    )


@pytest.mark.asyncio
async def test_close_full_endpoint_allows_automatic_side():
    current_user = Mock()
    current_user.id = 1

    account = Mock()
    account.id = 7
    account.exchange_name = "BYBIT"

    db = Mock()

    client = Mock()
    client.close_full_position = AsyncMock(
        return_value={
            "symbol": "ETHUSDT",
            "position_side": "SHORT",
            "requested_quantity": 0.5,
        }
    )

    request = CloseFullPositionRequest(
        symbol="ethusdt",
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

        response = await close_full_exchange_position(
            account_id=7,
            data=request,
            current_user=current_user,
            db=db,
        )

    client.close_full_position.assert_awaited_once_with(
        symbol="ETHUSDT",
        category="linear",
        settle_coin="USDT",
        position_side=None,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )

    assert response["success"] is True