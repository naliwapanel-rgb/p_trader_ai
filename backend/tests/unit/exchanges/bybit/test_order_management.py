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
async def test_cancel_order_dry_run_does_not_call_bybit():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    result = await client.cancel_order(
        symbol="btcusdt",
        order_id="order-123",
        dry_run=True,
    )

    assert result["action"] == "CANCEL"
    assert result["symbol"] == "BTCUSDT"
    assert result["order_id"] == "order-123"
    assert result["dry_run"] is True
    assert result["accepted"] is False

    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_order_live_mode_builds_correct_body():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "orderId": "order-123",
                "orderLinkId": "",
            },
        }
    )

    result = await client.cancel_order(
        symbol="btcusdt",
        order_id="order-123",
        category="linear",
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/order/cancel",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "orderId": "order-123",
        },
    )

    assert result["accepted"] is True
    assert result["dry_run"] is False


@pytest.mark.asyncio
async def test_cancel_order_requires_identifier():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.cancel_order(
            symbol="BTCUSDT",
            dry_run=True,
        )

    assert "Either order_id" in exc_info.value.detail
    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_amend_order_dry_run_validates_and_does_not_call_bybit():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock(
        return_value=valid_linear_rules()
    )
    client._private_post = AsyncMock()

    result = await client.amend_order(
        symbol="BTCUSDT",
        order_id="order-456",
        quantity=0.002,
        price=50000.0,
        dry_run=True,
    )

    assert result["action"] == "AMEND"
    assert result["dry_run"] is True
    assert result["accepted"] is False

    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_amend_order_live_mode_builds_correct_body():
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
                "orderId": "order-456",
                "orderLinkId": "ptrader-456",
            },
        }
    )

    result = await client.amend_order(
        symbol="btcusdt",
        order_id="order-456",
        client_order_id="ptrader-456",
        quantity=0.002,
        price=50000.0,
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/order/amend",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "orderId": "order-456",
            "orderLinkId": "ptrader-456",
            "qty": "0.002",
            "price": "50000.0",
        },
    )

    assert result["accepted"] is True
    assert result["dry_run"] is False


@pytest.mark.asyncio
async def test_amend_order_rejects_invalid_tick_size():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock(
        return_value=valid_linear_rules()
    )
    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.amend_order(
            symbol="BTCUSDT",
            order_id="order-456",
            price=50000.05,
            dry_run=True,
        )

    assert "tick size" in exc_info.value.detail
    client._private_post.assert_not_awaited()