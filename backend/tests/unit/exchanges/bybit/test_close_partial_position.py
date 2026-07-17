from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.exchanges.bybit.client import BybitClient


def make_client() -> BybitClient:
    client = object.__new__(BybitClient)
    client.get_positions = AsyncMock()
    client.close_position = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "symbol": "BTCUSDT",
            "accepted": False,
            "dry_run": True,
        }
    )
    return client


@pytest.mark.asyncio
async def test_partial_close_long_delegates_requested_quantity():
    client = make_client()

    client.get_positions.return_value = {
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "size": 0.5,
                "position_index": 0,
            }
        ]
    }

    result = await client.close_partial_position(
        symbol="btcusdt",
        quantity=0.1,
        position_side="long",
        dry_run=True,
    )

    client.close_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        position_side="LONG",
        quantity=0.1,
        category="linear",
        position_index=0,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )

    assert result["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_partial_close_short_uses_detected_side_and_index():
    client = make_client()

    client.get_positions.return_value = {
        "positions": [
            {
                "symbol": "ETHUSDT",
                "side": "SHORT",
                "size": 2.0,
                "position_index": 2,
            }
        ]
    }

    await client.close_partial_position(
        symbol="ethusdt",
        quantity=0.5,
        position_side="SHORT",
        dry_run=True,
    )

    client.close_position.assert_awaited_once_with(
        symbol="ETHUSDT",
        position_side="SHORT",
        quantity=0.5,
        category="linear",
        position_index=2,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )


@pytest.mark.asyncio
async def test_partial_close_allows_quantity_equal_to_position():
    client = make_client()

    client.get_positions.return_value = {
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "size": 0.5,
                "position_index": 0,
            }
        ]
    }

    await client.close_partial_position(
        symbol="BTCUSDT",
        quantity=0.5,
        dry_run=True,
    )

    client.close_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        position_side="LONG",
        quantity=0.5,
        category="linear",
        position_index=0,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )


@pytest.mark.asyncio
async def test_partial_close_rejects_quantity_above_position():
    client = make_client()

    client.get_positions.return_value = {
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "size": 0.5,
                "position_index": 0,
            }
        ]
    }

    with pytest.raises(HTTPException) as exc_info:
        await client.close_partial_position(
            symbol="BTCUSDT",
            quantity=0.6,
            dry_run=True,
        )

    assert exc_info.value.status_code == 400
    assert (
        "exceeds active position size"
        in exc_info.value.detail
    )

    client.close_position.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_close_rejects_zero_quantity():
    client = make_client()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_partial_position(
            symbol="BTCUSDT",
            quantity=0,
            dry_run=True,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Partial close quantity must be greater than zero"
    )

    client.get_positions.assert_not_awaited()
    client.close_position.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_close_rejects_negative_quantity():
    client = make_client()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_partial_position(
            symbol="BTCUSDT",
            quantity=-0.1,
            dry_run=True,
        )

    assert exc_info.value.status_code == 400
    client.get_positions.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_close_rejects_missing_position():
    client = make_client()

    client.get_positions.return_value = {
        "positions": []
    }

    with pytest.raises(HTTPException) as exc_info:
        await client.close_partial_position(
            symbol="BTCUSDT",
            quantity=0.1,
            position_side="LONG",
            dry_run=True,
        )

    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "No active position found for BTCUSDT with side LONG"
    )

    client.close_position.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_close_requires_side_for_hedged_positions():
    client = make_client()

    client.get_positions.return_value = {
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "size": 0.5,
                "position_index": 1,
            },
            {
                "symbol": "BTCUSDT",
                "side": "SHORT",
                "size": 0.3,
                "position_index": 2,
            },
        ]
    }

    with pytest.raises(HTTPException) as exc_info:
        await client.close_partial_position(
            symbol="BTCUSDT",
            quantity=0.1,
            dry_run=True,
        )

    assert exc_info.value.status_code == 409
    assert "Provide position_side" in exc_info.value.detail

    client.close_position.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_close_selects_requested_hedge_side():
    client = make_client()

    client.get_positions.return_value = {
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "size": 0.5,
                "position_index": 1,
            },
            {
                "symbol": "BTCUSDT",
                "side": "SHORT",
                "size": 0.3,
                "position_index": 2,
            },
        ]
    }

    await client.close_partial_position(
        symbol="BTCUSDT",
        quantity=0.1,
        position_side="SHORT",
        dry_run=True,
    )

    client.close_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        position_side="SHORT",
        quantity=0.1,
        category="linear",
        position_index=2,
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )


@pytest.mark.asyncio
async def test_partial_close_rejects_invalid_side():
    client = make_client()

    with pytest.raises(HTTPException) as exc_info:
        await client.close_partial_position(
            symbol="BTCUSDT",
            quantity=0.1,
            position_side="BUY",
            dry_run=True,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "position_side must be LONG or SHORT when provided"
    )

    client.get_positions.assert_not_awaited()