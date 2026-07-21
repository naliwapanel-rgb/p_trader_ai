from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.services.paper_trading_history_service import (
    PaperTradingHistoryService,
)
NOW = datetime(
    2026,
    7,
    21,
    18,
    0,
    tzinfo=UTC,
)
def build_account():
    return SimpleNamespace(
        id=20,
        user_id=7,
        trading_bot_id=10,
        currency="USDT",
        initial_balance_usd=10000.0,
        cash_balance_usd=9970.0,
        reserved_balance_usd=25.0,
        equity_usd=10006.5,
        realized_pnl_usd=8.0,
        unrealized_pnl_usd=3.0,
        total_fees_usd=4.5,
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
def build_position(
    *,
    position_id: int,
    status: str,
    realized_pnl: float,
    fees: float,
):
    return SimpleNamespace(
        id=position_id,
        user_id=7,
        trading_bot_id=10,
        paper_account_id=20,
        symbol="BTCUSDT",
        category="linear",
        side="LONG",
        status=status,
        quantity=1.0,
        average_entry_price=100.0,
        current_price=105.0,
        position_value_usd=(
            0.0
            if status == "CLOSED"
            else 105.0
        ),
        reserved_margin_usd=(
            0.0
            if status == "CLOSED"
            else 100.0
        ),
        unrealized_pnl_usd=(
            0.0
            if status == "CLOSED"
            else 3.0
        ),
        realized_pnl_usd=(
            realized_pnl
        ),
        total_fees_usd=fees,
        opened_at=NOW,
        closed_at=(
            NOW
            if status == "CLOSED"
            else None
        ),
        created_at=NOW,
        updated_at=NOW,
    )
def build_order():
    return SimpleNamespace(
        id=30,
        user_id=7,
        trading_bot_id=10,
        paper_account_id=20,
        paper_position_id=21,
        symbol="BTCUSDT",
        category="linear",
        side="BUY",
        position_effect="OPEN",
        status="FILLED",
        quantity=1.0,
        reference_price=100.0,
        fill_price=100.01,
        gross_value_usd=100.01,
        fee_rate=0.0006,
        fee_usd=0.06,
        slippage_rate=0.0001,
        slippage_usd=0.01,
        realized_pnl_usd=0.0,
        decision_reason="Test order",
        filled_at=NOW,
        created_at=NOW,
    )
def build_service(
    *,
    account=None,
):
    bot = SimpleNamespace(
        id=10,
        user_id=7,
    )
    user = SimpleNamespace(
        id=7,
    )
    bot_service = MagicMock()
    bot_service.get_bot.return_value = bot
    repository = MagicMock()
    repository.get_account_by_bot.return_value = (
        account
    )
    service = PaperTradingHistoryService(
        MagicMock(),
        bot_service=bot_service,
        repository=repository,
    )
    return (
        service,
        user,
        bot_service,
        repository,
    )
def test_missing_paper_account_is_rejected():
    (
        service,
        user,
        _,
        _,
    ) = build_service(
        account=None
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        service.get_account_summary(
            current_user=user,
            bot_id=10,
        )
    assert (
        error.value.status_code
        == 404
    )
    assert (
        error.value.detail
        == "Paper trading account not found"
    )
def test_account_summary_is_bot_scoped():
    account = build_account()
    (
        service,
        user,
        bot_service,
        repository,
    ) = build_service(
        account=account
    )
    result = service.get_account_summary(
        current_user=user,
        bot_id=10,
    )
    assert result.bot_id == 10
    assert result.account.id == 20
    assert result.account.equity_usd == 10006.5
    bot_service.get_bot.assert_called_once_with(
        current_user=user,
        bot_id=10,
    )
    repository.get_account_by_bot.assert_called_once_with(
        user_id=7,
        trading_bot_id=10,
    )
def test_order_history_is_paginated():
    account = build_account()
    (
        service,
        user,
        _,
        repository,
    ) = build_service(
        account=account
    )
    repository.list_orders.return_value = [
        build_order()
    ]
    repository.count_orders.return_value = 8
    result = service.list_orders(
        current_user=user,
        bot_id=10,
        limit=2,
        offset=4,
    )
    assert result.total_count == 8
    assert result.limit == 2
    assert result.offset == 4
    assert len(result.items) == 1
    repository.list_orders.assert_called_once_with(
        paper_account_id=20,
        limit=2,
        offset=4,
    )
def test_position_history_supports_status_filter():
    account = build_account()
    (
        service,
        user,
        _,
        repository,
    ) = build_service(
        account=account
    )
    repository.list_positions.return_value = [
        build_position(
            position_id=21,
            status="CLOSED",
            realized_pnl=5,
            fees=1,
        )
    ]
    repository.count_positions.return_value = 3
    result = service.list_positions(
        current_user=user,
        bot_id=10,
        position_status="CLOSED",
        limit=10,
        offset=0,
    )
    assert result.position_status == "CLOSED"
    assert result.total_count == 3
    assert result.items[0].status == "CLOSED"
    repository.list_positions.assert_called_once_with(
        paper_account_id=20,
        status="CLOSED",
        limit=10,
        offset=0,
    )
def test_performance_calculates_closed_trade_metrics():
    account = build_account()
    (
        service,
        user,
        _,
        repository,
    ) = build_service(
        account=account
    )
    repository.list_positions.return_value = [
        build_position(
            position_id=21,
            status="CLOSED",
            realized_pnl=12,
            fees=2,
        ),
        build_position(
            position_id=22,
            status="CLOSED",
            realized_pnl=-5,
            fees=1,
        ),
        build_position(
            position_id=23,
            status="CLOSED",
            realized_pnl=1,
            fees=1,
        ),
        build_position(
            position_id=24,
            status="OPEN",
            realized_pnl=0,
            fees=0.5,
        ),
    ]
    repository.count_orders.return_value = 7
    result = service.get_performance(
        current_user=user,
        bot_id=10,
    )
    assert result.order_count == 7
    assert result.trade_count == 4
    assert result.completed_trade_count == 3
    assert result.open_trade_count == 1
    assert result.winning_trade_count == 1
    assert result.losing_trade_count == 1
    assert result.breakeven_trade_count == 1
    assert (
        result.gross_realized_pnl_usd
        == pytest.approx(8)
    )
    assert (
        result.realized_fees_usd
        == pytest.approx(4)
    )
    assert (
        result.net_realized_pnl_usd
        == pytest.approx(4)
    )
    assert (
        result.gross_profit_usd
        == pytest.approx(10)
    )
    assert (
        result.gross_loss_usd
        == pytest.approx(6)
    )
    assert (
        result.average_win_usd
        == pytest.approx(10)
    )
    assert (
        result.average_loss_usd
        == pytest.approx(-6)
    )
    assert (
        result.win_rate_percent
        == pytest.approx(
            33.3333333333
        )
    )
    assert (
        result.profit_factor
        == pytest.approx(
            10 / 6
        )
    )
    assert (
        result.total_net_pnl_usd
        == pytest.approx(6.5)
    )
    assert (
        result.return_percent
        == pytest.approx(0.065)
    )
def test_performance_without_closed_trades_is_safe():
    account = build_account()
    account.equity_usd = 9999.5
    account.unrealized_pnl_usd = 0
    account.total_fees_usd = 0.5
    (
        service,
        user,
        _,
        repository,
    ) = build_service(
        account=account
    )
    repository.list_positions.return_value = [
        build_position(
            position_id=24,
            status="OPEN",
            realized_pnl=0,
            fees=0.5,
        )
    ]
    repository.count_orders.return_value = 1
    result = service.get_performance(
        current_user=user,
        bot_id=10,
    )
    assert result.completed_trade_count == 0
    assert result.win_rate_percent == 0
    assert result.average_win_usd == 0
    assert result.average_loss_usd == 0
    assert result.profit_factor is None
