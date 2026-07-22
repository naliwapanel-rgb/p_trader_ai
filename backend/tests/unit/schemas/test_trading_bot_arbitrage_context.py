from datetime import (
    UTC,
    datetime,
)
from decimal import (
    Decimal,
)
import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.arbitrage import (
    ArbitrageMarketQuote,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    ArbitrageStrategyConfig,
    TradingBotStrategyContext,
)
NOW = datetime(
    2026,
    7,
    22,
    9,
    0,
    tzinfo=UTC,
)
def build_ticker():
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="spot",
        symbol="BTCUSDT",
        last_price=100,
        bid_price=99,
        bid_size=10,
        ask_price=100,
        ask_size=10,
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_quote(
    *,
    exchange="BYBIT",
    symbol="BTCUSDT",
    base_asset="BTC",
    quote_asset="USDT",
    bid_price="99",
    ask_price="100",
    observed_at_ms=None,
):
    return ArbitrageMarketQuote(
        exchange=exchange,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        bid_price=Decimal(
            bid_price
        ),
        ask_price=Decimal(
            ask_price
        ),
        bid_size=Decimal("10"),
        ask_size=Decimal("10"),
        observed_at_ms=(
            observed_at_ms
            if observed_at_ms is not None
            else int(
                NOW.timestamp() * 1000
            )
        ),
    )
def build_context(
    quotes,
):
    return TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="ARBITRAGE",
        symbol="BTCUSDT",
        category="spot",
        timeframe="1m",
        config={},
        ticker=build_ticker(),
        arbitrage_quotes=quotes,
        evaluated_at=NOW,
    )
def test_arbitrage_config_defaults():
    config = ArbitrageStrategyConfig()
    assert (
        config.opportunity_type
        == "TRIANGULAR"
    )
    assert config.starting_asset == "USDT"
    assert config.starting_amount == 100
    assert config.exchanges == ["BYBIT"]
    assert config.evaluation_only is True
def test_arbitrage_config_normalizes_identifiers():
    config = ArbitrageStrategyConfig(
        starting_asset=" usdt ",
        exchanges=[
            " bybit ",
            "BYBIT",
        ],
        symbols=[
            " btcusdt ",
            "BTCUSDT",
            "ethusdt",
        ],
    )
    assert config.starting_asset == "USDT"
    assert config.exchanges == ["BYBIT"]
    assert config.symbols == [
        "BTCUSDT",
        "ETHUSDT",
    ]
def test_triangular_requires_one_exchange():
    with pytest.raises(
        ValidationError,
        match="exactly one exchange",
    ):
        ArbitrageStrategyConfig(
            opportunity_type="TRIANGULAR",
            exchanges=[
                "BYBIT",
                "BINANCE",
            ],
        )
def test_cross_exchange_requires_two_exchanges():
    with pytest.raises(
        ValidationError,
        match="at least two exchanges",
    ):
        ArbitrageStrategyConfig(
            opportunity_type=(
                "CROSS_EXCHANGE"
            ),
            exchanges=["BYBIT"],
        )
def test_cross_exchange_accepts_distinct_exchanges():
    config = ArbitrageStrategyConfig(
        opportunity_type=(
            "CROSS_EXCHANGE"
        ),
        exchanges=[
            "bybit",
            "binance",
        ],
    )
    assert config.exchanges == [
        "BYBIT",
        "BINANCE",
    ]
def test_arbitrage_config_is_evaluation_only():
    with pytest.raises(
        ValidationError,
    ):
        ArbitrageStrategyConfig(
            evaluation_only=False
        )
def test_arbitrage_config_rejects_unknown_fields():
    with pytest.raises(
        ValidationError,
        match="Extra inputs",
    ):
        ArbitrageStrategyConfig(
            live_execution=True
        )
def test_context_defaults_empty_quotes():
    context = build_context([])
    assert context.arbitrage_quotes == []
def test_context_accepts_valid_quotes():
    quotes = [
        build_quote(),
        build_quote(
            exchange="BINANCE",
        ),
    ]
    context = build_context(
        quotes
    )
    assert (
        context.arbitrage_quotes
        == quotes
    )
def test_context_rejects_duplicate_market_quotes():
    quotes = [
        build_quote(),
        build_quote(
            bid_price="98",
            ask_price="99",
        ),
    ]
    with pytest.raises(
        ValidationError,
        match="duplicate exchange",
    ):
        build_context(
            quotes
        )
def test_context_rejects_future_quote():
    future_time = int(
        NOW.timestamp() * 1000
    ) + 1
    with pytest.raises(
        ValidationError,
        match="future observations",
    ):
        build_context([
            build_quote(
                observed_at_ms=future_time
            )
        ])
def test_context_allows_unknown_quote_time():
    context = build_context([
        build_quote(
            observed_at_ms=0
        )
    ])
    assert (
        context.arbitrage_quotes[0]
        .observed_at_ms
        == 0
    )
def test_runtime_markets_normalize():
    config = ArbitrageStrategyConfig(
        exchanges=["bybit"],
        markets=[
            {
                "exchange": " bybit ",
                "symbol": " btcusdt ",
                "base_asset": " btc ",
                "quote_asset": " usdt ",
                "fee_rate_percent": 0.1,
            }
        ],
    )
    market = config.markets[0]
    assert market.exchange == "BYBIT"
    assert market.symbol == "BTCUSDT"
    assert market.base_asset == "BTC"
    assert market.quote_asset == "USDT"
def test_runtime_markets_reject_duplicates():
    market = {
        "exchange": "BYBIT",
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
    }
    with pytest.raises(
        ValidationError,
        match="duplicate",
    ):
        ArbitrageStrategyConfig(
            markets=[
                market,
                dict(market),
            ]
        )
def test_runtime_market_exchange_must_be_configured():
    with pytest.raises(
        ValidationError,
        match="included in exchanges",
    ):
        ArbitrageStrategyConfig(
            exchanges=["BYBIT"],
            markets=[
                {
                    "exchange": "BINANCE",
                    "symbol": "BTCUSDT",
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                }
            ],
        )
