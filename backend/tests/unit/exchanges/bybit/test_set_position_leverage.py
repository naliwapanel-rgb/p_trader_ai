from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from app.exchanges.bybit.client import BybitClient
def make_client():
    client = object.__new__(BybitClient)
    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {},
        }
    )
    return client
@pytest.mark.asyncio
async def test_set_position_leverage_dry_run():
    client = make_client()
    result = await client.set_position_leverage(
        symbol="btcusdt",
        buy_leverage=10,
        sell_leverage=10,
        category="LINEAR",
        dry_run=True,
    )
    client._private_post.assert_not_awaited()
    assert result == {
        "exchange": "BYBIT",
        "category": "linear",
        "symbol": "BTCUSDT",
        "buy_leverage": 10.0,
        "sell_leverage": 10.0,
        "dry_run": True,
        "accepted": False,
        "message": (
            "Dry run completed. No leverage update was "
            "sent to Bybit."
        ),
    }
@pytest.mark.asyncio
async def test_set_position_leverage_live_request():
    client = make_client()
    result = await client.set_position_leverage(
        symbol="BTCUSDT",
        buy_leverage=5,
        sell_leverage=7,
        category="linear",
        dry_run=False,
    )
    client._private_post.assert_awaited_once_with(
        endpoint="/v5/position/set-leverage",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "buyLeverage": "5",
            "sellLeverage": "7",
        },
    )
    assert result["accepted"] is True
    assert result["dry_run"] is False
    assert result["buy_leverage"] == 5.0
    assert result["sell_leverage"] == 7.0
    assert result["message"] == (
        "Position leverage update accepted by Bybit."
    )
@pytest.mark.asyncio
async def test_set_position_leverage_supports_inverse():
    client = make_client()
    await client.set_position_leverage(
        symbol="btcusd",
        buy_leverage=3,
        sell_leverage=3,
        category="inverse",
        dry_run=False,
    )
    client._private_post.assert_awaited_once_with(
        endpoint="/v5/position/set-leverage",
        body={
            "category": "inverse",
            "symbol": "BTCUSD",
            "buyLeverage": "3",
            "sellLeverage": "3",
        },
    )
@pytest.mark.asyncio
async def test_set_position_leverage_preserves_decimal_values():
    client = make_client()
    await client.set_position_leverage(
        symbol="ETHUSDT",
        buy_leverage=2.5,
        sell_leverage=4.25,
        dry_run=False,
    )
    client._private_post.assert_awaited_once_with(
        endpoint="/v5/position/set-leverage",
        body={
            "category": "linear",
            "symbol": "ETHUSDT",
            "buyLeverage": "2.5",
            "sellLeverage": "4.25",
        },
    )
@pytest.mark.asyncio
async def test_set_position_leverage_rejects_empty_symbol():
    client = make_client()
    with pytest.raises(HTTPException) as exc_info:
        await client.set_position_leverage(
            symbol=" ",
            buy_leverage=10,
            sell_leverage=10,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "symbol is required"
    client._private_post.assert_not_awaited()
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category",
    [
        "spot",
        "option",
        "",
    ],
)
async def test_set_position_leverage_rejects_category(
    category,
):
    client = make_client()
    with pytest.raises(HTTPException) as exc_info:
        await client.set_position_leverage(
            symbol="BTCUSDT",
            buy_leverage=10,
            sell_leverage=10,
            category=category,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "Position leverage is supported only for "
        "linear and inverse categories"
    )
    client._private_post.assert_not_awaited()
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "buy_leverage",
    [
        0,
        -1,
    ],
)
async def test_set_position_leverage_rejects_invalid_buy(
    buy_leverage,
):
    client = make_client()
    with pytest.raises(HTTPException) as exc_info:
        await client.set_position_leverage(
            symbol="BTCUSDT",
            buy_leverage=buy_leverage,
            sell_leverage=10,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "buy_leverage must be greater than zero"
    )
    client._private_post.assert_not_awaited()
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sell_leverage",
    [
        0,
        -1,
    ],
)
async def test_set_position_leverage_rejects_invalid_sell(
    sell_leverage,
):
    client = make_client()
    with pytest.raises(HTTPException) as exc_info:
        await client.set_position_leverage(
            symbol="BTCUSDT",
            buy_leverage=10,
            sell_leverage=sell_leverage,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "sell_leverage must be greater than zero"
    )
    client._private_post.assert_not_awaited()
