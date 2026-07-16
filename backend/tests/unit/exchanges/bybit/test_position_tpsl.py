from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.exchanges.bybit.client import BybitClient


@pytest.mark.asyncio
async def test_position_tpsl_dry_run_does_not_call_bybit():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    result = await client.set_position_tpsl(
        symbol="btcusdt",
        category="linear",
        position_index=0,
        take_profit=60000,
        stop_loss=45000,
        tp_trigger_by="MarkPrice",
        sl_trigger_by="MarkPrice",
        tpsl_mode="Full",
        dry_run=True,
    )

    assert result["exchange"] == "BYBIT"
    assert result["symbol"] == "BTCUSDT"
    assert result["action"] == "SET_POSITION_TPSL"
    assert result["dry_run"] is True
    assert result["accepted"] is False

    client._private_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_position_tpsl_live_builds_correct_full_body():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {},
        }
    )

    result = await client.set_position_tpsl(
        symbol="BTCUSDT",
        category="linear",
        position_index=0,
        take_profit=60000,
        stop_loss=45000,
        tp_trigger_by="MarkPrice",
        sl_trigger_by="IndexPrice",
        tpsl_mode="Full",
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/position/trading-stop",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "tpslMode": "Full",
            "positionIdx": 0,
            "takeProfit": "60000",
            "tpTriggerBy": "MarkPrice",
            "tpOrderType": "Market",
            "stopLoss": "45000",
            "slTriggerBy": "IndexPrice",
            "slOrderType": "Market",
        },
    )

    assert result["accepted"] is True
    assert result["dry_run"] is False


@pytest.mark.asyncio
async def test_position_partial_limit_tpsl_builds_body():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {},
        }
    )

    result = await client.set_position_tpsl(
        symbol="BTCUSDT",
        category="linear",
        position_index=0,
        take_profit=60000,
        stop_loss=45000,
        tp_trigger_by="MarkPrice",
        sl_trigger_by="MarkPrice",
        tpsl_mode="Partial",
        tp_order_type="Limit",
        sl_order_type="Limit",
        tp_size=0.001,
        sl_size=0.001,
        tp_limit_price=59900,
        sl_limit_price=44900,
        dry_run=False,
    )

    body = client._private_post.await_args.kwargs[
        "body"
    ]

    assert body["tpslMode"] == "Partial"
    assert body["tpSize"] == "0.001"
    assert body["slSize"] == "0.001"
    assert body["tpOrderType"] == "Limit"
    assert body["slOrderType"] == "Limit"
    assert body["tpLimitPrice"] == "59900"
    assert body["slLimitPrice"] == "44900"

    assert result["accepted"] is True


@pytest.mark.asyncio
async def test_position_partial_rejects_unequal_sizes():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_post = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.set_position_tpsl(
            symbol="BTCUSDT",
            take_profit=60000,
            stop_loss=45000,
            tpsl_mode="Partial",
            tp_size=0.001,
            sl_size=0.002,
            dry_run=True,
        )

    assert "must be equal" in exc_info.value.detail
    client._private_post.assert_not_awaited()