from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import (
    SimpleNamespace,
)
import pytest
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.services.trading_bot_runtime_market_history_service import (
    TradingBotRuntimeMarketHistoryService,
)
NOW = datetime(
    2026,
    7,
    22,
    0,
    0,
    tzinfo=UTC,
)
def build_bot(
    *,
    bot_id=10,
    symbol="BTCUSDT",
):
    return SimpleNamespace(
        id=bot_id,
        user_id=7,
        symbol=symbol,
        category="linear",
        timeframe="1m",
    )
def build_ticker(
    price,
):
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="linear",
        symbol="BTCUSDT",
        last_price=price,
        bid_price=price - 0.1,
        ask_price=price + 0.1,
        volume_24h=1000,
        turnover_24h=100000,
    )
def test_runtime_history_is_bounded():
    service = (
        TradingBotRuntimeMarketHistoryService(
            max_samples=3
        )
    )
    bot = build_bot()
    for index, price in enumerate([
        100,
        101,
        102,
        103,
    ]):
        service.append_ticker(
            bot=bot,
            ticker=build_ticker(
                price
            ),
            observed_at=(
                NOW
                + timedelta(
                    minutes=index
                )
            ),
        )
    history = service.get(
        bot=bot
    )
    assert [
        sample.close_price
        for sample in history
    ] == [
        101,
        102,
        103,
    ]
def test_runtime_history_is_bot_scoped():
    service = (
        TradingBotRuntimeMarketHistoryService()
    )
    first_bot = build_bot(
        bot_id=10
    )
    second_bot = build_bot(
        bot_id=11
    )
    service.append_ticker(
        bot=first_bot,
        ticker=build_ticker(100),
        observed_at=NOW,
    )
    service.append_ticker(
        bot=second_bot,
        ticker=build_ticker(200),
        observed_at=NOW,
    )
    assert (
        service.get(
            bot=first_bot
        )[0].close_price
        == 100
    )
    assert (
        service.get(
            bot=second_bot
        )[0].close_price
        == 200
    )
def test_duplicate_timestamp_replaces_sample():
    service = (
        TradingBotRuntimeMarketHistoryService()
    )
    bot = build_bot()
    service.append_ticker(
        bot=bot,
        ticker=build_ticker(100),
        observed_at=NOW,
    )
    history = service.append_ticker(
        bot=bot,
        ticker=build_ticker(101),
        observed_at=NOW,
    )
    assert len(history) == 1
    assert (
        history[0].close_price
        == 101
    )
def test_runtime_history_rejects_backwards_time():
    service = (
        TradingBotRuntimeMarketHistoryService()
    )
    bot = build_bot()
    service.append_ticker(
        bot=bot,
        ticker=build_ticker(100),
        observed_at=NOW,
    )
    with pytest.raises(
        ValueError,
        match="backwards",
    ):
        service.append_ticker(
            bot=bot,
            ticker=build_ticker(99),
            observed_at=(
                NOW
                - timedelta(minutes=1)
            ),
        )
def test_runtime_history_can_be_cleared():
    service = (
        TradingBotRuntimeMarketHistoryService()
    )
    bot = build_bot()
    service.append_ticker(
        bot=bot,
        ticker=build_ticker(100),
        observed_at=NOW,
    )
    assert service.clear(
        bot=bot
    ) is True
    assert service.get(
        bot=bot
    ) == []
    assert service.clear(
        bot=bot
    ) is False
