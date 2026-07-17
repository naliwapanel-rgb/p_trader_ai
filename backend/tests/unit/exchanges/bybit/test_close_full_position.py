from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.exchanges.bybit.client import BybitClient


def make_client() -> BybitClient:
    return BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )


@pytest.mark.asyncio
async def test_close_full_long_detects_size_and_side():
    client = make_client()

    client.get_positions = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "settle_coin": "USDT",
            "count": 1,
            "positions": [
                {
                    "exchange": "BYBIT",
                    "category": "linear",
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 0.005,
                    "position_index": 0,
                }
            ],
        }
    )

    client.close_position = AsyncMock(
        return_value={
            "symbol": "BTCUSDT",
            "position_side": "LONG",
            "requested_quantity": 0.005,
            "dry_run": True,
        }
    )

    result = await client.close_full_position(
        symbol="btcusdt",
        category="linear",
        settle_coin="usdt",
        dry_run=True,
    )

    client.get_positions.assert_awaited_once_with(
        category="linear",
        settle_coin="USDT",
    )

    client.close_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        position_side="LONG",
        quantity=0.005,
        category="linear",
        position_index=0,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )

    assert result["position_side"] == "LONG"
    assert result["requested_quantity"] == 0.005


@pytest.mark.asyncio
async def test_close_full_short_uses_buy_close_foundation():
    client = make_client()

    client.get_positions = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "settle_coin": "USDT",
            "count": 1,
            "positions": [
                {
                    "symbol": "ETHUSDT",
                    "side": "SHORT",
                    "size": 0.25,
                    "position_index": 2,
                }
            ],
        }
    )

    client.close_position = AsyncMock(
        return_value={
            "symbol": "ETHUSDT",
            "position_side": "SHORT",
            "requested_quantity": 0.25,
        }
    )

    await client.close_full_position(
        symbol="ETHUSDT",
        position_side="SHORT",
        dry_run=False,
    )

    client.close_position.assert_awaited_once_with(
        symbol="ETHUSDT",
        position_side="SHORT",
        quantity=0.25,
        category="linear",
        position_index=2,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=False,
    )


@pytest.mark.asyncio
async def test_close_full_rejects_missing_position():
    client = make_client()

    client.get_positions = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "settle_coin": "USDT",
            "count": 0,
            "positions": [],
        }
    )

    client.close_position = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_full_position(
            symbol="BTCUSDT",
        )

    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "No active position found for BTCUSDT"
    )

    client.close_position.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_full_requires_side_when_hedged():
    client = make_client()

    client.get_positions = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "settle_coin": "USDT",
            "count": 2,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 0.01,
                    "position_index": 1,
                },
                {
                    "symbol": "BTCUSDT",
                    "side": "SHORT",
                    "size": 0.02,
                    "position_index": 2,
                },
            ],
        }
    )

    client.close_position = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_full_position(
            symbol="BTCUSDT",
        )

    assert exc_info.value.status_code == 409
    assert "Multiple active positions" in (
        exc_info.value.detail
    )

    client.close_position.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_full_selects_requested_hedge_side():
    client = make_client()

    client.get_positions = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "settle_coin": "USDT",
            "count": 2,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 0.01,
                    "position_index": 1,
                },
                {
                    "symbol": "BTCUSDT",
                    "side": "SHORT",
                    "size": 0.02,
                    "position_index": 2,
                },
            ],
        }
    )

    client.close_position = AsyncMock(
        return_value={
            "symbol": "BTCUSDT",
            "position_side": "SHORT",
            "requested_quantity": 0.02,
        }
    )

    await client.close_full_position(
        symbol="BTCUSDT",
        position_side="SHORT",
        dry_run=True,
    )

    client.close_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        position_side="SHORT",
        quantity=0.02,
        category="linear",
        position_index=2,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )


@pytest.mark.asyncio
async def test_close_full_rejects_invalid_requested_side():
    client = make_client()

    client.get_positions = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_full_position(
            symbol="BTCUSDT",
            position_side="BUY",
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == (
            "position_side must be LONG or SHORT "
            "when provided"
        )
    )

    client.get_positions.assert_not_awaited()