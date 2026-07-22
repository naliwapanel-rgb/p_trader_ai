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
    TradingBotStrategyContext,
)
from app.strategies.arbitrage import (
    ArbitrageTradingStrategy,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
)
NOW = datetime(
    2026,
    7,
    22,
    10,
    0,
    tzinfo=UTC,
)
def quote(
    *,
    exchange,
    symbol,
    base_asset,
    quote_asset,
    bid,
    ask,
):
    return ArbitrageMarketQuote(
        exchange=exchange,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        bid_price=Decimal(
            str(bid)
        ),
        ask_price=Decimal(
            str(ask)
        ),
        bid_size=Decimal("100"),
        ask_size=Decimal("100"),
        fee_rate_percent=Decimal("0"),
        slippage_percent=Decimal("0"),
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def triangular_quotes():
    return [
        quote(
            exchange="BYBIT",
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            bid=99,
            ask=100,
        ),
        quote(
            exchange="BYBIT",
            symbol="ETHBTC",
            base_asset="ETH",
            quote_asset="BTC",
            bid=0.49,
            ask=0.5,
        ),
        quote(
            exchange="BYBIT",
            symbol="ETHUSDT",
            base_asset="ETH",
            quote_asset="USDT",
            bid=60,
            ask=61,
        ),
    ]
def cross_exchange_quotes():
    return [
        quote(
            exchange="BYBIT",
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            bid=99,
            ask=100,
        ),
        quote(
            exchange="BINANCE",
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            bid=110,
            ask=111,
        ),
    ]
def build_ticker():
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="spot",
        symbol="BTCUSDT",
        last_price=100,
        bid_price=99,
        bid_size=100,
        ask_price=100,
        ask_size=100,
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_context(
    *,
    quotes,
    config,
):
    return TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="ARBITRAGE",
        symbol="BTCUSDT",
        category="spot",
        timeframe="1m",
        config=config,
        ticker=build_ticker(),
        arbitrage_quotes=quotes,
        evaluated_at=NOW,
    )
def triangular_config(
    **updates,
):
    config = {
        "opportunity_type": (
            "TRIANGULAR"
        ),
        "starting_asset": "USDT",
        "starting_amount": 100,
        "minimum_profit_percent": 1,
        "exchanges": ["BYBIT"],
        "maximum_quote_age_ms": None,
        "maximum_time_skew_ms": None,
        "require_full_liquidity": True,
        "evaluation_only": True,
    }
    config.update(updates)
    return config
def cross_config(
    **updates,
):
    config = {
        "opportunity_type": (
            "CROSS_EXCHANGE"
        ),
        "starting_asset": "USDT",
        "starting_amount": 100,
        "minimum_profit_percent": 1,
        "exchanges": [
            "BYBIT",
            "BINANCE",
        ],
        "maximum_quote_age_ms": None,
        "maximum_time_skew_ms": None,
        "require_full_liquidity": True,
        "evaluation_only": True,
    }
    config.update(updates)
    return config
def test_arbitrage_validates_configuration():
    strategy = ArbitrageTradingStrategy()
    config = strategy.validate_config(
        triangular_config()
    )
    assert (
        config["opportunity_type"]
        == "TRIANGULAR"
    )
    assert (
        config["evaluation_only"]
        is True
    )
    with pytest.raises(
        ValidationError,
        match="at least two exchanges",
    ):
        strategy.validate_config({
            "opportunity_type": (
                "CROSS_EXCHANGE"
            ),
            "exchanges": ["BYBIT"],
        })
def test_default_registry_contains_arbitrage():
    registry = (
        TradingBotStrategyRegistry
        .default()
    )
    assert (
        registry.get("ARBITRAGE")
        .strategy_type
        == "ARBITRAGE"
    )
    assert (
        "ARBITRAGE"
        in registry.list_types()
    )
@pytest.mark.asyncio
async def test_arbitrage_holds_without_quotes():
    decision = await (
        ArbitrageTradingStrategy()
        .evaluate(
            build_context(
                quotes=[],
                config=(
                    triangular_config()
                ),
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "waiting for matching"
        in decision.reason
    )
    assert (
        decision.metadata[
            "opportunity_detected"
        ]
        is False
    )
@pytest.mark.asyncio
async def test_detects_triangular_opportunity():
    decision = await (
        ArbitrageTradingStrategy()
        .evaluate(
            build_context(
                quotes=(
                    triangular_quotes()
                ),
                config=(
                    triangular_config()
                ),
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        decision.metadata[
            "opportunity_detected"
        ]
        is True
    )
    assert (
        decision.metadata[
            "opportunity_type"
        ]
        == "TRIANGULAR"
    )
    assert (
        decision.metadata[
            "best_net_profit_percent"
        ]
        > 0
    )
@pytest.mark.asyncio
async def test_detects_cross_exchange_opportunity():
    decision = await (
        ArbitrageTradingStrategy()
        .evaluate(
            build_context(
                quotes=(
                    cross_exchange_quotes()
                ),
                config=cross_config(),
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        decision.metadata[
            "opportunity_detected"
        ]
        is True
    )
    best = decision.metadata[
        "best_opportunity"
    ]
    assert (
        best["buy_exchange"]
        == "BYBIT"
    )
    assert (
        best["sell_exchange"]
        == "BINANCE"
    )
@pytest.mark.asyncio
async def test_holds_when_profit_limit_is_not_met():
    decision = await (
        ArbitrageTradingStrategy()
        .evaluate(
            build_context(
                quotes=(
                    cross_exchange_quotes()
                ),
                config=cross_config(
                    minimum_profit_percent=50
                ),
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        decision.metadata[
            "opportunity_detected"
        ]
        is False
    )
    assert (
        decision.metadata[
            "matched_count"
        ]
        == 0
    )
@pytest.mark.asyncio
async def test_symbol_filter_is_applied():
    decision = await (
        ArbitrageTradingStrategy()
        .evaluate(
            build_context(
                quotes=(
                    triangular_quotes()
                ),
                config=(
                    triangular_config(
                        symbols=[
                            "BTCUSDT",
                            "ETHBTC",
                        ]
                    )
                ),
            )
        )
    )
    assert (
        decision.metadata[
            "filtered_quote_count"
        ]
        == 2
    )
    assert (
        decision.metadata[
            "opportunity_detected"
        ]
        is False
    )
    assert (
        decision.metadata[
            "required_quote_count"
        ]
        == 3
    )
    assert (
        decision.metadata[
            "matched_count"
        ]
        == 0
    )
    assert (
        "sufficient matching"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_exchange_filter_is_applied():
    quotes = (
        triangular_quotes()
        + [
            quote(
                exchange="BINANCE",
                symbol="SOLUSDT",
                base_asset="SOL",
                quote_asset="USDT",
                bid=50,
                ask=51,
            )
        ]
    )
    decision = await (
        ArbitrageTradingStrategy()
        .evaluate(
            build_context(
                quotes=quotes,
                config=(
                    triangular_config()
                ),
            )
        )
    )
    assert (
        decision.metadata[
            "received_quote_count"
        ]
        == 4
    )
    assert (
        decision.metadata[
            "filtered_quote_count"
        ]
        == 3
    )
@pytest.mark.asyncio
async def test_opportunity_remains_evaluation_only():
    decision = await (
        ArbitrageTradingStrategy()
        .evaluate(
            build_context(
                quotes=(
                    cross_exchange_quotes()
                ),
                config=cross_config(),
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        decision.metadata[
            "evaluation_only"
        ]
        is True
    )
    assert (
        "evaluation-only"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_arbitrage_decision_is_deterministic():
    strategy = ArbitrageTradingStrategy()
    context = build_context(
        quotes=triangular_quotes(),
        config=triangular_config(),
    )
    first = await strategy.evaluate(
        context
    )
    second = await strategy.evaluate(
        context
    )
    first_dump = first.model_dump(
        mode="json"
    )
    second_dump = second.model_dump(
        mode="json"
    )
    first_dump["metadata"].pop(
        "scanned_at_ms",
        None,
    )
    second_dump["metadata"].pop(
        "scanned_at_ms",
        None,
    )
    assert first_dump == second_dump
