from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
import pytest
from pydantic import ValidationError
from app.schemas.market_scanner import (
    MarketScanRequest,
)
from app.services.market_scanner_service import (
    MarketScannerService,
)
def build_ticker(
    symbol: str,
    *,
    last_price: float,
    turnover: float,
    volume: float,
    change_percent: float,
):
    return {
        "exchange": "BYBIT",
        "category": "spot",
        "symbol": symbol,
        "last_price": last_price,
        "turnover_24h": turnover,
        "volume_24h": volume,
        "price_change_percent_24h": (
            change_percent
        ),
        "observed_at_ms": 123456789,
    }
def build_service(tickers):
    client = SimpleNamespace(
        get_tickers=AsyncMock(
            return_value={
                "exchange": "BYBIT",
                "category": "spot",
                "observed_at_ms": 123456789,
                "count": len(tickers),
                "tickers": tickers,
            }
        )
    )
    client_factory = MagicMock(
        return_value=client
    )
    service = MarketScannerService(
        client_factory=client_factory
    )
    return service, client, client_factory
@pytest.mark.asyncio
async def test_scan_filters_ranks_and_limits():
    service, client, client_factory = (
        build_service(
            [
                build_ticker(
                    "BTCUSDT",
                    last_price=60000,
                    turnover=1000,
                    volume=10,
                    change_percent=2,
                ),
                build_ticker(
                    "ETHUSDT",
                    last_price=3000,
                    turnover=5000,
                    volume=50,
                    change_percent=-3,
                ),
                build_ticker(
                    "XRPUSDT",
                    last_price=0.5,
                    turnover=3000,
                    volume=5000,
                    change_percent=8,
                ),
                build_ticker(
                    "BTCUSDC",
                    last_price=60010,
                    turnover=9000,
                    volume=12,
                    change_percent=1,
                ),
            ]
        )
    )
    request = MarketScanRequest(
        quote_coin="usdt",
        minimum_turnover_24h=2000,
        sort_by="turnover_24h",
        descending=True,
        limit=2,
    )
    result = await service.scan(request)
    assert result.total_received == 4
    assert result.total_matched == 2
    assert result.returned_count == 2
    assert [
        ticker.symbol
        for ticker in result.tickers
    ] == [
        "ETHUSDT",
        "XRPUSDT",
    ]
    client_factory.assert_called_once_with(
        False
    )
    client.get_tickers.assert_awaited_once_with(
        category="spot"
    )
@pytest.mark.asyncio
async def test_scan_uses_normalized_symbols():
    service, _, _ = build_service(
        [
            build_ticker(
                "BTCUSDT",
                last_price=60000,
                turnover=1000,
                volume=10,
                change_percent=2,
            ),
            build_ticker(
                "ETHUSDT",
                last_price=3000,
                turnover=2000,
                volume=20,
                change_percent=3,
            ),
        ]
    )
    request = MarketScanRequest(
        quote_coin=None,
        symbols=[
            "btcusdt",
            "BTCUSDT",
        ],
    )
    assert request.symbols == ["BTCUSDT"]
    result = await service.scan(request)
    assert result.total_matched == 1
    assert result.tickers[0].symbol == "BTCUSDT"
@pytest.mark.asyncio
async def test_scan_sorts_by_absolute_change():
    service, _, _ = build_service(
        [
            build_ticker(
                "BTCUSDT",
                last_price=60000,
                turnover=1000,
                volume=10,
                change_percent=2,
            ),
            build_ticker(
                "ETHUSDT",
                last_price=3000,
                turnover=2000,
                volume=20,
                change_percent=-7,
            ),
            build_ticker(
                "XRPUSDT",
                last_price=0.5,
                turnover=3000,
                volume=30,
                change_percent=4,
            ),
        ]
    )
    result = await service.scan(
        MarketScanRequest(
            sort_by=(
                "absolute_"
                "price_change_percent_24h"
            ),
            limit=3,
        )
    )
    assert [
        ticker.symbol
        for ticker in result.tickers
    ] == [
        "ETHUSDT",
        "XRPUSDT",
        "BTCUSDT",
    ]
@pytest.mark.asyncio
async def test_scan_handles_no_matches():
    service, _, _ = build_service(
        [
            build_ticker(
                "BTCUSDT",
                last_price=60000,
                turnover=1000,
                volume=10,
                change_percent=2,
            )
        ]
    )
    result = await service.scan(
        MarketScanRequest(
            minimum_turnover_24h=999999,
        )
    )
    assert result.total_received == 1
    assert result.total_matched == 0
    assert result.returned_count == 0
    assert result.tickers == []
def test_scan_request_rejects_bad_ranges():
    with pytest.raises(ValidationError):
        MarketScanRequest(
            minimum_price=100,
            maximum_price=10,
        )
    with pytest.raises(ValidationError):
        MarketScanRequest(
            minimum_change_percent_24h=10,
            maximum_change_percent_24h=-10,
        )
