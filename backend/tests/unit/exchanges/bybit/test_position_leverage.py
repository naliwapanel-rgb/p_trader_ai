from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from app.exchanges.bybit.client import BybitClient
@pytest.fixture
def client() -> BybitClient:
    return BybitClient(
        api_key="test-key",
        api_secret="test-secret",
        is_testnet=True,
    )
@pytest.mark.asyncio
async def test_get_position_leverage_normalizes_one_way_position(
    client: BybitClient,
):
    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "side": "Buy",
                        "size": "0.010",
                        "positionIdx": 0,
                        "tradeMode": 0,
                        "leverage": "10",
                    }
                ]
            },
        }
    )
    result = await client.get_position_leverage(
        symbol="btcusdt",
        category="LINEAR",
    )
    client._private_get.assert_awaited_once_with(
        endpoint="/v5/position/list",
        params={
            "category": "linear",
            "symbol": "BTCUSDT",
        },
    )
    assert result == {
        "exchange": "BYBIT",
        "symbol": "BTCUSDT",
        "category": "linear",
        "positions": [
            {
                "symbol": "BTCUSDT",
                "category": "linear",
                "position_side": "LONG",
                "position_index": 0,
                "position_mode": "ONE_WAY",
                "leverage": 10.0,
                "portfolio_margin": False,
                "trade_mode": 0,
                "position_size": 0.01,
            }
        ],
    }
@pytest.mark.asyncio
async def test_get_position_leverage_supports_hedge_mode(
    client: BybitClient,
):
    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "symbol": "ETHUSDT",
                        "side": "Buy",
                        "size": "1",
                        "positionIdx": 1,
                        "tradeMode": 0,
                        "leverage": "5",
                    },
                    {
                        "symbol": "ETHUSDT",
                        "side": "Sell",
                        "size": "2",
                        "positionIdx": 2,
                        "tradeMode": 0,
                        "leverage": "8",
                    },
                ]
            },
        }
    )
    result = await client.get_position_leverage(
        symbol="ETHUSDT",
    )
    assert len(result["positions"]) == 2
    assert result["positions"][0]["position_side"] == "LONG"
    assert result["positions"][0]["position_index"] == 1
    assert result["positions"][0]["position_mode"] == "HEDGE"
    assert result["positions"][0]["leverage"] == 5.0
    assert result["positions"][1]["position_side"] == "SHORT"
    assert result["positions"][1]["position_index"] == 2
    assert result["positions"][1]["position_mode"] == "HEDGE"
    assert result["positions"][1]["leverage"] == 8.0
@pytest.mark.asyncio
async def test_get_position_leverage_handles_portfolio_margin(
    client: BybitClient,
):
    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "side": "",
                        "size": "0",
                        "positionIdx": 0,
                        "tradeMode": 0,
                        "leverage": "",
                    }
                ]
            },
        }
    )
    result = await client.get_position_leverage(
        symbol="BTCUSDT",
    )
    position = result["positions"][0]
    assert position["leverage"] is None
    assert position["portfolio_margin"] is True
    assert position["position_side"] is None
@pytest.mark.asyncio
async def test_get_position_leverage_handles_empty_result(
    client: BybitClient,
):
    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [],
            },
        }
    )
    result = await client.get_position_leverage(
        symbol="BTCUSDT",
    )
    assert result == {
        "exchange": "BYBIT",
        "symbol": "BTCUSDT",
        "category": "linear",
        "positions": [],
    }
@pytest.mark.asyncio
async def test_get_position_leverage_rejects_empty_symbol(
    client: BybitClient,
):
    with pytest.raises(HTTPException) as exc_info:
        await client.get_position_leverage(symbol=" ")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "symbol is required"
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category",
    [
        "spot",
        "option",
        "",
    ],
)
async def test_get_position_leverage_rejects_invalid_category(
    client: BybitClient,
    category: str,
):
    with pytest.raises(HTTPException) as exc_info:
        await client.get_position_leverage(
            symbol="BTCUSDT",
            category=category,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "category must be linear or inverse"
    )
