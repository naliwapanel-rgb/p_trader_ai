from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import (
    SimpleNamespace,
)
import pytest
from app.schemas.trading_bot_backtest import (
    HistoricalMarketCandle,
    TradingBotBacktestRequest,
)
from app.services.backtest_market_replay_service import (
    BacktestMarketReplayService,
)
BASE_TIME = datetime(
    2026,
    7,
    1,
    0,
    0,
    tzinfo=UTC,
)
def build_bot():
    return SimpleNamespace(
        id=10,
        user_id=7,
        symbol="btcusdt",
        category="linear",
        timeframe="12h",
    )
def build_candle(
    *,
    start_hour: int,
    close_price: float,
    high_price: float,
    low_price: float,
    volume: float,
    turnover_usd: float,
):
    opened_at = (
        BASE_TIME
        + timedelta(
            hours=start_hour
        )
    )
    return HistoricalMarketCandle(
        opened_at=opened_at,
        closed_at=(
            opened_at
            + timedelta(hours=12)
        ),
        open_price=(
            close_price - 1
        ),
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume,
        turnover_usd=turnover_usd,
    )
def build_request():
    return TradingBotBacktestRequest(
        candles=[
            build_candle(
                start_hour=0,
                close_price=100,
                high_price=102,
                low_price=98,
                volume=1,
                turnover_usd=100,
            ),
            build_candle(
                start_hour=12,
                close_price=105,
                high_price=106,
                low_price=103,
                volume=2,
                turnover_usd=210,
            ),
            build_candle(
                start_hour=24,
                close_price=110,
                high_price=112,
                low_price=108,
                volume=3,
                turnover_usd=330,
            ),
        ]
    )
def test_replay_builds_chronological_frames():
    frames = (
        BacktestMarketReplayService
        .build_frames(
            bot=build_bot(),
            data=build_request(),
        )
    )
    assert len(frames) == 3
    assert [
        frame.sequence
        for frame in frames
    ] == [
        1,
        2,
        3,
    ]
    assert (
        frames[0].candle.closed_at
        < frames[1].candle.closed_at
        < frames[2].candle.closed_at
    )
def test_replay_uses_no_future_market_data():
    frames = (
        BacktestMarketReplayService
        .build_frames(
            bot=build_bot(),
            data=build_request(),
        )
    )
    first = frames[0]
    assert (
        first.ticker.high_24h
        == 102
    )
    assert (
        first.ticker.low_24h
        == 98
    )
    assert (
        first.ticker.volume_24h
        == 1
    )
    assert (
        first.ticker.turnover_24h
        == 100
    )
    assert (
        first.warmup_complete
        is False
    )
def test_replay_calculates_trailing_24h_values():
    frames = (
        BacktestMarketReplayService
        .build_frames(
            bot=build_bot(),
            data=build_request(),
        )
    )
    last = frames[-1]
    assert (
        last.warmup_complete
        is True
    )
    assert (
        last.ticker.previous_price_24h
        == 100
    )
    assert (
        last.ticker.price_change_24h
        == 10
    )
    assert (
        last.ticker
        .price_change_percent_24h
        == pytest.approx(10)
    )
    assert (
        last.ticker.high_24h
        == 112
    )
    assert (
        last.ticker.low_24h
        == 103
    )
    assert (
        last.ticker.volume_24h
        == 5
    )
    assert (
        last.ticker.turnover_24h
        == 540
    )
def test_replay_derives_missing_turnover():
    request = build_request()
    request.candles[0].turnover_usd = 0
    frames = (
        BacktestMarketReplayService
        .build_frames(
            bot=build_bot(),
            data=request,
        )
    )
    assert (
        frames[0]
        .ticker
        .turnover_24h
        == 100
    )
def test_replay_uses_bot_market_identity():
    frames = (
        BacktestMarketReplayService
        .build_frames(
            bot=build_bot(),
            data=build_request(),
        )
    )
    ticker = frames[0].ticker
    assert ticker.exchange == "BACKTEST"
    assert ticker.symbol == "BTCUSDT"
    assert ticker.category == "linear"
    assert ticker.last_price == 100
    assert ticker.bid_price == 100
    assert ticker.ask_price == 100
    assert ticker.spread_percent == 0
