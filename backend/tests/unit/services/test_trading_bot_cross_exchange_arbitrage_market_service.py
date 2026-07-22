from types import (
    SimpleNamespace,
)
import pytest
from app.schemas.market_scanner import (
    MarketTickerBatch,
    MarketTickerSnapshot,
)
from app.services.trading_bot_cross_exchange_arbitrage_market_service import (
    TradingBotCrossExchangeArbitrageMarketService,
    TradingBotPublicMarketDataRegistry,
)
OBSERVED_AT_MS = 1784721600000
class FakePublicMarketClient:
    def __init__(
        self,
        batch,
    ):
        self.batch = batch
        self.calls = []
    async def get_tickers(
        self,
        *,
        category,
    ):
        self.calls.append(
            category
        )
        return self.batch
def build_batch(
    exchange,
    *,
    category="spot",
):
    ticker = MarketTickerSnapshot(
        exchange=exchange,
        category=category,
        symbol="BTCUSDT",
        last_price=100,
        bid_price=99,
        bid_size=100,
        ask_price=100,
        ask_size=100,
        observed_at_ms=(
            OBSERVED_AT_MS
        ),
    )
    return MarketTickerBatch(
        exchange=exchange,
        category=category,
        observed_at_ms=(
            OBSERVED_AT_MS
        ),
        count=1,
        tickers=[ticker],
    )
def build_bot(
    *,
    opportunity_type=(
        "CROSS_EXCHANGE"
    ),
    category="spot",
):
    exchanges = (
        [
            "BYBIT",
            "BINANCE",
        ]
        if opportunity_type
        == "CROSS_EXCHANGE"
        else ["BYBIT"]
    )
    return SimpleNamespace(
        category=category,
        strategy_config={
            "opportunity_type": (
                opportunity_type
            ),
            "starting_asset": "USDT",
            "starting_amount": 100,
            "minimum_profit_percent": 0.1,
            "exchanges": exchanges,
            "markets": [],
        },
    )
def build_account():
    return SimpleNamespace(
        exchange_name="BYBIT",
        is_testnet=True,
    )
def test_default_registry_contains_bybit():
    registry = (
        TradingBotPublicMarketDataRegistry
        .default()
    )
    assert (
        registry.list_exchanges()
        == ("BYBIT",)
    )
def test_registry_normalizes_exchange():
    factory = (
        lambda is_testnet:
        ("client", is_testnet)
    )
    registry = (
        TradingBotPublicMarketDataRegistry({
            " binance ": factory,
        })
    )
    assert (
        registry.list_exchanges()
        == ("BINANCE",)
    )
    assert (
        registry.create_client(
            exchange=" binance ",
            is_testnet=True,
        )
        == ("client", True)
    )
def test_registry_rejects_duplicate():
    registry = (
        TradingBotPublicMarketDataRegistry({
            "BINANCE": (
                lambda is_testnet:
                object()
            ),
        })
    )
    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register(
            exchange="binance",
            factory=(
                lambda is_testnet:
                object()
            ),
        )
@pytest.mark.asyncio
async def test_loads_primary_and_secondary_batches():
    secondary_client = (
        FakePublicMarketClient(
            build_batch(
                "BINANCE"
            )
        )
    )
    registry = (
        TradingBotPublicMarketDataRegistry({
            "BINANCE": (
                lambda is_testnet:
                secondary_client
            ),
        })
    )
    service = (
        TradingBotCrossExchangeArbitrageMarketService(
            registry=registry
        )
    )
    batches = await service.load_batches(
        bot=build_bot(),
        account=build_account(),
        primary_batch=build_batch(
            "BYBIT"
        ),
    )
    assert set(batches) == {
        "BYBIT",
        "BINANCE",
    }
    assert (
        secondary_client.calls
        == ["spot"]
    )
@pytest.mark.asyncio
async def test_missing_provider_is_rejected():
    service = (
        TradingBotCrossExchangeArbitrageMarketService()
    )
    with pytest.raises(
        ValueError,
        match=(
            "not registered for BINANCE"
        ),
    ):
        await service.load_batches(
            bot=build_bot(),
            account=build_account(),
            primary_batch=build_batch(
                "BYBIT"
            ),
        )
@pytest.mark.asyncio
async def test_provider_exchange_mismatch_is_rejected():
    secondary_client = (
        FakePublicMarketClient(
            build_batch(
                "MEXC"
            )
        )
    )
    registry = (
        TradingBotPublicMarketDataRegistry({
            "BINANCE": (
                lambda is_testnet:
                secondary_client
            ),
        })
    )
    service = (
        TradingBotCrossExchangeArbitrageMarketService(
            registry=registry
        )
    )
    with pytest.raises(
        ValueError,
        match="returned MEXC",
    ):
        await service.load_batches(
            bot=build_bot(),
            account=build_account(),
            primary_batch=build_batch(
                "BYBIT"
            ),
        )
@pytest.mark.asyncio
async def test_cross_exchange_requires_spot():
    service = (
        TradingBotCrossExchangeArbitrageMarketService()
    )
    with pytest.raises(
        ValueError,
        match="spot markets only",
    ):
        await service.load_batches(
            bot=build_bot(
                category="linear"
            ),
            account=build_account(),
            primary_batch=build_batch(
                "BYBIT"
            ),
        )
@pytest.mark.asyncio
async def test_non_cross_exchange_returns_empty():
    service = (
        TradingBotCrossExchangeArbitrageMarketService()
    )
    result = await service.load_batches(
        bot=build_bot(
            opportunity_type=(
                "TRIANGULAR"
            )
        ),
        account=build_account(),
        primary_batch=build_batch(
            "BYBIT"
        ),
    )
    assert result == {}
