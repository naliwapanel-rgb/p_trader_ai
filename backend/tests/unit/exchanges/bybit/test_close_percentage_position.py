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
async def test_percentage_close_calculates_25_percent(
    client: BybitClient,
):
    client.get_positions = AsyncMock(
        return_value={
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 0.040,
                    "position_index": 0,
                }
            ]
        }
    )
    client.get_instrument_rules = AsyncMock(
        return_value={
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
            "max_market_order_quantity": "100",
            "quantity_step": "0.001",
            "min_notional_value": "5",
        }
    )
    client.close_partial_position = AsyncMock(
        return_value={
            "symbol": "BTCUSDT",
            "dry_run": True,
        }
    )
    result = await client.close_percentage_position(
        symbol="BTCUSDT",
        percentage=25,
    )
    client.close_partial_position.assert_awaited_once_with(
        symbol="BTCUSDT",
        quantity=0.01,
        category="linear",
        settle_coin="USDT",
        position_side="LONG",
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )
    assert result["requested_percentage"] == 25.0
    assert result["position_quantity"] == 0.04
    assert result["calculated_close_quantity"] == 0.01
@pytest.mark.asyncio
async def test_percentage_close_rounds_down_to_step(
    client: BybitClient,
):
    client.get_positions = AsyncMock(
        return_value={
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 0.015,
                    "position_index": 0,
                }
            ]
        }
    )
    client.get_instrument_rules = AsyncMock(
        return_value={
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
            "max_market_order_quantity": "100",
            "quantity_step": "0.001",
            "min_notional_value": "5",
        }
    )
    client.close_partial_position = AsyncMock(
        return_value={}
    )
    result = await client.close_percentage_position(
        symbol="BTCUSDT",
        percentage=25,
    )
    client.close_partial_position.assert_awaited_once()
    called_quantity = (
        client.close_partial_position.await_args
        .kwargs["quantity"]
    )
    assert called_quantity == 0.003
    assert result["calculated_close_quantity"] == 0.003
@pytest.mark.asyncio
async def test_percentage_close_100_percent_uses_full_size(
    client: BybitClient,
):
    client.get_positions = AsyncMock(
        return_value={
            "positions": [
                {
                    "symbol": "ETHUSDT",
                    "side": "SHORT",
                    "size": 0.125,
                    "position_index": 2,
                }
            ]
        }
    )
    client.get_instrument_rules = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "category": "linear",
            "symbol": "ETHUSDT",
            "status": "Trading",
            "base_coin": "ETH",
            "quote_coin": "USDT",
            "settle_coin": "USDT",
            "min_price": "0.01",
            "max_price": "100000",
            "tick_size": "0.01",
            "min_order_quantity": "0.001",
            "max_limit_order_quantity": "1000",
            "max_market_order_quantity": "1000",
            "quantity_step": "0.001",
            "min_notional_value": "5",
        }
    )
    client.close_partial_position = AsyncMock(
        return_value={}
    )
    await client.close_percentage_position(
        symbol="ETHUSDT",
        percentage=100,
    )
    client.close_partial_position.assert_awaited_once_with(
        symbol="ETHUSDT",
        quantity=0.125,
        category="linear",
        settle_coin="USDT",
        position_side="SHORT",
        time_in_force="IOC",
        client_order_id=None,
        dry_run=True,
    )
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "percentage",
    [0, -1, 100.01, 150],
)
async def test_percentage_close_rejects_invalid_percentage(
    client: BybitClient,
    percentage: float,
):
    with pytest.raises(HTTPException) as exc_info:
        await client.close_percentage_position(
            symbol="BTCUSDT",
            percentage=percentage,
        )
    assert exc_info.value.status_code == 400
@pytest.mark.asyncio
async def test_percentage_close_rejects_missing_position(
    client: BybitClient,
):
    client.get_positions = AsyncMock(
        return_value={"positions": []}
    )
    with pytest.raises(HTTPException) as exc_info:
        await client.close_percentage_position(
            symbol="BTCUSDT",
            percentage=25,
        )
    assert exc_info.value.status_code == 404
@pytest.mark.asyncio
async def test_percentage_close_requires_side_when_hedged(
    client: BybitClient,
):
    client.get_positions = AsyncMock(
        return_value={
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "size": 0.010,
                    "position_index": 1,
                },
                {
                    "symbol": "BTCUSDT",
                    "side": "SHORT",
                    "size": 0.020,
                    "position_index": 2,
                },
            ]
        }
    )
    with pytest.raises(HTTPException) as exc_info:
        await client.close_percentage_position(
            symbol="BTCUSDT",
            percentage=25,
        )
    assert exc_info.value.status_code == 409
