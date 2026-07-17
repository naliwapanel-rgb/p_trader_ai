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
async def test_close_long_dry_run_uses_sell_reduce_only():
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

    result = await client.close_position(
        symbol="btcusdt",
        position_side="LONG",
        quantity=0.001,
        category="linear",
        position_index=0,
        client_order_id="close-long-001",
        dry_run=True,
    )

    assert result["symbol"] == "BTCUSDT"
    assert result["position_side"] == "LONG"
    assert result["closing_side"] == "SELL"
    assert result["reduce_only"] is True
    assert result["dry_run"] is True
    assert result["accepted"] is False

    client._private_post.assert_not_awaited()
    client.get_order_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_short_live_builds_buy_reduce_only_body():
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
                "orderId": "close-short-123",
                "orderLinkId": "close-short-001",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.close_position(
        symbol="BTCUSDT",
        position_side="SHORT",
        quantity=0.001,
        category="linear",
        position_index=2,
        time_in_force="IOC",
        client_order_id="close-short-001",
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/order/create",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "orderType": "Market",
            "qty": "0.001",
            "timeInForce": "IOC",
            "reduceOnly": True,
            "closeOnTrigger": False,
            "positionIdx": 2,
            "orderLinkId": "close-short-001",
        },
    )

    assert result["order_id"] == "close-short-123"
    assert result["closing_side"] == "BUY"
    assert result["status"] == "PENDING"
    assert result["accepted"] is True
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_close_position_rejects_invalid_side():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock()
    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_position(
            symbol="BTCUSDT",
            position_side="INVALID",
            quantity=0.001,
            dry_run=True,
        )

    assert "LONG or SHORT" in exc_info.value.detail
    client.get_instrument_rules.assert_not_awaited()
    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_long_rejects_short_hedge_index():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock()
    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_position(
            symbol="BTCUSDT",
            position_side="LONG",
            quantity=0.001,
            position_index=2,
            dry_run=True,
        )

    assert "cannot use position_index 2" in exc_info.value.detail
    client.get_instrument_rules.assert_not_awaited()
    client._private_post.assert_not_awaited()