from unittest.mock import AsyncMock

import pytest

from app.exchanges.bybit.client import BybitClient


@pytest.mark.asyncio
async def test_get_open_orders_normalizes_bybit_response():
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
                "nextPageCursor": "",
                "list": [
                    {
                        "orderId": "order-123",
                        "orderLinkId": "ptrader-001",
                        "symbol": "BTCUSDT",
                        "side": "Buy",
                        "orderType": "Limit",
                        "orderStatus": "New",
                        "price": "60000",
                        "avgPrice": "",
                        "qty": "0.01",
                        "cumExecQty": "0",
                        "leavesQty": "0.01",
                        "leavesValue": "600",
                        "cumExecValue": "0",
                        "cumExecFee": "0",
                        "timeInForce": "GTC",
                        "positionIdx": 0,
                        "reduceOnly": False,
                        "closeOnTrigger": False,
                        "triggerPrice": "",
                        "triggerDirection": 0,
                        "triggerBy": "",
                        "takeProfit": "65000",
                        "stopLoss": "58000",
                        "orderFilter": "Order",
                        "rejectReason": "EC_NoError",
                        "cancelType": "UNKNOWN",
                        "createdTime": "1710000000000",
                        "updatedTime": "1710001000000",
                    }
                ],
            },
        }
    )

    result = await client.get_open_orders()

    assert result["exchange"] == "BYBIT"
    assert result["category"] == "linear"
    assert result["settle_coin"] == "USDT"
    assert result["count"] == 1

    order = result["orders"][0]

    assert order["order_id"] == "order-123"
    assert order["client_order_id"] == "ptrader-001"
    assert order["symbol"] == "BTCUSDT"
    assert order["side"] == "BUY"
    assert order["order_type"] == "LIMIT"
    assert order["status"] == "NEW"

    assert order["price"] == 60000.0
    assert order["quantity"] == 0.01
    assert order["filled_quantity"] == 0.0
    assert order["remaining_quantity"] == 0.01

    assert order["take_profit"] == 65000.0
    assert order["stop_loss"] == 58000.0

    client._private_get.assert_awaited_once_with(
        endpoint="/v5/order/realtime",
        params={
            "category": "linear",
            "openOnly": "0",
            "limit": "50",
            "settleCoin": "USDT",
        },
    )


@pytest.mark.asyncio
async def test_get_open_orders_normalizes_sell_side():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "list": [
                    {
                        "orderId": "order-456",
                        "symbol": "ETHUSDT",
                        "side": "Sell",
                        "orderType": "Market",
                        "orderStatus": "PartiallyFilled",
                        "qty": "2",
                        "cumExecQty": "0.5",
                        "leavesQty": "1.5",
                    }
                ],
            },
        }
    )

    result = await client.get_open_orders()

    assert result["count"] == 1

    order = result["orders"][0]

    assert order["side"] == "SELL"
    assert order["order_type"] == "MARKET"
    assert order["status"] == "PARTIALLYFILLED"
    assert order["filled_quantity"] == 0.5
    assert order["remaining_quantity"] == 1.5


@pytest.mark.asyncio
async def test_get_open_orders_uses_symbol_when_provided():
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

    result = await client.get_open_orders(
        category="linear",
        settle_coin="USDT",
        symbol="btcusdt",
    )

    assert result["count"] == 0

    client._private_get.assert_awaited_once_with(
        endpoint="/v5/order/realtime",
        params={
            "category": "linear",
            "openOnly": "0",
            "limit": "50",
            "symbol": "BTCUSDT",
        },
    )


@pytest.mark.asyncio
async def test_get_open_orders_handles_empty_list():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "nextPageCursor": "",
                "list": [],
            },
        }
    )

    result = await client.get_open_orders()

    assert result["exchange"] == "BYBIT"
    assert result["count"] == 0
    assert result["orders"] == []