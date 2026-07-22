from datetime import (
    UTC,
    datetime,
)
from decimal import (
    Decimal,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
import pytest
from app.schemas.arbitrage import (
    ArbitrageMarketQuote,
)
from app.schemas.market_scanner import (
    MarketTickerBatch,
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
from app.services.trading_bot_runtime_service import (
    TradingBotRuntimeService,
)
NOW = datetime(
    2026,
    7,
    22,
    11,
    0,
    tzinfo=UTC,
)
def build_bot():
    return SimpleNamespace(
        id=10,
        user_id=7,
        exchange_account_id=5,
        strategy_type="ARBITRAGE",
        strategy_config={
            "opportunity_type": (
                "TRIANGULAR"
            ),
            "exchanges": ["BYBIT"],
        },
        symbol="BTCUSDT",
        category="spot",
        timeframe="1m",
        status="RUNNING",
        paper_trading=True,
    )
def build_account():
    return SimpleNamespace(
        id=5,
        exchange_name="BYBIT",
        is_active=True,
        is_testnet=True,
    )
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
def build_batch():
    ticker = build_ticker()
    return MarketTickerBatch(
        exchange="BYBIT",
        category="spot",
        observed_at_ms=(
            ticker.observed_at_ms
        ),
        count=1,
        tickers=[ticker],
    )
def build_quote():
    return ArbitrageMarketQuote(
        exchange="BYBIT",
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        bid_price=Decimal("99"),
        ask_price=Decimal("100"),
        bid_size=Decimal("100"),
        ask_size=Decimal("100"),
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_service(
    quotes,
):
    bot = build_bot()
    account = build_account()
    batch = build_batch()
    ticker = batch.tickers[0]
    db = MagicMock()
    repository = MagicMock()
    repository.get_by_id_and_user.return_value = (
        bot
    )
    account_repository = MagicMock()
    account_repository.get_by_id_and_user.return_value = (
        account
    )
    scanner = MagicMock()
    scanner.get_tickers = AsyncMock(
        return_value=batch
    )
    decision = TradingBotStrategyDecision(
        action="HOLD",
        confidence=0.5,
        reason=(
            "Arbitrage runtime evaluation"
        ),
        reference_price=100,
        evaluated_at=NOW,
        metadata={
            "evaluation_only": True,
        },
    )
    runner = MagicMock()
    runner.run = AsyncMock(
        return_value=decision
    )
    quote_service = MagicMock()
    quote_service.build_quotes.return_value = (
        quotes
    )
    paper_engine = MagicMock()
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
        paper_engine_factory=(
            lambda session: paper_engine
        ),
        arbitrage_quote_service=(
            quote_service
        ),
        clock=lambda: NOW,
    )
    return (
        service,
        bot,
        account,
        batch,
        ticker,
        runner,
        quote_service,
        paper_engine,
        scanner,
    )
@pytest.mark.asyncio
async def test_runtime_forwards_triangular_quotes():
    quotes = [
        build_quote()
    ]
    (
        service,
        bot,
        account,
        batch,
        ticker,
        runner,
        quote_service,
        paper_engine,
        scanner,
    ) = build_service(
        quotes
    )
    result = await service.execute_tick({
        "user_id": 7,
        "bot_id": 10,
    })
    assert result["outcome"] == "EVALUATED"
    scanner.get_tickers.assert_awaited_once_with(
        category="spot",
        is_testnet=True,
    )
    quote_service.build_quotes.assert_called_once_with(
        bot=bot,
        account=account,
        batch=batch,
    )
    runner.run.assert_awaited_once_with(
        bot=bot,
        ticker=ticker,
        arbitrage_quotes=quotes,
    )
    paper_engine.execute.assert_not_called()
    assert (
        result["paper_execution"]
        is None
    )
@pytest.mark.asyncio
async def test_runtime_accepts_empty_quote_context():
    (
        service,
        bot,
        account,
        batch,
        ticker,
        runner,
        quote_service,
        paper_engine,
        _,
    ) = build_service([])
    result = await service.execute_tick({
        "user_id": 7,
        "bot_id": 10,
    })
    assert result["outcome"] == "EVALUATED"
    runner.run.assert_awaited_once_with(
        bot=bot,
        ticker=ticker,
        arbitrage_quotes=[],
    )
    paper_engine.execute.assert_not_called()
