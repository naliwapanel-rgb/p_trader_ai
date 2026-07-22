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
from app.strategies.mean_reversion import (
    MeanReversionTradingStrategy,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
)
NOW = datetime(
    2026,
    7,
    21,
    22,
    0,
    tzinfo=UTC,
)
BASE_CONFIG = {
    "lookback_period": 5,
    "rsi_period": 3,
    "entry_z_score": 1.0,
    "exit_z_score": 0.25,
    "oversold_rsi": 35,
    "overbought_rsi": 65,
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
            high_price=price + 1,
            low_price=max(
                price - 1,
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
        strategy_type="MEAN_REVERSION",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
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
def test_mean_reversion_validates_configuration():
    strategy = (
        MeanReversionTradingStrategy()
    )
    config = strategy.validate_config(
        BASE_CONFIG
    )
    assert (
        config["lookback_period"]
        == 5
    )
    assert config["rsi_period"] == 3
    with pytest.raises(
        ValidationError,
        match="exit_z_score",
    ):
        strategy.validate_config({
            "entry_z_score": 1,
            "exit_z_score": 2,
        })
def test_default_registry_contains_mean_reversion():
    registry = (
        TradingBotStrategyRegistry
        .default()
    )
    assert (
        registry.get(
            "MEAN_REVERSION"
        ).strategy_type
        == "MEAN_REVERSION"
    )
    assert (
        "MEAN_REVERSION"
        in registry.list_types()
    )
@pytest.mark.asyncio
async def test_mean_reversion_holds_during_warmup():
    decision = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    99,
                    98,
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
async def test_mean_reversion_opens_long():
    decision = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    100,
                    100,
                    100,
                    90,
                ]
            )
        )
    )
    assert decision.action == "BUY"
    assert (
        decision.metadata["signal"]
        == "OVERSOLD"
    )
    assert (
        decision.metadata["z_score"]
        <= -1
    )
@pytest.mark.asyncio
async def test_mean_reversion_opens_short():
    decision = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    100,
                    100,
                    100,
                    110,
                ]
            )
        )
    )
    assert decision.action == "SELL"
    assert (
        decision.metadata["signal"]
        == "OVERBOUGHT"
    )
    assert (
        decision.metadata["z_score"]
        >= 1
    )
@pytest.mark.asyncio
async def test_mean_reversion_holds_neutral_market():
    decision = await (
        MeanReversionTradingStrategy()
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
async def test_mean_reversion_closes_long_after_reversion():
    prices = [
        90,
        92,
        94,
        98,
        100,
    ]
    decision = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=prices,
                position=build_position(
                    side="LONG",
                    price=90,
                ),
            )
        )
    )
    assert decision.action == "SELL"
    assert (
        "reverted"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_mean_reversion_closes_short_after_reversion():
    prices = [
        110,
        108,
        106,
        102,
        100,
    ]
    decision = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=prices,
                position=build_position(
                    side="SHORT",
                    price=110,
                ),
            )
        )
    )
    assert decision.action == "BUY"
@pytest.mark.asyncio
async def test_mean_reversion_holds_position_before_exit():
    prices = [
        100,
        100,
        100,
        95,
        92,
    ]
    decision = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=prices,
                position=build_position(
                    side="LONG",
                    price=90,
                ),
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "has not reached"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_mean_reversion_respects_direction():
    long_blocked = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    100,
                    100,
                    100,
                    90,
                ],
                config={
                    "direction": "SHORT",
                },
            )
        )
    )
    short_blocked = await (
        MeanReversionTradingStrategy()
        .evaluate(
            build_context(
                prices=[
                    100,
                    100,
                    100,
                    100,
                    110,
                ],
                config={
                    "direction": "LONG",
                },
            )
        )
    )
    assert long_blocked.action == "HOLD"
    assert short_blocked.action == "HOLD"
@pytest.mark.asyncio
async def test_mean_reversion_applies_market_filters():
    strategy = (
        MeanReversionTradingStrategy()
    )
    prices = [
        100,
        100,
        100,
        100,
        90,
    ]
    wide_spread = await strategy.evaluate(
        build_context(
            prices=prices,
            config={
                (
                    "maximum_spread_"
                    "percent"
                ): 0.5,
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
async def test_mean_reversion_decision_is_deterministic():
    strategy = (
        MeanReversionTradingStrategy()
    )
    context = build_context(
        prices=[
            100,
            100,
            100,
            100,
            90,
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
