from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from app.exchanges.bybit.client import BybitClient
def make_client() -> BybitClient:
    return BybitClient(
        api_key="test-key",
        api_secret="test-secret",
        is_testnet=True,
    )
def long_position() -> dict:
    return {
        "exchange": "BYBIT",
        "category": "linear",
        "settle_coin": "USDT",
        "count": 1,
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "size": 1.0,
                "position_index": 0,
            }
        ],
    }
@pytest.mark.asyncio
async def test_set_position_tp_sl_dry_run():
    client = make_client()
    client.get_positions = AsyncMock(
        return_value=long_position()
    )
    client._private_post = AsyncMock()
    result = await client.set_position_tp_sl(
        symbol="btcusdt",
        take_profit=72000,
        stop_loss=65000,
        category="linear",
        settle_coin="usdt",
        dry_run=True,
    )
    client._private_post.assert_not_awaited()
    assert result["exchange"] == "BYBIT"
    assert result["symbol"] == "BTCUSDT"
    assert result["position_side"] == "LONG"
    assert result["position_index"] == 0
    assert result["take_profit"] == 72000.0
    assert result["stop_loss"] == 65000.0
    assert result["dry_run"] is True
    assert result["accepted"] is False
@pytest.mark.asyncio
async def test_set_position_tp_sl_live_builds_correct_body():
    client = make_client()
    client.get_positions = AsyncMock(
        return_value=long_position()
    )
    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {},
        }
    )
    result = await client.set_position_tp_sl(
        symbol="BTCUSDT",
        take_profit=72000,
        stop_loss=65000,
        category="linear",
        settle_coin="USDT",
        position_side="LONG",
        tp_trigger_by="LastPrice",
        sl_trigger_by="MarkPrice",
        dry_run=False,
    )
    client._private_post.assert_awaited_once_with(
        endpoint="/v5/position/trading-stop",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "tpslMode": "Full",
            "positionIdx": 0,
            "takeProfit": "72000",
            "tpTriggerBy": "LastPrice",
            "stopLoss": "65000",
            "slTriggerBy": "MarkPrice",
        },
    )
    assert result["accepted"] is True
    assert result["dry_run"] is False
@pytest.mark.asyncio
async def test_set_position_tp_only():
    client = make_client()
    client.get_positions = AsyncMock(
        return_value=long_position()
    )
    client._private_post = AsyncMock()
    result = await client.set_position_tp_sl(
        symbol="BTCUSDT",
        take_profit=72000,
        dry_run=True,
    )
    assert result["take_profit"] == 72000.0
    assert result["stop_loss"] is None
@pytest.mark.asyncio
async def test_set_position_sl_only():
    client = make_client()
    client.get_positions = AsyncMock(
        return_value=long_position()
    )
    client._private_post = AsyncMock()
    result = await client.set_position_tp_sl(
        symbol="BTCUSDT",
        stop_loss=65000,
        dry_run=True,
    )
    assert result["take_profit"] is None
    assert result["stop_loss"] == 65000.0
@pytest.mark.asyncio
async def test_set_position_tp_sl_requires_value():
    client = make_client()
    with pytest.raises(HTTPException) as error:
        await client.set_position_tp_sl(
            symbol="BTCUSDT",
        )
    assert error.value.status_code == 400
    assert (
        error.value.detail
        == (
            "At least one of take_profit or stop_loss "
            "must be provided"
        )
    )
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "take_profit, stop_loss",
    [
        (0, None),
        (-1, None),
        (None, 0),
        (None, -1),
    ],
)
async def test_set_position_tp_sl_rejects_non_positive_prices(
    take_profit,
    stop_loss,
):
    client = make_client()
    with pytest.raises(HTTPException) as error:
        await client.set_position_tp_sl(
            symbol="BTCUSDT",
            take_profit=take_profit,
            stop_loss=stop_loss,
        )
    assert error.value.status_code == 400
@pytest.mark.asyncio
async def test_set_position_tp_sl_rejects_missing_position():
    client = make_client()
    client.get_positions = AsyncMock(
        return_value={
            "positions": [],
        }
    )
    with pytest.raises(HTTPException) as error:
        await client.set_position_tp_sl(
            symbol="BTCUSDT",
            take_profit=72000,
        )
    assert error.value.status_code == 404
    assert (
        error.value.detail
        == "No active position found for BTCUSDT"
    )
@pytest.mark.asyncio
async def test_set_position_tp_sl_requires_side_when_hedged():
    client = make_client()
    client.get_positions = AsyncMock(
        return_value={
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 1,
                    "position_index": 1,
                },
                {
                    "symbol": "BTCUSDT",
                    "side": "SHORT",
                    "size": 1,
                    "position_index": 2,
                },
            ]
        }
    )
    with pytest.raises(HTTPException) as error:
        await client.set_position_tp_sl(
            symbol="BTCUSDT",
            take_profit=72000,
        )
    assert error.value.status_code == 409
@pytest.mark.asyncio
async def test_set_position_tp_sl_selects_requested_hedge_side():
    client = make_client()
    client.get_positions = AsyncMock(
        return_value={
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 1,
                    "position_index": 1,
                },
                {
                    "symbol": "BTCUSDT",
                    "side": "SHORT",
                    "size": 1,
                    "position_index": 2,
                },
            ]
        }
    )
    client._private_post = AsyncMock()
    result = await client.set_position_tp_sl(
        symbol="BTCUSDT",
        stop_loss=73000,
        position_side="SHORT",
        dry_run=True,
    )
    assert result["position_side"] == "SHORT"
    assert result["position_index"] == 2
