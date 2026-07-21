from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyState,
)
from app.services.trading_bot_strategy_state_service import (
    TradingBotStrategyStateService,
)
NOW = datetime(
    2026,
    7,
    21,
    21,
    0,
    tzinfo=UTC,
)
def build_bot():
    return SimpleNamespace(
        id=10,
        user_id=7,
        symbol="BTCUSDT",
    )
def build_order(
    *,
    order_id,
    position_id,
    action,
    effect,
    price,
    filled_at,
):
    return SimpleNamespace(
        id=order_id,
        paper_position_id=position_id,
        side=action,
        position_effect=effect,
        reference_price=price,
        filled_at=filled_at,
    )
def build_position(
    *,
    position_id=21,
    side="LONG",
    quantity=2,
    average_entry=98,
):
    return SimpleNamespace(
        id=position_id,
        side=side,
        quantity=quantity,
        average_entry_price=(
            average_entry
        ),
        opened_at=(
            NOW
            - timedelta(hours=3)
        ),
    )
def build_service(
    repository,
):
    return TradingBotStrategyStateService(
        MagicMock(),
        repository=repository,
    )
def test_missing_account_returns_empty_state():
    repository = MagicMock()
    repository.get_account_by_bot.return_value = (
        None
    )
    state = build_service(
        repository
    ).build_from_paper_ledger(
        bot=build_bot(),
        current_price=100,
    )
    assert state == (
        TradingBotStrategyState()
    )
    repository.list_orders.assert_not_called()
def test_closed_ledger_state_without_position():
    repository = MagicMock()
    repository.get_account_by_bot.return_value = (
        SimpleNamespace(id=20)
    )
    close_order = build_order(
        order_id=40,
        position_id=21,
        action="SELL",
        effect="CLOSE",
        price=105,
        filled_at=NOW,
    )
    repository.list_orders.return_value = [
        close_order
    ]
    repository.count_orders.return_value = 4
    repository.count_positions.return_value = 2
    repository.get_open_position.return_value = (
        None
    )
    state = build_service(
        repository
    ).build_from_paper_ledger(
        bot=build_bot(),
        current_price=105,
    )
    assert state.order_count == 4
    assert (
        state.completed_trade_count
        == 2
    )
    assert state.position is None
    assert (
        state.last_order_action
        == "SELL"
    )
    assert (
        state.last_order_reference_price
        == 105
    )
def test_open_long_state_uses_current_cycle_entries():
    repository = MagicMock()
    repository.get_account_by_bot.return_value = (
        SimpleNamespace(id=20)
    )
    orders = [
        build_order(
            order_id=32,
            position_id=21,
            action="BUY",
            effect="INCREASE",
            price=95,
            filled_at=NOW,
        ),
        build_order(
            order_id=31,
            position_id=21,
            action="BUY",
            effect="OPEN",
            price=100,
            filled_at=(
                NOW
                - timedelta(hours=1)
            ),
        ),
        build_order(
            order_id=20,
            position_id=18,
            action="SELL",
            effect="CLOSE",
            price=110,
            filled_at=(
                NOW
                - timedelta(days=1)
            ),
        ),
    ]
    repository.list_orders.return_value = (
        orders
    )
    repository.count_orders.return_value = 3
    repository.count_positions.return_value = 1
    repository.get_open_position.return_value = (
        build_position()
    )
    state = build_service(
        repository
    ).build_from_paper_ledger(
        bot=build_bot(),
        current_price=94,
    )
    position = state.position
    assert position is not None
    assert position.side == "LONG"
    assert position.entry_count == 2
    assert (
        position.last_entry_price
        == 95
    )
    assert position.current_price == 94
    assert position.position_value_usd == 188
    assert (
        position.unrealized_pnl_usd
        == pytest.approx(-8)
    )
def test_open_short_state_calculates_profit():
    repository = MagicMock()
    repository.get_account_by_bot.return_value = (
        SimpleNamespace(id=20)
    )
    repository.list_orders.return_value = [
        build_order(
            order_id=31,
            position_id=21,
            action="SELL",
            effect="OPEN",
            price=100,
            filled_at=NOW,
        )
    ]
    repository.count_orders.return_value = 1
    repository.count_positions.return_value = 0
    repository.get_open_position.return_value = (
        build_position(
            side="SHORT",
            quantity=3,
            average_entry=100,
        )
    )
    state = build_service(
        repository
    ).build_from_paper_ledger(
        bot=build_bot(),
        current_price=96,
    )
    assert state.position is not None
    assert (
        state.position
        .unrealized_pnl_usd
        == pytest.approx(12)
    )
def test_missing_entry_order_uses_position_fallback():
    repository = MagicMock()
    repository.get_account_by_bot.return_value = (
        SimpleNamespace(id=20)
    )
    repository.list_orders.return_value = []
    repository.count_orders.return_value = 1
    repository.count_positions.return_value = 0
    position = build_position(
        average_entry=101,
    )
    repository.get_open_position.return_value = (
        position
    )
    state = build_service(
        repository
    ).build_from_paper_ledger(
        bot=build_bot(),
        current_price=100,
    )
    assert state.position is not None
    assert state.position.entry_count == 1
    assert (
        state.position.last_entry_price
        == 101
    )
    assert (
        state.position.last_entry_at
        == position.opened_at
    )
