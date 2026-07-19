from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api.v1.endpoints.market_scanner import (
    get_current_websocket_user,
)
from app.main import app
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
    MarketTickerStreamEvent,
)
class FakeStreamClient:
    def __init__(
        self,
        events=None,
    ):
        self.events = events or []
        self.calls = []
    async def stream_tickers(
        self,
        *,
        symbols,
        category,
        max_messages,
    ):
        self.calls.append(
            {
                "symbols": symbols,
                "category": category,
                "max_messages": max_messages,
            }
        )
        for event in self.events:
            yield event
def build_event():
    ticker = MarketTickerSnapshot(
        exchange="BYBIT",
        category="spot",
        symbol="BTCUSDT",
        last_price=60000,
        bid_price=59999,
        ask_price=60001,
        spread=2,
        spread_percent=0.003333,
        observed_at_ms=123456789,
    )
    return MarketTickerStreamEvent(
        exchange="BYBIT",
        category="spot",
        topic="tickers.BTCUSDT",
        message_type="snapshot",
        symbol="BTCUSDT",
        sequence=1,
        exchange_timestamp_ms=123456789,
        received_at_ms=123456790,
        ticker=ticker,
    )
def test_market_stream_route_is_registered():
    path = app.url_path_for(
        "stream_market_tickers"
    )
    assert str(path) == (
        "/api/v1/market-scanner/stream"
    )
def test_market_stream_requires_authentication():
    client = TestClient(app)
    try:
        with client.websocket_connect(
            (
                "/api/v1/market-scanner/stream"
                "?symbols=BTCUSDT"
            )
        ):
            raise AssertionError(
                "Unauthenticated connection "
                "should not be accepted"
            )
    except Exception as exc:
        assert (
            getattr(exc, "code", None)
            == 4401
            or "4401" in str(exc)
        )
def test_market_stream_sends_connection_and_update():
    fake_client = FakeStreamClient(
        events=[build_event()]
    )
    app.dependency_overrides[
        get_current_websocket_user
    ] = lambda: SimpleNamespace(
        id=1,
        is_active=True,
    )
    client = TestClient(app)
    try:
        with patch(
            (
                "app.api.v1.endpoints."
                "market_scanner."
                "get_market_stream_client"
            ),
            return_value=fake_client,
        ):
            with client.websocket_connect(
                (
                    "/api/v1/market-scanner/stream"
                    "?symbols=btcusdt"
                    "&category=spot"
                    "&max_messages=1"
                )
            ) as websocket:
                connected = (
                    websocket.receive_json()
                )
                update = (
                    websocket.receive_json()
                )
        assert connected["success"] is True
        assert (
            connected["message"]
            == "Market ticker stream connected"
        )
        assert (
            connected["data"]["symbols"]
            == ["BTCUSDT"]
        )
        assert update["success"] is True
        assert (
            update["message"]
            == "Market ticker update"
        )
        assert (
            update["data"]["symbol"]
            == "BTCUSDT"
        )
        assert (
            update["data"]["ticker"][
                "last_price"
            ]
            == 60000.0
        )
        assert fake_client.calls == [
            {
                "symbols": ["BTCUSDT"],
                "category": "spot",
                "max_messages": 1,
            }
        ]
    finally:
        app.dependency_overrides.clear()
def test_market_stream_normalizes_multiple_symbols():
    fake_client = FakeStreamClient()
    app.dependency_overrides[
        get_current_websocket_user
    ] = lambda: SimpleNamespace(
        id=1,
        is_active=True,
    )
    client = TestClient(app)
    try:
        with patch(
            (
                "app.api.v1.endpoints."
                "market_scanner."
                "get_market_stream_client"
            ),
            return_value=fake_client,
        ):
            with client.websocket_connect(
                (
                    "/api/v1/market-scanner/stream"
                    "?symbols=btcusdt,"
                    "%20ETHUSDT,btcusdt"
                    "&category=linear"
                )
            ) as websocket:
                connected = (
                    websocket.receive_json()
                )
        assert connected["data"]["symbols"] == [
            "BTCUSDT",
            "ETHUSDT",
        ]
        assert connected["data"]["category"] == (
            "linear"
        )
        assert fake_client.calls == [
            {
                "symbols": [
                    "BTCUSDT",
                    "ETHUSDT",
                ],
                "category": "linear",
                "max_messages": None,
            }
        ]
    finally:
        app.dependency_overrides.clear()
