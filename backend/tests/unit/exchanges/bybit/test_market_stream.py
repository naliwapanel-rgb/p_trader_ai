import json
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.exchanges.bybit.market_stream import (
    BybitTickerStreamClient,
)
from app.schemas.market_scanner import (
    MarketTickerStreamSubscription,
)
class FakeWebSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent_messages: list[str] = []
    async def send(self, payload: str):
        self.sent_messages.append(payload)
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)
class FakeConnectionContext:
    def __init__(self, websocket):
        self.websocket = websocket
    async def __aenter__(self):
        return self.websocket
    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False
class FakeConnectFactory:
    def __init__(self, websocket):
        self.websocket = websocket
        self.calls: list[tuple] = []
    def __call__(self, url, **kwargs):
        self.calls.append(
            (
                url,
                kwargs,
            )
        )
        return FakeConnectionContext(
            self.websocket
        )
async def collect_events(generator):
    return [
        event
        async for event in generator
    ]
def test_stream_subscription_normalizes_symbols():
    subscription = (
        MarketTickerStreamSubscription(
            symbols=[
                "btcusdt",
                " BTCUSDT ",
                "ethusdt",
            ]
        )
    )
    assert subscription.symbols == [
        "BTCUSDT",
        "ETHUSDT",
    ]
    with pytest.raises(ValidationError):
        MarketTickerStreamSubscription(
            symbols=[""],
        )
def test_websocket_urls_are_category_specific():
    mainnet = BybitTickerStreamClient()
    testnet = BybitTickerStreamClient(
        is_testnet=True
    )
    assert mainnet.websocket_url("spot") == (
        "wss://stream.bybit.com/"
        "v5/public/spot"
    )
    assert mainnet.websocket_url("linear") == (
        "wss://stream.bybit.com/"
        "v5/public/linear"
    )
    assert mainnet.websocket_url("inverse") == (
        "wss://stream.bybit.com/"
        "v5/public/inverse"
    )
    assert testnet.websocket_url("spot") == (
        "wss://stream-testnet.bybit.com/"
        "v5/public/spot"
    )
@pytest.mark.asyncio
async def test_spot_subscriptions_are_batched_by_ten():
    websocket = FakeWebSocket([])
    connect_factory = FakeConnectFactory(
        websocket
    )
    client = BybitTickerStreamClient(
        connect_factory=connect_factory,
        heartbeat_interval_seconds=3600,
    )
    symbols = [
        f"COIN{index}USDT"
        for index in range(11)
    ]
    events = await collect_events(
        client.stream_tickers(
            symbols=symbols,
            category="spot",
        )
    )
    assert events == []
    requests = [
        json.loads(payload)
        for payload in websocket.sent_messages
    ]
    assert len(requests) == 2
    assert len(requests[0]["args"]) == 10
    assert len(requests[1]["args"]) == 1
    assert requests[0]["op"] == "subscribe"
@pytest.mark.asyncio
async def test_stream_yields_normalized_snapshot():
    websocket = FakeWebSocket(
        [
            json.dumps(
                {
                    "success": True,
                    "ret_msg": "subscribe",
                    "op": "subscribe",
                }
            ),
            json.dumps(
                {
                    "topic": "tickers.BTCUSDT",
                    "type": "snapshot",
                    "ts": 123456789,
                    "cs": 100,
                    "data": {
                        "symbol": "BTCUSDT",
                        "lastPrice": "60000",
                        "prevPrice24h": "59000",
                        "bid1Price": "59999",
                        "ask1Price": "60001",
                        "volume24h": "100",
                        "turnover24h": "6000000",
                        "price24hPcnt": "0.016949",
                    },
                }
            ),
        ]
    )
    client = BybitTickerStreamClient(
        connect_factory=FakeConnectFactory(
            websocket
        ),
        heartbeat_interval_seconds=3600,
    )
    events = await collect_events(
        client.stream_tickers(
            symbols=["btcusdt"],
            category="spot",
            max_messages=1,
        )
    )
    assert len(events) == 1
    event = events[0]
    assert event.symbol == "BTCUSDT"
    assert event.message_type == "snapshot"
    assert event.sequence == 100
    assert event.exchange_timestamp_ms == 123456789
    assert event.ticker.last_price == 60000.0
    assert event.ticker.spread == 2.0
    assert (
        event.ticker.price_change_percent_24h
        == pytest.approx(1.6949)
    )
@pytest.mark.asyncio
async def test_linear_delta_merges_snapshot_state():
    websocket = FakeWebSocket(
        [
            json.dumps(
                {
                    "topic": "tickers.ETHUSDT",
                    "type": "snapshot",
                    "ts": 1000,
                    "cs": 1,
                    "data": {
                        "symbol": "ETHUSDT",
                        "lastPrice": "3000",
                        "prevPrice24h": "2900",
                        "bid1Price": "2999",
                        "ask1Price": "3001",
                        "markPrice": "3000.5",
                    },
                }
            ),
            json.dumps(
                {
                    "topic": "tickers.ETHUSDT",
                    "type": "delta",
                    "ts": 1001,
                    "cs": 2,
                    "data": {
                        "ask1Price": "3002",
                    },
                }
            ),
        ]
    )
    client = BybitTickerStreamClient(
        connect_factory=FakeConnectFactory(
            websocket
        ),
        heartbeat_interval_seconds=3600,
    )
    events = await collect_events(
        client.stream_tickers(
            symbols=["ETHUSDT"],
            category="linear",
            max_messages=2,
        )
    )
    assert len(events) == 2
    delta_event = events[1]
    assert delta_event.message_type == "delta"
    assert delta_event.sequence == 2
    assert (
        delta_event.ticker.last_price
        == 3000.0
    )
    assert (
        delta_event.ticker.bid_price
        == 2999.0
    )
    assert (
        delta_event.ticker.ask_price
        == 3002.0
    )
    assert (
        delta_event.ticker.mark_price
        == 3000.5
    )
@pytest.mark.asyncio
async def test_subscription_failure_is_reported():
    websocket = FakeWebSocket(
        [
            json.dumps(
                {
                    "success": False,
                    "ret_msg": "Invalid topic",
                    "op": "subscribe",
                }
            )
        ]
    )
    client = BybitTickerStreamClient(
        connect_factory=FakeConnectFactory(
            websocket
        ),
        heartbeat_interval_seconds=3600,
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        await collect_events(
            client.stream_tickers(
                symbols=["BTCUSDT"],
                category="spot",
            )
        )
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == (
        "Bybit WebSocket subscription failed: "
        "Invalid topic"
    )
@pytest.mark.asyncio
async def test_malformed_websocket_message_is_rejected():
    websocket = FakeWebSocket(
        [
            "not-json",
        ]
    )
    client = BybitTickerStreamClient(
        connect_factory=FakeConnectFactory(
            websocket
        ),
        heartbeat_interval_seconds=3600,
    )
    with pytest.raises(
        HTTPException
    ) as exc_info:
        await collect_events(
            client.stream_tickers(
                symbols=["BTCUSDT"],
                category="spot",
            )
        )
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == (
        "Bybit returned malformed "
        "WebSocket data"
    )
