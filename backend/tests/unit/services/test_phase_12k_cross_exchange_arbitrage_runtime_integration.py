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
    13,
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
                "CROSS_EXCHANGE"
            ),
            "starting_asset": "USDT",
            "starting_amount": 100,
            "minimum_profit_percent": 0.1,
            "exchanges": [
                "BYBIT",
                "BINANCE",
            ],
            "markets": [],
            "evaluation_only": True,
        },
        symbol="BTCUSDT",
        category="spot",
        timeframe="1m",
        status="RUNNING",
        paper_trading=True,
        last_run_at=None,
        last_error=None,
    )
def build_account():
    return SimpleNamespace(
        id=5,
        exchange_name="BYBIT",
        is_active=True,
        is_testnet=True,
    )
def build_ticker(
    exchange="BYBIT",
):
    return MarketTickerSnapshot(
        exchange=exchange,
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
def build_batch(
    exchange="BYBIT",
):
    ticker = build_ticker(
        exchange
    )
    return MarketTickerBatch(
        exchange=exchange,
        category="spot",
        observed_at_ms=(
            ticker.observed_at_ms
        ),
        count=1,
        tickers=[ticker],
    )
def build_quote(
    exchange,
):
    return ArbitrageMarketQuote(
        exchange=exchange,
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
    *,
    quotes=None,
    cross_error=None,
):
    bot = build_bot()
    account = build_account()
    primary_batch = build_batch(
        "BYBIT"
    )
    exchange_batches = {
        "BYBIT": primary_batch,
        "BINANCE": build_batch(
            "BINANCE"
        ),
    }
    db = MagicMock()
    repository = MagicMock()
    repository.get_by_id_and_user.return_value = (
        bot
    )
    def save_lifecycle(
        *,
        bot,
        status,
        updated_at,
        **fields,
    ):
        bot.status = status
        bot.updated_at = updated_at
        for key, value in fields.items():
            setattr(
                bot,
                key,
                value,
            )
        return bot
    repository.save_lifecycle.side_effect = (
        save_lifecycle
    )
    account_repository = MagicMock()
    account_repository.get_by_id_and_user.return_value = (
        account
    )
    scanner = MagicMock()
    scanner.get_tickers = AsyncMock(
        return_value=primary_batch
    )
    decision = TradingBotStrategyDecision(
        action="HOLD",
        confidence=0.75,
        reason=(
            "Cross-exchange Arbitrage "
            "evaluation completed"
        ),
        reference_price=100,
        evaluated_at=NOW,
        metadata={
            "opportunity_type": (
                "CROSS_EXCHANGE"
            ),
            "evaluation_only": True,
            "opportunity_detected": True,
        },
    )
    runner = MagicMock()
    runner.run = AsyncMock(
        return_value=decision
    )
    cross_service = MagicMock()
    if cross_error is None:
        cross_service.load_batches = (
            AsyncMock(
                return_value=(
                    exchange_batches
                )
            )
        )
    else:
        cross_service.load_batches = (
            AsyncMock(
                side_effect=cross_error
            )
        )
    quote_service = MagicMock()
    quote_service.build_cross_exchange_quotes.return_value = (
        quotes
        if quotes is not None
        else [
            build_quote("BYBIT"),
            build_quote("BINANCE"),
        ]
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
        cross_exchange_market_service=(
            cross_service
        ),
        clock=lambda: NOW,
    )
    return SimpleNamespace(
        service=service,
        bot=bot,
        account=account,
        primary_batch=primary_batch,
        exchange_batches=exchange_batches,
        repository=repository,
        runner=runner,
        cross_service=cross_service,
        quote_service=quote_service,
        paper_engine=paper_engine,
        db=db,
    )
@pytest.mark.asyncio
async def test_runtime_forwards_cross_exchange_quotes():
    context = build_service()
    result = await (
        context.service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
    )
    assert result["outcome"] == "EVALUATED"
    assert (
        result["decision"]["metadata"][
            "opportunity_type"
        ]
        == "CROSS_EXCHANGE"
    )
    context.cross_service.load_batches.assert_awaited_once_with(
        bot=context.bot,
        account=context.account,
        primary_batch=(
            context.primary_batch
        ),
    )
    context.quote_service.build_cross_exchange_quotes.assert_called_once_with(
        bot=context.bot,
        batches=context.exchange_batches,
    )
    context.quote_service.build_quotes.assert_not_called()
    expected_quotes = (
        context
        .quote_service
        .build_cross_exchange_quotes
        .return_value
    )
    context.runner.run.assert_awaited_once_with(
        bot=context.bot,
        ticker=(
            context
            .primary_batch
            .tickers[0]
        ),
        arbitrage_quotes=(
            expected_quotes
        ),
    )
    context.paper_engine.execute.assert_not_called()
    assert result["paper_execution"] is None
@pytest.mark.asyncio
async def test_cross_exchange_empty_quotes_still_evaluates():
    context = build_service(
        quotes=[]
    )
    result = await (
        context.service.execute_tick({
            "user_id": 7,
            "bot_id": 10,
        })
    )
    assert result["outcome"] == "EVALUATED"
    context.runner.run.assert_awaited_once_with(
        bot=context.bot,
        ticker=(
            context
            .primary_batch
            .tickers[0]
        ),
        arbitrage_quotes=[],
    )
    context.paper_engine.execute.assert_not_called()
@pytest.mark.asyncio
async def test_cross_exchange_provider_failure_marks_error():
    context = build_service(
        cross_error=ValueError(
            "Public provider unavailable"
        )
    )
    with pytest.raises(
        ValueError,
        match="provider unavailable",
    ):
        await (
            context.service.execute_tick({
                "user_id": 7,
                "bot_id": 10,
            })
        )
    assert context.bot.status == "ERROR"
    assert (
        context.bot.last_error
        == "Public provider unavailable"
    )
    context.runner.run.assert_not_awaited()
    context.paper_engine.execute.assert_not_called()
    context.db.rollback.assert_called_once()
