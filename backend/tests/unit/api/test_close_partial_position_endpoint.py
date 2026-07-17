from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.exchange_connections import (
    close_partial_exchange_position,
)
from app.schemas.exchange_trade import ClosePartialPositionRequest


@pytest.mark.asyncio
async def test_close_partial_endpoint_calls_exchange_client():
    current_user = MagicMock()
    db = MagicMock()
    account = MagicMock()

    client = MagicMock()
    client.close_partial_position = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "symbol": "BTCUSDT",
            "position_side": "LONG",
            "requested_quantity": 0.1,
            "dry_run": True,
        }
    )

    request = ClosePartialPositionRequest(
        symbol="btcusdt",
        quantity=0.1,
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
        service_class.return_value.get_account.return_value = account

        response = await close_partial_exchange_position(
            account_id=1,
            data=request,
            current_user=current_user,
            db=db,
        )

    service_class.assert_called_once_with(db)

    service_class.return_value.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=1,
    )

    client.close_partial_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        quantity=0.1,
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
        == "Partial position close processed successfully"
    )
    assert response["data"]["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_close_partial_endpoint_allows_automatic_side():
    current_user = MagicMock()
    db = MagicMock()
    account = MagicMock()

    client = MagicMock()
    client.close_partial_position = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "symbol": "ETHUSDT",
            "position_side": "SHORT",
            "requested_quantity": 0.5,
            "dry_run": True,
        }
    )

    request = ClosePartialPositionRequest(
        symbol="ethusdt",
        quantity=0.5,
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
        service_class.return_value.get_account.return_value = account

        response = await close_partial_exchange_position(
            account_id=7,
            data=request,
            current_user=current_user,
            db=db,
        )

    client.close_partial_position.assert_awaited_once_with(
        symbol="ETHUSDT",
        quantity=0.5,
        category="linear",
        settle_coin="USDT",
        position_side=None,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )

    assert response["success"] is True


@pytest.mark.asyncio
async def test_close_partial_endpoint_rejects_unsupported_exchange():
    current_user = MagicMock()
    db = MagicMock()
    account = MagicMock()

    client = MagicMock(spec=[])

    request = ClosePartialPositionRequest(
        symbol="BTCUSDT",
        quantity=0.1,
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
        service_class.return_value.get_account.return_value = account

        with pytest.raises(HTTPException) as exc_info:
            await close_partial_exchange_position(
                account_id=1,
                data=request,
                current_user=current_user,
                db=db,
            )

    assert exc_info.value.status_code == 501
    assert (
        exc_info.value.detail
        == "Partial position close is not supported for this exchange"
    )