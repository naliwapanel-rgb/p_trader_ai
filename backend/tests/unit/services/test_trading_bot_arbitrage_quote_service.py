from types import (
    SimpleNamespace,
)
import pytest
from app.schemas.market_scanner import (
    MarketTickerBatch,
    MarketTickerSnapshot,
)
from app.services.trading_bot_arbitrage_quote_service import (
    TradingBotArbitrageQuoteService,
)
OBSERVED_AT_MS = 1784718000000
def build_market(
    *,
    symbol,
    base_asset,
    quote_asset,
):
    return {
        "exchange": "BYBIT",
        "symbol": symbol,
        "base_asset": base_asset,
        "quote_asset": quote_asset,
        "fee_rate_percent": 0.1,
        "slippage_percent": 0.05,
    }
def build_config(
    *,
    opportunity_type="TRIANGULAR",
):
    exchanges = (
        ["BYBIT"]
        if opportunity_type
        == "TRIANGULAR"
        else [
            "BYBIT",
            "BINANCE",
        ]
    )
    return {
        "opportunity_type": (
            opportunity_type
        ),
        "starting_asset": "USDT",
        "starting_amount": 100,
        "minimum_profit_percent": 0.1,
        "exchanges": exchanges,
        "markets": [
            build_market(
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
            ),
            build_market(
                symbol="ETHBTC",
                base_asset="ETH",
                quote_asset="BTC",
            ),
            build_market(
                symbol="ETHUSDT",
                base_asset="ETH",
                quote_asset="USDT",
            ),
        ],
    }
def build_bot(
    *,
    category="spot",
    opportunity_type="TRIANGULAR",
):
    return SimpleNamespace(
        category=category,
        strategy_config=build_config(
            opportunity_type=(
                opportunity_type
            )
        ),
    )
def build_account(
    exchange_name="BYBIT",
):
    return SimpleNamespace(
        exchange_name=exchange_name,
    )
def ticker(
    symbol,
    *,
    bid,
    ask,
    bid_size=100,
    ask_size=100,
    observed_at_ms=OBSERVED_AT_MS,
):
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="spot",
        symbol=symbol,
        last_price=ask,
        bid_price=bid,
        bid_size=bid_size,
        ask_price=ask,
        ask_size=ask_size,
        observed_at_ms=observed_at_ms,
    )
def build_batch(
    tickers,
):
    return MarketTickerBatch(
        exchange="BYBIT",
        category="spot",
        observed_at_ms=OBSERVED_AT_MS,
        count=len(tickers),
        tickers=tickers,
    )
def test_builds_triangular_quotes():
    batch = build_batch([
        ticker(
            "BTCUSDT",
            bid=99,
            ask=100,
        ),
        ticker(
            "ETHBTC",
            bid=0.49,
            ask=0.5,
        ),
        ticker(
            "ETHUSDT",
            bid=60,
            ask=61,
        ),
    ])
    quotes = (
        TradingBotArbitrageQuoteService()
        .build_quotes(
            bot=build_bot(),
            account=build_account(),
            batch=batch,
        )
    )
    assert len(quotes) == 3
    assert [
        quote.symbol
        for quote in quotes
    ] == [
        "BTCUSDT",
        "ETHBTC",
        "ETHUSDT",
    ]
    assert (
        str(
            quotes[0]
            .fee_rate_percent
        )
        == "0.1"
    )
def test_missing_market_is_skipped():
    batch = build_batch([
        ticker(
            "BTCUSDT",
            bid=99,
            ask=100,
        ),
        ticker(
            "ETHBTC",
            bid=0.49,
            ask=0.5,
        ),
    ])
    quotes = (
        TradingBotArbitrageQuoteService()
        .build_quotes(
            bot=build_bot(),
            account=build_account(),
            batch=batch,
        )
    )
    assert len(quotes) == 2
def test_invalid_local_quote_is_skipped():
    batch = build_batch([
        ticker(
            "BTCUSDT",
            bid=99,
            ask=100,
        ),
        ticker(
            "ETHBTC",
            bid=0.49,
            ask=0.5,
            bid_size=0,
        ),
        ticker(
            "ETHUSDT",
            bid=60,
            ask=61,
        ),
    ])
    quotes = (
        TradingBotArbitrageQuoteService()
        .build_quotes(
            bot=build_bot(),
            account=build_account(),
            batch=batch,
        )
    )
    assert [
        quote.symbol
        for quote in quotes
    ] == [
        "BTCUSDT",
        "ETHUSDT",
    ]
def test_cross_exchange_is_deferred():
    quotes = (
        TradingBotArbitrageQuoteService()
        .build_quotes(
            bot=build_bot(
                opportunity_type=(
                    "CROSS_EXCHANGE"
                )
            ),
            account=build_account(),
            batch=build_batch([]),
        )
    )
    assert quotes == []
def test_triangular_runtime_requires_spot():
    with pytest.raises(
        ValueError,
        match="spot markets only",
    ):
        (
            TradingBotArbitrageQuoteService()
            .build_quotes(
                bot=build_bot(
                    category="linear"
                ),
                account=build_account(),
                batch=build_batch([]),
            )
        )
