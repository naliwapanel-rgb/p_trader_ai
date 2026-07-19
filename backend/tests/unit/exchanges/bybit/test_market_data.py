from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from app.exchanges.bybit.market_data import (
    BybitMarketDataClient,
)
@pytest.mark.asyncio
async def test_get_tickers_normalizes_spot_data():
    client = BybitMarketDataClient()
    client._request_tickers = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "category": "spot",
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "bid1Price": "100",
                        "bid1Size": "2",
                        "ask1Price": "102",
                        "ask1Size": "3",
                        "lastPrice": "101",
                        "prevPrice24h": "96",
                        "price24hPcnt": "0.052083",
                        "highPrice24h": "110",
                        "lowPrice24h": "90",
                        "turnover24h": "500000",
                        "volume24h": "5000",
                        "usdIndexPrice": "101.5",
                    }
                ],
            },
            "time": 123456789,
        }
    )
    result = await client.get_tickers(
        category="SPOT"
    )
    assert result["exchange"] == "BYBIT"
    assert result["category"] == "spot"
    assert result["count"] == 1
    assert result["observed_at_ms"] == 123456789
    ticker = result["tickers"][0]
    assert ticker["symbol"] == "BTCUSDT"
    assert ticker["last_price"] == 101.0
    assert ticker["spread"] == 2.0
    assert ticker["spread_percent"] == pytest.approx(
        1.980198,
        rel=1e-5,
    )
    assert ticker["price_change_24h"] == 5.0
    assert (
        ticker["price_change_percent_24h"]
        == pytest.approx(5.2083)
    )
    assert ticker["turnover_24h"] == 500000.0
@pytest.mark.asyncio
async def test_get_tickers_normalizes_linear_data():
    client = BybitMarketDataClient()
    client._request_tickers = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "category": "linear",
                "list": [
                    {
                        "symbol": "ETHUSDT",
                        "lastPrice": "3000",
                        "prevPrice24h": "3100",
                        "bid1Price": "2999",
                        "ask1Price": "3001",
                        "indexPrice": "3002",
                        "markPrice": "3000.5",
                        "openInterest": "125",
                        "openInterestValue": "375000",
                        "fundingRate": "0.0001",
                        "nextFundingTime": (
                            "123456799"
                        ),
                    }
                ],
            },
            "time": 123456789,
        }
    )
    result = await client.get_tickers(
        category="linear"
    )
    ticker = result["tickers"][0]
    assert ticker["index_price"] == 3002.0
    assert ticker["mark_price"] == 3000.5
    assert ticker["open_interest"] == 125.0
    assert (
        ticker["open_interest_value"]
        == 375000.0
    )
    assert ticker["funding_rate"] == 0.0001
    assert (
        ticker["next_funding_time_ms"]
        == 123456799
    )
@pytest.mark.asyncio
async def test_get_tickers_rejects_category():
    client = BybitMarketDataClient()
    client._request_tickers = AsyncMock()
    with pytest.raises(HTTPException) as exc_info:
        await client.get_tickers(
            category="option"
        )
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == (
            "category must be spot, "
            "linear or inverse"
        )
    )
    client._request_tickers.assert_not_awaited()
@pytest.mark.asyncio
async def test_get_tickers_maps_bybit_error():
    client = BybitMarketDataClient()
    client._request_tickers = AsyncMock(
        return_value={
            "retCode": 10001,
            "retMsg": "Invalid category",
        }
    )
    with pytest.raises(HTTPException) as exc_info:
        await client.get_tickers(
            category="spot"
        )
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Bybit API error: Invalid category"
    )
@pytest.mark.asyncio
async def test_get_tickers_rejects_bad_list():
    client = BybitMarketDataClient()
    client._request_tickers = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "category": "spot",
                "list": {
                    "symbol": "BTCUSDT",
                },
            },
        }
    )
    with pytest.raises(HTTPException) as exc_info:
        await client.get_tickers(
            category="spot"
        )
    assert exc_info.value.status_code == 502
    assert (
        exc_info.value.detail
        == "Bybit returned invalid ticker data"
    )
