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
    DcaStrategyConfig,
    GridStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyPositionState,
    TradingBotStrategyState,
)
NOW = datetime(
    2026,
    7,
    21,
    18,
    0,
    tzinfo=UTC,
)
def build_ticker():
    return MarketTickerSnapshot(
        exchange="BACKTEST",
        category="linear",
        symbol="BTCUSDT",
        last_price=100,
        bid_price=100,
        ask_price=100,
        spread=0,
        spread_percent=0,
        volume_24h=1000,
        turnover_24h=100000,
        observed_at_ms=1,
    )
def build_position():
    return TradingBotStrategyPositionState(
        side="LONG",
        quantity=1,
        average_entry_price=100,
        current_price=98,
        position_value_usd=98,
        unrealized_pnl_usd=-2,
        entry_count=2,
        last_entry_price=98,
        opened_at=NOW,
        last_entry_at=NOW,
    )
def test_dca_config_defaults():
    config = DcaStrategyConfig()
    assert config.direction == "LONG"
    assert (
        config.entry_spacing_percent
        == 2
    )
    assert config.maximum_entries == 5
    assert (
        config.take_profit_percent
        == 3
    )
    assert (
        config
        .initial_entry_change_percent_24h
        is None
    )
def test_dca_config_bounds_entries():
    with pytest.raises(
        ValidationError,
    ):
        DcaStrategyConfig(
            maximum_entries=0
        )
    with pytest.raises(
        ValidationError,
    ):
        DcaStrategyConfig(
            maximum_entries=51
        )
def test_dca_config_rejects_unknown_fields():
    with pytest.raises(
        ValidationError,
    ):
        DcaStrategyConfig(
            live_execution=True
        )
def test_grid_config_defaults():
    config = GridStrategyConfig(
        lower_price=90,
        upper_price=110,
    )
    assert config.direction == "LONG"
    assert config.grid_levels == 10
    assert config.maximum_entries == 5
    assert config.take_profit_percent == 2
def test_grid_rejects_invalid_range():
    with pytest.raises(
        ValidationError,
        match="lower_price",
    ):
        GridStrategyConfig(
            lower_price=110,
            upper_price=100,
        )
def test_grid_rejects_excess_entries():
    with pytest.raises(
        ValidationError,
        match="maximum_entries",
    ):
        GridStrategyConfig(
            lower_price=90,
            upper_price=110,
            grid_levels=4,
            maximum_entries=5,
        )
def test_strategy_state_defaults_empty():
    state = TradingBotStrategyState()
    assert state.order_count == 0
    assert (
        state.completed_trade_count
        == 0
    )
    assert state.position is None
    assert state.last_order_action is None
def test_strategy_state_accepts_position():
    state = TradingBotStrategyState(
        order_count=2,
        last_order_action="BUY",
        last_order_reference_price=98,
        last_order_at=NOW,
        position=build_position(),
    )
    assert state.position is not None
    assert (
        state.position.entry_count
        == 2
    )
    assert (
        state.position.last_entry_price
        == 98
    )
def test_state_requires_complete_last_order():
    with pytest.raises(
        ValidationError,
        match="provided together",
    ):
        TradingBotStrategyState(
            last_order_action="BUY",
        )
def test_state_rejects_low_order_count():
    with pytest.raises(
        ValidationError,
        match="entry_count",
    ):
        TradingBotStrategyState(
            order_count=1,
            position=build_position(),
        )
def test_context_defaults_empty_state():
    context = TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="DCA",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        config={},
        ticker=build_ticker(),
        evaluated_at=NOW,
    )
    assert context.state.order_count == 0
    assert context.state.position is None
def test_context_accepts_strategy_state():
    state = TradingBotStrategyState(
        order_count=2,
        last_order_action="BUY",
        last_order_reference_price=98,
        last_order_at=NOW,
        position=build_position(),
    )
    context = TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="DCA",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        config={},
        ticker=build_ticker(),
        evaluated_at=NOW,
        state=state,
    )
    assert context.state == state
