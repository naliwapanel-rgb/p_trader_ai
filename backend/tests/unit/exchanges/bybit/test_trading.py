from unittest.mock import AsyncMock

import pytest

from app.exchanges.bybit.client import BybitClient


@pytest.mark.asyncio
async def test_market_order_dry_run_does_not_call_bybit():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    result = await client.place_market_order(
        symbol="btcusdt",
        side="BUY",
        quantity=0.001,
        category="linear",
        dry_run=True,
    )

    assert result["exchange"] == "BYBIT"
    assert result["category"] == "linear"
    assert result["symbol"] == "BTCUSDT"
    assert result["side"] == "BUY"
    assert result["order_type"] == "MARKET"
    assert result["quantity"] == 0.001
    assert result["dry_run"] is True
    assert result["accepted"] is False
    assert result["order_id"] == ""

    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_limit_order_dry_run_does_not_call_bybit():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    result = await client.place_limit_order(
        symbol="ethusdt",
        side="SELL",
        quantity=0.01,
        price=5000.0,
        category="linear",
        time_in_force="GTC",
        client_order_id="ptrader-test-001",
        dry_run=True,
    )

    assert result["exchange"] == "BYBIT"
    assert result["symbol"] == "ETHUSDT"
    assert result["side"] == "SELL"
    assert result["order_type"] == "LIMIT"
    assert result["quantity"] == 0.01
    assert result["price"] == 5000.0
    assert result["client_order_id"] == "ptrader-test-001"
    assert result["dry_run"] is True
    assert result["accepted"] is False

    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_market_order_live_mode_builds_correct_bybit_body():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "orderId": "bybit-order-123",
                "orderLinkId": "ptrader-market-001",
            },
        }
    )

    result = await client.place_market_order(
        symbol="btcusdt",
        side="BUY",
        quantity=0.001,
        category="linear",
        time_in_force="IOC",
        client_order_id="ptrader-market-001",
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
            "reduceOnly": False,
            "closeOnTrigger": False,
            "orderLinkId": "ptrader-market-001",
        },
    )

    assert result["order_id"] == "bybit-order-123"
    assert result["accepted"] is True
    assert result["dry_run"] is False


@pytest.mark.asyncio
async def test_limit_order_live_mode_builds_correct_bybit_body():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "orderId": "bybit-order-456",
                "orderLinkId": "ptrader-limit-001",
            },
        }
    )

    result = await client.place_limit_order(
        symbol="ethusdt",
        side="SELL",
        quantity=0.01,
        price=5000.0,
        category="linear",
        time_in_force="GTC",
        reduce_only=True,
        client_order_id="ptrader-limit-001",
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/order/create",
        body={
            "category": "linear",
            "symbol": "ETHUSDT",
            "side": "Sell",
            "orderType": "Limit",
            "qty": "0.01",
            "price": "5000.0",
            "timeInForce": "GTC",
            "reduceOnly": True,
            "closeOnTrigger": False,
            "orderLinkId": "ptrader-limit-001",
        },
    )

    assert result["order_id"] == "bybit-order-456"
    assert result["accepted"] is True
    assert result["dry_run"] is False