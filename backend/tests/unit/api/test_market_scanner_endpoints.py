from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from app.api.v1.endpoints.market_scanner import (
    get_market_scanner_service,
    list_market_tickers,
    scan_market,
)
from app.main import app
from app.schemas.market_scanner import (
    MarketScanRequest,
    MarketScanResult,
    MarketTickerBatch,
    MarketTickerSnapshot,
)
from app.services.market_scanner_service import (
    MarketScannerService,
)
def build_ticker() -> MarketTickerSnapshot:
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="spot",
        symbol="BTCUSDT",
        last_price=60000,
        bid_price=59999,
        ask_price=60001,
        spread=2,
        spread_percent=0.003333,
        volume_24h=100,
        turnover_24h=6000000,
        observed_at_ms=123456789,
    )
def test_market_scanner_routes_are_registered():
    paths = app.openapi()["paths"]
    assert (
        "/api/v1/market-scanner/tickers"
        in paths
    )
    assert (
        "/api/v1/market-scanner/scan"
        in paths
    )
    assert (
        "get"
        in paths[
            "/api/v1/market-scanner/tickers"
        ]
    )
    assert (
        "post"
        in paths[
            "/api/v1/market-scanner/scan"
        ]
    )
def test_market_scanner_routes_require_authentication():
    paths = app.openapi()["paths"]
    ticker_operation = paths[
        "/api/v1/market-scanner/tickers"
    ]["get"]
    scan_operation = paths[
        "/api/v1/market-scanner/scan"
    ]["post"]
    assert ticker_operation["security"]
    assert scan_operation["security"]
def test_get_market_scanner_service_returns_service():
    service = get_market_scanner_service(
        current_user=SimpleNamespace(id=1)
    )
    assert isinstance(
        service,
        MarketScannerService,
    )
@pytest.mark.asyncio
async def test_tickers_endpoint_delegates_to_service():
    batch = MarketTickerBatch(
        exchange="BYBIT",
        category="spot",
        observed_at_ms=123456789,
        count=1,
        tickers=[build_ticker()],
    )
    service = SimpleNamespace(
        get_tickers=AsyncMock(
            return_value=batch
        )
    )
    response = await list_market_tickers(
        category="spot",
        is_testnet=True,
        service=service,
    )
    service.get_tickers.assert_awaited_once_with(
        category="spot",
        is_testnet=True,
    )
    assert response["success"] is True
    assert (
        response["message"]
        == (
            "Market ticker snapshots retrieved "
            "successfully"
        )
    )
    assert (
        response["data"]
        == batch.model_dump(mode="json")
    )
@pytest.mark.asyncio
async def test_scan_endpoint_delegates_to_service():
    request = MarketScanRequest(
        category="spot",
        quote_coin="USDT",
        minimum_turnover_24h=1000,
        limit=10,
    )
    result = MarketScanResult(
        exchange="BYBIT",
        category="spot",
        quote_coin="USDT",
        total_received=5,
        total_matched=1,
        returned_count=1,
        scanned_at_ms=123456789,
        tickers=[build_ticker()],
    )
    service = SimpleNamespace(
        scan=AsyncMock(
            return_value=result
        )
    )
    response = await scan_market(
        data=request,
        service=service,
    )
    service.scan.assert_awaited_once_with(
        request
    )
    assert response["success"] is True
    assert (
        response["message"]
        == "Market scan completed successfully"
    )
    assert (
        response["data"]
        == result.model_dump(mode="json")
    )
def test_ticker_route_exposes_query_parameters():
    operation = app.openapi()["paths"][
        "/api/v1/market-scanner/tickers"
    ]["get"]
    parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
    }
    assert set(parameters) == {
        "category",
        "is_testnet",
    }
    category_schema = parameters[
        "category"
    ]["schema"]
    assert category_schema["default"] == "spot"
    assert set(category_schema["enum"]) == {
        "spot",
        "linear",
        "inverse",
    }
    assert (
        parameters["is_testnet"]["schema"][
            "default"
        ]
        is False
    )
