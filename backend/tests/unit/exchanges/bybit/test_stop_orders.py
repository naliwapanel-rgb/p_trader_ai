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
async def test_stop_market_dry_run_does_not_call_bybit():
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

    result = await client.place_stop_market_order(
        symbol="btcusdt",
        side="SELL",
        quantity=0.001,
        trigger_price=50000,
        trigger_direction=2,
        trigger_by="MarkPrice",
        category="linear",
        reduce_only=True,
        close_on_trigger=True,
        client_order_id="ptrader-stop-001",
        dry_run=True,
    )

    assert result["order_type"] == "STOP_MARKET"
    assert result["status"] == "PENDING"
    assert result["dry_run"] is True
    assert result["accepted"] is False

    client._private_post.assert_not_awaited()
    client.get_order_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_stop_market_live_mode_builds_correct_body():
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
                "orderId": "stop-order-123",
                "orderLinkId": "ptrader-stop-001",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.place_stop_market_order(
        symbol="BTCUSDT",
        side="SELL",
        quantity=0.001,
        trigger_price=50000,
        trigger_direction=2,
        trigger_by="MarkPrice",
        category="linear",
        reduce_only=True,
        close_on_trigger=True,
        position_index=0,
        client_order_id="ptrader-stop-001",
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/order/create",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "side": "Sell",
            "orderType": "Market",
            "qty": "0.001",
            "triggerPrice": "50000",
            "triggerDirection": 2,
            "triggerBy": "MarkPrice",
            "reduceOnly": True,
            "closeOnTrigger": True,
            "positionIdx": 0,
            "orderLinkId": "ptrader-stop-001",
        },
    )

    assert result["order_id"] == "stop-order-123"
    assert result["status"] == "PENDING"
    assert result["accepted"] is True
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_stop_market_rejects_invalid_direction():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.place_stop_market_order(
            symbol="BTCUSDT",
            side="SELL",
            quantity=0.001,
            trigger_price=50000,
            trigger_direction=3,
            dry_run=True,
        )

    assert "trigger_direction" in exc_info.value.detail
    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_stop_market_rejects_invalid_trigger_type():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.place_stop_market_order(
            symbol="BTCUSDT",
            side="SELL",
            quantity=0.001,
            trigger_price=50000,
            trigger_direction=2,
            trigger_by="InvalidPrice",
            dry_run=True,
        )

    assert "trigger price type" in exc_info.value.detail
    client._private_post.assert_not_awaited()