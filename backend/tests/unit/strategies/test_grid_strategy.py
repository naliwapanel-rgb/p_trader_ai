from datetime import (
    UTC,
    datetime,
)
import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyContext,
    TradingBotStrategyPositionState,
    TradingBotStrategyState,
)
from app.strategies.grid import (
    GridTradingStrategy,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
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
    *,
    price=100,
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
        previous_price_24h=100,
        price_change_24h=(
            price - 100
        ),
        price_change_percent_24h=(
            price - 100
        ),
        high_24h=max(
            price,
            100,
        ),
        low_24h=min(
            price,
            100,
        ),
        volume_24h=1000,
        turnover_24h=turnover,
        observed_at_ms=1,
    )
def build_position(
    *,
    side="LONG",
    average_entry=100,
    last_entry=100,
    current_price=100,
    entry_count=1,
):
    profit = (
        current_price
        - average_entry
        if side == "LONG"
        else average_entry
        - current_price
    )
    return (
        TradingBotStrategyPositionState(
            side=side,
            quantity=1,
            average_entry_price=(
                average_entry
            ),
            current_price=current_price,
            position_value_usd=(
                current_price
            ),
            unrealized_pnl_usd=profit,
            entry_count=entry_count,
            last_entry_price=(
                last_entry
            ),
            opened_at=NOW,
            last_entry_at=NOW,
        )
    )
def build_context(
    *,
    config=None,
    ticker=None,
    position=None,
):
    strategy_config = {
        "lower_price": 90,
        "upper_price": 110,
        "grid_levels": 11,
        "maximum_entries": 5,
    }
    if config:
        strategy_config.update(config)
    state = TradingBotStrategyState(
        order_count=(
            position.entry_count
            if position is not None
            else 0
        ),
        position=position,
    )
    return TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="GRID",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        config=strategy_config,
        ticker=(
            ticker
            or build_ticker()
        ),
        evaluated_at=NOW,
        state=state,
    )
def test_grid_validates_configuration():
    strategy = GridTradingStrategy()
    config = strategy.validate_config({
        "direction": "SHORT",
        "lower_price": 90,
        "upper_price": 110,
        "grid_levels": 11,
        "maximum_entries": 4,
    })
    assert config["direction"] == "SHORT"
    assert config["grid_levels"] == 11
    assert config["maximum_entries"] == 4
    with pytest.raises(
        ValidationError,
    ):
        strategy.validate_config({
            "lower_price": 110,
            "upper_price": 90,
        })
def test_default_registry_contains_grid():
    registry = (
        TradingBotStrategyRegistry
        .default()
    )
    assert (
        registry.get("GRID")
        .strategy_type
        == "GRID"
    )
    assert "GRID" in registry.list_types()
@pytest.mark.asyncio
async def test_grid_opens_initial_long_in_range():
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context()
        )
    )
    assert decision.action == "BUY"
    assert (
        decision.metadata[
            "grid_spacing_usd"
        ]
        == pytest.approx(2)
    )
    assert (
        decision.metadata[
            "current_grid_index"
        ]
        == 5
    )
@pytest.mark.asyncio
async def test_grid_holds_outside_range():
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context(
                ticker=build_ticker(
                    price=120,
                )
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "outside"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_grid_adds_long_at_next_level():
    position = build_position(
        side="LONG",
        average_entry=100,
        last_entry=100,
        current_price=97,
        entry_count=2,
    )
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context(
                ticker=build_ticker(
                    price=97,
                ),
                position=position,
            )
        )
    )
    assert decision.action == "BUY"
    assert (
        decision.metadata[
            "next_entry_price"
        ]
        == pytest.approx(98)
    )
@pytest.mark.asyncio
async def test_grid_holds_before_next_level():
    position = build_position(
        side="LONG",
        last_entry=100,
        current_price=99,
        entry_count=2,
    )
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context(
                ticker=build_ticker(
                    price=99,
                ),
                position=position,
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        decision.metadata[
            "next_entry_price"
        ]
        == pytest.approx(98)
    )
@pytest.mark.asyncio
async def test_grid_closes_long_at_profit():
    position = build_position(
        side="LONG",
        average_entry=100,
        last_entry=98,
        current_price=104,
        entry_count=2,
    )
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context(
                config={
                    (
                        "take_profit_"
                        "percent"
                    ): 3,
                },
                ticker=build_ticker(
                    price=104,
                ),
                position=position,
            )
        )
    )
    assert decision.action == "SELL"
    assert (
        decision.metadata[
            "position_profit_percent"
        ]
        == pytest.approx(4)
    )
@pytest.mark.asyncio
async def test_grid_respects_maximum_entries():
    position = build_position(
        side="LONG",
        last_entry=100,
        current_price=95,
        entry_count=3,
    )
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context(
                config={
                    "maximum_entries": 3,
                },
                ticker=build_ticker(
                    price=95,
                ),
                position=position,
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "maximum entry count"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_grid_short_open_add_and_close():
    strategy = GridTradingStrategy()
    initial = await strategy.evaluate(
        build_context(
            config={
                "direction": "SHORT",
            }
        )
    )
    assert initial.action == "SELL"
    position = build_position(
        side="SHORT",
        average_entry=100,
        last_entry=100,
        current_price=103,
        entry_count=2,
    )
    increase = await strategy.evaluate(
        build_context(
            config={
                "direction": "SHORT",
            },
            ticker=build_ticker(
                price=103,
            ),
            position=position,
        )
    )
    assert increase.action == "SELL"
    profitable_position = (
        build_position(
            side="SHORT",
            average_entry=100,
            last_entry=102,
            current_price=96,
            entry_count=2,
        )
    )
    close = await strategy.evaluate(
        build_context(
            config={
                "direction": "SHORT",
                (
                    "take_profit_"
                    "percent"
                ): 3,
            },
            ticker=build_ticker(
                price=96,
            ),
            position=(
                profitable_position
            ),
        )
    )
    assert close.action == "BUY"
@pytest.mark.asyncio
async def test_grid_rejects_position_direction_mismatch():
    position = build_position(
        side="SHORT",
        current_price=100,
    )
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context(
                config={
                    "direction": "LONG",
                },
                position=position,
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "does not match"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_grid_applies_market_filters():
    strategy = GridTradingStrategy()
    wide_spread = await strategy.evaluate(
        build_context(
            config={
                (
                    "maximum_spread_"
                    "percent"
                ): 0.5,
            },
            ticker=build_ticker(
                spread=1,
            ),
        )
    )
    assert wide_spread.action == "HOLD"
    low_turnover = await strategy.evaluate(
        build_context(
            config={
                (
                    "minimum_turnover_"
                    "24h"
                ): 200000,
            },
            ticker=build_ticker(
                turnover=100000,
            ),
        )
    )
    assert low_turnover.action == "HOLD"
@pytest.mark.asyncio
async def test_grid_does_not_add_below_range():
    position = build_position(
        side="LONG",
        last_entry=92,
        current_price=85,
        entry_count=2,
    )
    decision = await (
        GridTradingStrategy()
        .evaluate(
            build_context(
                ticker=build_ticker(
                    price=85,
                ),
                position=position,
            )
        )
    )
    assert decision.action == "HOLD"
    assert (
        "outside"
        in decision.reason
    )
@pytest.mark.asyncio
async def test_grid_decision_is_deterministic():
    strategy = GridTradingStrategy()
    context = build_context(
        ticker=build_ticker(
            price=97,
        ),
        position=build_position(
            last_entry=100,
            current_price=97,
            entry_count=2,
        ),
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
