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
from app.strategies.dca import (
    DcaTradingStrategy,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
)
NOW = datetime(
    2026,
    7,
    21,
    19,
    0,
    tzinfo=UTC,
)
def build_ticker(
    *,
    price=100,
    change=0,
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
            change
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
        strategy_type="DCA",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        config=config or {},
        ticker=(
            ticker
            or build_ticker()
        ),
        evaluated_at=NOW,
        state=state,
    )
def test_dca_validates_configuration():
    strategy = DcaTradingStrategy()
    config = strategy.validate_config({
        "direction": "SHORT",
        "entry_spacing_percent": 3,
        "maximum_entries": 4,
    })
    assert config["direction"] == "SHORT"
    assert (
        config["entry_spacing_percent"]
        == 3
    )
    assert config["maximum_entries"] == 4
    with pytest.raises(
        ValidationError,
    ):
        strategy.validate_config({
            "maximum_entries": 0
        })
def test_default_registry_contains_dca():
    registry = (
        TradingBotStrategyRegistry
        .default()
    )
    assert (
        registry.get("DCA")
        .strategy_type
        == "DCA"
    )
    assert "DCA" in registry.list_types()
@pytest.mark.asyncio
async def test_dca_opens_initial_long():
    decision = await (
        DcaTradingStrategy()
        .evaluate(
            build_context()
        )
    )
    assert decision.action == "BUY"
    assert (
        decision.reference_price
        == 100
    )
    assert (
        decision.metadata["direction"]
        == "LONG"
    )
    assert (
        decision.metadata["entry_count"]
        == 0
    )
@pytest.mark.asyncio
async def test_dca_waits_for_initial_threshold():
    context = build_context(
        config={
            (
                "initial_entry_"
                "change_percent_24h"
            ): -2,
        },
        ticker=build_ticker(
            change=-1,
        ),
    )
    decision = await (
        DcaTradingStrategy()
        .evaluate(context)
    )
    assert decision.action == "HOLD"
    context = build_context(
        config={
            (
                "initial_entry_"
                "change_percent_24h"
            ): -2,
        },
        ticker=build_ticker(
            change=-2.5,
        ),
    )
    decision = await (
        DcaTradingStrategy()
        .evaluate(context)
    )
    assert decision.action == "BUY"
@pytest.mark.asyncio
async def test_dca_adds_long_after_spacing():
    position = build_position(
        side="LONG",
        average_entry=100,
        last_entry=98,
        current_price=95,
        entry_count=2,
    )
    decision = await (
        DcaTradingStrategy()
        .evaluate(
            build_context(
                config={
                    (
                        "entry_spacing_"
                        "percent"
                    ): 2,
                },
                ticker=build_ticker(
                    price=95,
                ),
                position=position,
            )
        )
    )
    assert decision.action == "BUY"
    assert (
        decision.metadata[
            "spacing_progress_percent"
        ]
        > 2
    )
    assert (
        decision.metadata["entry_count"]
        == 2
    )
@pytest.mark.asyncio
async def test_dca_holds_before_spacing():
    position = build_position(
        side="LONG",
        last_entry=100,
        current_price=99,
        entry_count=2,
    )
    decision = await (
        DcaTradingStrategy()
        .evaluate(
            build_context(
                config={
                    (
                        "entry_spacing_"
                        "percent"
                    ): 2,
                },
                ticker=build_ticker(
                    price=99,
                ),
                position=position,
            )
        )
    )
    assert decision.action == "HOLD"
@pytest.mark.asyncio
async def test_dca_closes_long_at_profit():
    position = build_position(
        side="LONG",
        average_entry=100,
        last_entry=98,
        current_price=104,
        entry_count=2,
    )
    decision = await (
        DcaTradingStrategy()
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
async def test_dca_respects_maximum_entries():
    position = build_position(
        side="LONG",
        last_entry=100,
        current_price=90,
        entry_count=3,
    )
    decision = await (
        DcaTradingStrategy()
        .evaluate(
            build_context(
                config={
                    "maximum_entries": 3,
                    (
                        "entry_spacing_"
                        "percent"
                    ): 2,
                },
                ticker=build_ticker(
                    price=90,
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
async def test_dca_short_open_add_and_close():
    strategy = DcaTradingStrategy()
    initial = await strategy.evaluate(
        build_context(
            config={
                "direction": "SHORT",
            },
        )
    )
    assert initial.action == "SELL"
    position = build_position(
        side="SHORT",
        average_entry=100,
        last_entry=102,
        current_price=105,
        entry_count=2,
    )
    increase = await strategy.evaluate(
        build_context(
            config={
                "direction": "SHORT",
                (
                    "entry_spacing_"
                    "percent"
                ): 2,
            },
            ticker=build_ticker(
                price=105,
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
async def test_dca_rejects_position_direction_mismatch():
    position = build_position(
        side="SHORT",
        average_entry=100,
        last_entry=100,
        current_price=105,
    )
    decision = await (
        DcaTradingStrategy()
        .evaluate(
            build_context(
                config={
                    "direction": "LONG",
                },
                ticker=build_ticker(
                    price=105,
                ),
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
async def test_dca_applies_market_filters():
    strategy = DcaTradingStrategy()
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
async def test_dca_decision_is_deterministic():
    strategy = DcaTradingStrategy()
    context = build_context(
        config={
            (
                "entry_spacing_"
                "percent"
            ): 2,
            "maximum_entries": 5,
        },
        ticker=build_ticker(
            price=95,
        ),
        position=build_position(
            last_entry=100,
            current_price=95,
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
