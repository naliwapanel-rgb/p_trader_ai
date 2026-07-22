from datetime import (
    UTC,
    datetime,
    timedelta,
    timezone,
)
import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
)
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
    TradingBotStrategyContext,
)
NOW = datetime(
    2026,
    7,
    21,
    20,
    0,
    tzinfo=UTC,
)
def build_ticker(
    price=100,
):
    return MarketTickerSnapshot(
        exchange="BACKTEST",
        category="linear",
        symbol="BTCUSDT",
        last_price=price,
        bid_price=price,
        ask_price=price,
        spread=0,
        spread_percent=0,
        volume_24h=1000,
        turnover_24h=100000,
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_sample(
    *,
    observed_at=NOW,
    price=100,
):
    return TradingBotMarketSample(
        observed_at=observed_at,
        open_price=price,
        high_price=price + 1,
        low_price=price - 1,
        close_price=price,
        bid_price=price - 0.1,
        ask_price=price + 0.1,
        volume=100,
        turnover_usd=(
            price * 100
        ),
        source="CANDLE",
    )
def build_context(
    history,
    price=100,
):
    return TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="TREND",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        config={},
        ticker=build_ticker(
            price
        ),
        market_history=history,
        evaluated_at=NOW,
    )
def test_phase_12j_strategy_types_supported():
    for strategy_type in [
        "TREND",
        "MEAN_REVERSION",
        "SCALPING",
    ]:
        bot = TradingBotCreateRequest(
            name=(
                f"{strategy_type} Bot"
            ),
            strategy_type=strategy_type,
            symbol="BTCUSDT",
        )
        assert (
            bot.strategy_type
            == strategy_type
        )
def test_sample_normalizes_timezone():
    offset_time = datetime(
        2026,
        7,
        21,
        22,
        0,
        tzinfo=timezone(
            timedelta(hours=2)
        ),
    )
    sample = build_sample(
        observed_at=offset_time,
    )
    assert sample.observed_at == NOW
def test_sample_rejects_invalid_ohlc():
    with pytest.raises(
        ValidationError,
        match="high_price",
    ):
        TradingBotMarketSample(
            observed_at=NOW,
            open_price=100,
            high_price=99,
            low_price=98,
            close_price=100,
        )
def test_sample_rejects_inverted_quotes():
    with pytest.raises(
        ValidationError,
        match="ask_price",
    ):
        TradingBotMarketSample(
            observed_at=NOW,
            open_price=100,
            high_price=101,
            low_price=99,
            close_price=100,
            bid_price=101,
            ask_price=100,
        )
def test_context_defaults_empty_history():
    context = build_context([])
    assert context.market_history == []
def test_context_accepts_chronological_history():
    history = [
        build_sample(
            observed_at=(
                NOW
                - timedelta(minutes=10)
            ),
            price=98,
        ),
        build_sample(
            observed_at=(
                NOW
                - timedelta(minutes=5)
            ),
            price=99,
        ),
        build_sample(
            observed_at=NOW,
            price=100,
        ),
    ]
    context = build_context(
        history
    )
    assert len(
        context.market_history
    ) == 3
    assert (
        context.market_history[-1]
        .close_price
        == 100
    )
def test_context_rejects_unordered_history():
    history = [
        build_sample(
            observed_at=NOW,
            price=99,
        ),
        build_sample(
            observed_at=(
                NOW
                - timedelta(minutes=5)
            ),
            price=100,
        ),
    ]
    with pytest.raises(
        ValidationError,
        match="chronological",
    ):
        build_context(
            history
        )
def test_context_rejects_future_history():
    history = [
        build_sample(
            observed_at=(
                NOW
                + timedelta(minutes=1)
            ),
            price=100,
        )
    ]
    with pytest.raises(
        ValidationError,
        match="future",
    ):
        build_context(
            history
        )
def test_context_rejects_latest_price_mismatch():
    history = [
        build_sample(
            observed_at=NOW,
            price=99,
        )
    ]
    with pytest.raises(
        ValidationError,
        match="does not match",
    ):
        build_context(
            history,
            price=100,
        )
