from unittest.mock import AsyncMock

import pytest

from app.exchanges.bybit.client import BybitClient


@pytest.mark.asyncio
async def test_get_positions_normalizes_bybit_response():
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
                "category": "linear",
                "nextPageCursor": "",
                "list": [
                    {
                        "positionIdx": 0,
                        "symbol": "BTCUSDT",
                        "side": "Buy",
                        "size": "0.01",
                        "positionValue": "650.00",
                        "avgPrice": "64000.00",
                        "breakEvenPrice": "64035.20",
                        "markPrice": "65000.00",
                        "liqPrice": "58000.00",
                        "leverage": "10",
                        "unrealisedPnl": "10.00",
                        "curRealisedPnl": "1.25",
                        "cumRealisedPnl": "15.75",
                        "takeProfit": "68000.00",
                        "stopLoss": "62000.00",
                        "trailingStop": "0",
                        "positionIM": "65.00",
                        "positionMM": "3.25",
                        "positionStatus": "Normal",
                        "autoAddMargin": 0,
                        "isReduceOnly": False,
                        "createdTime": "1710000000000",
                        "updatedTime": "1710001000000",
                    }
                ],
            },
        }
    )

    result = await client.get_positions()

    assert result["exchange"] == "BYBIT"
    assert result["category"] == "linear"
    assert result["settle_coin"] == "USDT"
    assert result["count"] == 1

    position = result["positions"][0]

    assert position["symbol"] == "BTCUSDT"
    assert position["side"] == "LONG"
    assert position["size"] == 0.01
    assert position["entry_price"] == 64000.00
    assert position["mark_price"] == 65000.00
    assert position["liquidation_price"] == 58000.00
    assert position["leverage"] == 10.0
    assert position["unrealized_pnl"] == 10.0
    assert position["take_profit"] == 68000.00
    assert position["stop_loss"] == 62000.00

    client._private_get.assert_awaited_once_with(
        endpoint="/v5/position/list",
        params={
            "category": "linear",
            "settleCoin": "USDT",
        },
    )


@pytest.mark.asyncio
async def test_get_positions_converts_sell_to_short():
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
                        "symbol": "ETHUSDT",
                        "side": "Sell",
                        "size": "2",
                    }
                ],
            },
        }
    )

    result = await client.get_positions()

    assert result["count"] == 1
    assert result["positions"][0]["side"] == "SHORT"


@pytest.mark.asyncio
async def test_get_positions_filters_zero_size_positions():
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
                        "symbol": "BTCUSDT",
                        "side": "",
                        "size": "0",
                    }
                ],
            },
        }
    )

    result = await client.get_positions()

    assert result["count"] == 0
    assert result["positions"] == []


@pytest.mark.asyncio
async def test_get_positions_handles_empty_list():
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

    result = await client.get_positions()

    assert result["exchange"] == "BYBIT"
    assert result["count"] == 0
    assert result["positions"] == []