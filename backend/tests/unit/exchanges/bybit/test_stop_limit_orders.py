from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.exchanges.bybit.client import BybitClient


def valid_linear_rules() -> dict:
    return {
        "exchange": "BYBIT",
        "category": "linear",
        "symbol": "BTCUSDT",
        "status": "Trading",
        "base_coin": "BTC",
        "quote_coin": "USDT",
        "settle_coin": "USDT",
        "min_price": "0.1",
        "max_price": "1000000",
        "tick_size": "0.1",
        "min_order_quantity": "0.001",
        "max_limit_order_quantity": "100",
        "max_market_order_quantity": "50",
        "quantity_step": "0.001",
        "min_notional_value": "5",
    }


@pytest.mark.asyncio
async def test_stop_limit_dry_run_does_not_call_bybit():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock(
        return_value=valid_linear_rules()
    )
    client._private_post = AsyncMock()
    client.get_order_by_id = AsyncMock()

    result = await client.place_stop_limit_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        price=50100,
        trigger_price=50000,
        trigger_direction=1,
        trigger_by="MarkPrice",
        category="linear",
        time_in_force="GTC",
        client_order_id="ptrader-stop-limit-001",
        dry_run=True,
    )

    assert result["order_type"] == "STOP_LIMIT"
    assert result["status"] == "PENDING"
    assert result["dry_run"] is True
    assert result["accepted"] is False

    client._private_post.assert_not_awaited()
    client.get_order_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_stop_limit_live_mode_builds_correct_body():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock(
        return_value=valid_linear_rules()
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "orderId": "stop-limit-order-123",
                "orderLinkId": "ptrader-stop-limit-001",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.place_stop_limit_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        price=50100,
        trigger_price=50000,
        trigger_direction=1,
        trigger_by="MarkPrice",
        category="linear",
        time_in_force="GTC",
        reduce_only=False,
        close_on_trigger=False,
        position_index=0,
        client_order_id="ptrader-stop-limit-001",
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/order/create",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "orderType": "Limit",
            "qty": "0.001",
            "price": "50100",
            "triggerPrice": "50000",
            "triggerDirection": 1,
            "triggerBy": "MarkPrice",
            "timeInForce": "GTC",
            "reduceOnly": False,
            "closeOnTrigger": False,
            "positionIdx": 0,
            "orderLinkId": "ptrader-stop-limit-001",
        },
    )

    assert result["order_id"] == "stop-limit-order-123"
    assert result["status"] == "PENDING"
    assert result["accepted"] is True
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_stop_limit_rejects_invalid_trigger_direction():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.place_stop_limit_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.001,
            price=50100,
            trigger_price=50000,
            trigger_direction=3,
            dry_run=True,
        )

    assert "trigger_direction" in exc_info.value.detail
    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_stop_limit_rejects_invalid_trigger_type():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.place_stop_limit_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.001,
            price=50100,
            trigger_price=50000,
            trigger_direction=1,
            trigger_by="InvalidPrice",
            dry_run=True,
        )

    assert "trigger price type" in exc_info.value.detail
    client._private_post.assert_not_awaited()