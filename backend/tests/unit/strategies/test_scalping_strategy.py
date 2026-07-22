from datetime import (
    UTC,
    datetime,
    timedelta,
)
import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
    TradingBotStrategyContext,
    TradingBotStrategyPositionState,
    TradingBotStrategyState,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
)
from app.strategies.scalping import (
    ScalpingTradingStrategy,
)
NOW = datetime(
    2026,
    7,
    21,
    23,
    0,
    tzinfo=UTC,
)
BASE_CONFIG = {
    "fast_ema_period": 2,
    "slow_ema_period": 4,
    "rsi_period": 3,
    "atr_period": 3,
    "momentum_lookback": 2,
    "minimum_momentum_percent": 0.1,
    "exit_momentum_percent": 0.05,
    "long_rsi_minimum": 50,
    "long_rsi_maximum": 100,
    "short_rsi_minimum": 0,
    "short_rsi_maximum": 50,
    "minimum_atr_percent": 0.01,
    "maximum_atr_percent": 5,
}
def build_history(
    prices,
):
    start = (
        NOW
        - timedelta(
            minutes=(
                len(prices) - 1
            )
        )
    )
    return [
        TradingBotMarketSample(
            observed_at=(
                start
                + timedelta(
                    minutes=index
                )
            ),
            open_price=price,
            high_price=price + 0.5,
            low_price=max(
                price - 0.5,
                0.01,
            ),
            close_price=price,
            volume=100,
            turnover_usd=(
                price * 100
            ),
            source="CANDLE",
        )
        for index, price
        in enumerate(prices)
    ]
def build_ticker(
    *,
    price,
    spread=0.1,
    turnover=100000,
):
    return MarketTickerSnapshot(
        exchange="BACKTEST",
        category="linear",
        symbol="BTCUSDT",
        last_price=price,
        bid_price=price,
        ask_price=price,
        spread=0,
        spread_percent=spread,
        volume_24h=1000,
        turnover_24h=turnover,
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_position(
    *,
    side,
    price,
):
    return (
        TradingBotStrategyPositionState(
            side=side,
            quantity=1,
            average_entry_price=price,
            current_price=price,
            position_value_usd=price,
            unrealized_pnl_usd=0,
            entry_count=1,
            last_entry_price=price,
            opened_at=NOW,
            last_entry_at=NOW,
        )
    )
def build_context(
    *,
    prices,
    config=None,
    position=None,
    spread=0.1,
    turnover=100000,
):
    strategy_config = dict(
        BASE_CONFIG
    )
    if config:
        strategy_config.update(config)
    state = TradingBotStrategyState(
        order_count=(
            1
            if position is not None
            else 0
        ),
        position=position,
    )
    return TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="SCALPING",
        symbol="BTCUSDT",
        category="linear",
        timeframe="1m",
        config=strategy_config,
        ticker=build_ticker(
            price=prices[-1],
            spread=spread,
            turnover=turnover,
        ),
        market_history=(
            build_history(prices)
        ),
        evaluated_at=NOW,
        state=state,
    )
def test_scalping_validates_configuration():
    strategy = ScalpingTradingStrategy()
    config = strategy.validate_config(
        BASE_CONFIG
    )
    assert (
        config["fast_ema_period"]
        == 2
    )
    assert (
        config["atr_period"]
        == 3
    )
    with pytest.raises(
        ValidationError,
        match="fast_ema_period",
    ):
        strategy.validate_config({
            "fast_ema_period": 10,
            "slow_ema_period": 5,
        })
def test_default_registry_contains_scalping():
    registry = (
        TradingBotStrategyRegistry
        .default()
    )
    assert (
        registry.get("SCALPING")
        .strategy_type
        == "SCALPING"
    )
    assert (
        "SCALPING"
        in registry.list_types()
    )
@pytest.mark.asyncio
async def test_scalping_holds_during_warmup():
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    101,
                    102,
                ]
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "sufficient market history"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_scalping_opens_long():
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    101,
                    102,
                    103,
                    104,
                ]
            )
        )
    )
    assert decision.action == "BUY"
    assert (
        decision.metadata["signal"]
        == "BULLISH_SCALP"
    )
@pytest.mark.asyncio
async def test_scalping_opens_short():
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    104,
                    103,
                    102,
                    101,
                    100,
                ]
            )
        )
    )
    assert decision.action == "SELL"
    assert (
        decision.metadata["signal"]
        == "BEARISH_SCALP"
    )
@pytest.mark.asyncio
async def test_scalping_holds_neutral_market():
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    100,
                    100,
                    100,
                    100,
                ]
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        decision.metadata["signal"]
        == "NEUTRAL"
    )
@pytest.mark.asyncio
async def test_scalping_does_not_increase_position():
    prices = [
        100,
        101,
        102,
        103,
        104,
    ]
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=prices,
                position=build_position(
                    side="LONG",
                    price=102,
                ),
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "remains aligned"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_scalping_closes_long_on_reversal():
    prices = [
        104,
        103,
        102,
        101,
        100,
    ]
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=prices,
                position=build_position(
                    side="LONG",
                    price=104,
                ),
            )
        )
    )
    assert decision.action == "SELL"
@pytest.mark.asyncio
async def test_scalping_closes_short_on_reversal():
    prices = [
        100,
        101,
        102,
        103,
        104,
    ]
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=prices,
                position=build_position(
                    side="SHORT",
                    price=100,
                ),
            )
        )
    )
    assert decision.action == "BUY"
@pytest.mark.asyncio
async def test_scalping_respects_direction_mode():
    blocked_long = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    101,
                    102,
                    103,
                    104,
                ],
                config={
                    "direction": "SHORT",
                },
            )
        )
    )
    blocked_short = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    104,
                    103,
                    102,
                    101,
                    100,
                ],
                config={
                    "direction": "LONG",
                },
            )
        )
    )
    assert blocked_long.action == "HOLD"
    assert blocked_short.action == "HOLD"
@pytest.mark.asyncio
async def test_scalping_applies_market_filters():
    strategy = ScalpingTradingStrategy()
    prices = [
        100,
        101,
        102,
        103,
        104,
    ]
    wide_spread = await strategy.evaluate(
        build_context(
            prices=prices,
            config={
                (
                    "maximum_spread_"
                    "percent"
                ): 0.2,
            },
            spread=1,
        )
    )
    low_turnover = await strategy.evaluate(
        build_context(
            prices=prices,
            config={
                (
                    "minimum_turnover_"
                    "24h"
                ): 200000,
            },
            turnover=100000,
        )
    )
    assert wide_spread.action == "HOLD"
    assert low_turnover.action == "HOLD"
@pytest.mark.asyncio
async def test_scalping_filters_low_volatility():
    decision = await (
        ScalpingTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    100.01,
                    100.02,
                    100.03,
                    100.04,
                ],
                config={
                    "minimum_atr_percent": 2,
                },
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        decision.metadata["signal"]
        == "VOLATILITY_FILTERED"
    )
@pytest.mark.asyncio
async def test_scalping_decision_is_deterministic():
    strategy = ScalpingTradingStrategy()
    context = build_context(
        prices=[
            100,
            101,
            102,
            103,
            104,
        ]
    )
    first = await strategy.evaluate(
        context
    )
    second = await strategy.evaluate(
        context
    )
    assert (
        first.model_dump(
            mode="json"
        )
        == second.model_dump(
            mode="json"
        )
    )
