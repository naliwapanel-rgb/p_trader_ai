from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
import pytest
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
    TradingBotStrategyDecision,
    TradingBotStrategyState,
)
from app.services.trading_bot_runtime_service import (
    TradingBotRuntimeService,
)
NOW = datetime(
    2026,
    7,
    22,
    1,
    0,
    tzinfo=UTC,
)
def build_ticker():
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="linear",
        symbol="BTCUSDT",
        last_price=100,
        bid_price=99.9,
        ask_price=100.1,
        spread=0.2,
        spread_percent=0.2,
        previous_price_24h=99,
        price_change_24h=1,
        price_change_percent_24h=1,
        high_24h=105,
        low_24h=95,
        volume_24h=1000,
        turnover_24h=100000,
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_sample():
    return TradingBotMarketSample(
        observed_at=NOW,
        open_price=100,
        high_price=100,
        low_price=100,
        close_price=100,
        bid_price=99.9,
        ask_price=100.1,
        volume=1000,
        turnover_usd=100000,
        source="TICKER",
    )
def build_bot(
    strategy_type,
    *,
    paper_trading=False,
):
    return SimpleNamespace(
        id=10,
        user_id=7,
        exchange_account_id=5,
        strategy_type=strategy_type,
        strategy_config={},
        symbol="BTCUSDT",
        category="linear",
        timeframe="1m",
        status="RUNNING",
        paper_trading=paper_trading,
    )
def build_service(
    *,
    bot,
    runner,
    history_service,
    state_factory,
    paper_engine=None,
):
    db = MagicMock()
    repository = MagicMock()
    repository.get_by_id_and_user.return_value = (
        bot
    )
    account_repository = MagicMock()
    account_repository.get_by_id_and_user.return_value = (
        SimpleNamespace(
            id=5,
            exchange_name="BYBIT",
            is_active=True,
            is_testnet=True,
        )
    )
    scanner = MagicMock()
    scanner.get_tickers = AsyncMock(
        return_value=SimpleNamespace(
            tickers=[
                build_ticker()
            ]
        )
    )
    service = TradingBotRuntimeService(
        scheduler=MagicMock(),
        session_factory=lambda: db,
        repository_factory=(
            lambda session: repository
        ),
        account_repository_factory=(
            lambda session:
            account_repository
        ),
        market_scanner_service=scanner,
        strategy_runner=runner,
        strategy_state_service_factory=(
            state_factory
        ),
        market_history_service=(
            history_service
        ),
        paper_engine_factory=(
            (
                lambda session:
                paper_engine
            )
            if paper_engine is not None
            else None
        ),
        clock=lambda: NOW,
    )
    return service, db
@pytest.mark.asyncio
async def test_runtime_forwards_history_and_state():
    bot = build_bot("TREND")
    decision = TradingBotStrategyDecision(
        action="HOLD",
        confidence=0,
        reason="Trend runtime integration",
        reference_price=100,
        evaluated_at=NOW,
    )
    runner = MagicMock()
    runner.run = AsyncMock(
        return_value=decision
    )
    history = [
        build_sample()
    ]
    history_service = MagicMock()
    history_service.append_ticker.return_value = (
        history
    )
    state = TradingBotStrategyState()
    state_service = MagicMock()
    state_service.build_from_paper_ledger.return_value = (
        state
    )
    state_factory = MagicMock(
        return_value=state_service
    )
    service, db = build_service(
        bot=bot,
        runner=runner,
        history_service=(
            history_service
        ),
        state_factory=state_factory,
    )
    result = await service.execute_tick({
        "user_id": 7,
        "bot_id": 10,
    })
    assert result["outcome"] == "EVALUATED"
    history_service.append_ticker.assert_called_once_with(
        bot=bot,
        ticker=build_ticker(),
        observed_at=NOW,
    )
    state_factory.assert_called_once_with(
        db
    )
    runner.run.assert_awaited_once_with(
        bot=bot,
        ticker=build_ticker(),
        market_history=history,
        state=state,
    )
@pytest.mark.asyncio
async def test_rule_based_runtime_remains_compatible():
    bot = build_bot("RULE_BASED")
    decision = TradingBotStrategyDecision(
        action="HOLD",
        confidence=0,
        reason="Rule compatibility",
        reference_price=100,
        evaluated_at=NOW,
    )
    runner = MagicMock()
    runner.run = AsyncMock(
        return_value=decision
    )
    history_service = MagicMock()
    state_factory = MagicMock()
    service, _ = build_service(
        bot=bot,
        runner=runner,
        history_service=(
            history_service
        ),
        state_factory=state_factory,
    )
    await service.execute_tick({
        "user_id": 7,
        "bot_id": 10,
    })
    history_service.append_ticker.assert_not_called()
    state_factory.assert_not_called()
    runner.run.assert_awaited_once_with(
        bot=bot,
        ticker=build_ticker(),
    )
