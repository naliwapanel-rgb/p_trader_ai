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
OBSERVED_AT_MS = 1784721600000
def market(
    *,
    exchange,
    symbol="BTCUSDT",
):
    return {
        "exchange": exchange,
        "symbol": symbol,
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "fee_rate_percent": 0.1,
        "slippage_percent": 0.05,
    }
def build_bot(
    *,
    symbols=None,
):
    return SimpleNamespace(
        category="spot",
        strategy_config={
            "opportunity_type": (
                "CROSS_EXCHANGE"
            ),
            "starting_asset": "USDT",
            "starting_amount": 100,
            "minimum_profit_percent": 0.1,
            "exchanges": [
                "BYBIT",
                "BINANCE",
            ],
            "symbols": (
                symbols or []
            ),
            "markets": [
                market(
                    exchange="BYBIT"
                ),
                market(
                    exchange="BINANCE"
                ),
            ],
        },
    )
def build_batch(
    exchange,
    *,
    symbol="BTCUSDT",
):
    ticker = MarketTickerSnapshot(
        exchange=exchange,
        category="spot",
        symbol=symbol,
        last_price=100,
        bid_price=99,
        bid_size=100,
        ask_price=100,
        ask_size=100,
        observed_at_ms=(
            OBSERVED_AT_MS
        ),
    )
    return MarketTickerBatch(
        exchange=exchange,
        category="spot",
        observed_at_ms=(
            OBSERVED_AT_MS
        ),
        count=1,
        tickers=[ticker],
    )
def test_builds_cross_exchange_quotes():
    quotes = (
        TradingBotArbitrageQuoteService()
        .build_cross_exchange_quotes(
            bot=build_bot(),
            batches={
                "BYBIT": build_batch(
                    "BYBIT"
                ),
                "BINANCE": build_batch(
                    "BINANCE"
                ),
            },
        )
    )
    assert len(quotes) == 2
    assert {
        quote.exchange
        for quote in quotes
    } == {
        "BYBIT",
        "BINANCE",
    }
def test_cross_exchange_symbol_filter_is_applied():
    quotes = (
        TradingBotArbitrageQuoteService()
        .build_cross_exchange_quotes(
            bot=build_bot(
                symbols=[
                    "ETHUSDT",
                ]
            ),
            batches={
                "BYBIT": build_batch(
                    "BYBIT"
                ),
                "BINANCE": build_batch(
                    "BINANCE"
                ),
            },
        )
    )
    assert quotes == []
def test_batch_key_must_match_exchange():
    with pytest.raises(
        ValueError,
        match=(
            "does not match its exchange"
        ),
    ):
        (
            TradingBotArbitrageQuoteService()
            .build_cross_exchange_quotes(
                bot=build_bot(),
                batches={
                    "BINANCE": (
                        build_batch(
                            "BYBIT"
                        )
                    ),
                },
            )
        )
