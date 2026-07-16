from unittest.mock import AsyncMock

import pytest

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


def test_normalize_order_status():
    assert BybitClient._normalize_order_status("New") == "NEW"

    assert (
        BybitClient._normalize_order_status("PartiallyFilled")
        == "PARTIALLY_FILLED"
    )

    assert BybitClient._normalize_order_status("Filled") == "FILLED"

    assert (
        BybitClient._normalize_order_status("Cancelled")
        == "CANCELLED"
    )

    assert (
        BybitClient._normalize_order_status("Rejected")
        == "REJECTED"
    )

    assert (
        BybitClient._normalize_order_status("Deactivated")
        == "EXPIRED"
    )

    assert (
        BybitClient._normalize_order_status("UnexpectedStatus")
        == "UNKNOWN"
    )


@pytest.mark.asyncio
async def test_get_order_by_id_normalizes_verified_order():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "orderId": "order-123",
                        "orderLinkId": "ptrader-123",
                        "symbol": "BTCUSDT",
                        "side": "Buy",
                        "orderType": "Limit",
                        "orderStatus": "PartiallyFilled",
                        "qty": "0.010",
                        "cumExecQty": "0.004",
                        "leavesQty": "0.006",
                        "price": "50000",
                        "avgPrice": "49990",
                        "cumExecValue": "199.96",
                        "cumExecFee": "0.12",
                        "reduceOnly": False,
                        "closeOnTrigger": False,
                        "createdTime": "1710000000000",
                        "updatedTime": "1710001000000",
                    }
                ],
            },
        }
    )

    result = await client.get_order_by_id(
        order_id="order-123",
        category="linear",
        symbol="btcusdt",
    )

    assert result is not None
    assert result["exchange"] == "BYBIT"
    assert result["order_id"] == "order-123"
    assert result["client_order_id"] == "ptrader-123"
    assert result["symbol"] == "BTCUSDT"
    assert result["side"] == "BUY"
    assert result["order_type"] == "LIMIT"
    assert result["status"] == "PARTIALLY_FILLED"

    assert result["quantity"] == 0.01
    assert result["filled_quantity"] == 0.004
    assert result["remaining_quantity"] == 0.006

    assert result["accepted"] is True
    assert result["verified"] is True
    assert result["dry_run"] is False

    client._private_get.assert_awaited_once_with(
        endpoint="/v5/order/realtime",
        params={
            "category": "linear",
            "orderId": "order-123",
            "openOnly": "0",
            "limit": "1",
            "symbol": "BTCUSDT",
        },
    )


@pytest.mark.asyncio
async def test_get_order_by_id_returns_none_when_not_found():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "list": [],
            },
        }
    )

    result = await client.get_order_by_id(
        order_id="missing-order",
        category="linear",
    )

    assert result is None


@pytest.mark.asyncio
async def test_market_order_returns_pending_when_not_yet_visible():
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
                "orderId": "market-pending-123",
                "orderLinkId": "ptrader-pending-market",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.place_market_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        category="linear",
        client_order_id="ptrader-pending-market",
        dry_run=False,
    )

    assert result["order_id"] == "market-pending-123"
    assert result["status"] == "PENDING"
    assert result["accepted"] is True
    assert result["verified"] is False
    assert result["dry_run"] is False

    client.get_order_by_id.assert_awaited_once_with(
        order_id="market-pending-123",
        category="linear",
        symbol="BTCUSDT",
    )


@pytest.mark.asyncio
async def test_limit_order_returns_pending_when_not_yet_visible():
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
                "orderId": "limit-pending-456",
                "orderLinkId": "ptrader-pending-limit",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.place_limit_order(
        symbol="BTCUSDT",
        side="SELL",
        quantity=0.001,
        price=50000.0,
        category="linear",
        client_order_id="ptrader-pending-limit",
        dry_run=False,
    )

    assert result["order_id"] == "limit-pending-456"
    assert result["status"] == "PENDING"
    assert result["accepted"] is True
    assert result["verified"] is False
    assert result["dry_run"] is False

    client.get_order_by_id.assert_awaited_once_with(
        order_id="limit-pending-456",
        category="linear",
        symbol="BTCUSDT",
    )