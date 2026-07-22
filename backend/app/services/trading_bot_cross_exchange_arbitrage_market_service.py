from collections.abc import (
    Callable,
)
from typing import (
    Any,
)
from app.exchanges.bybit.market_data import (
    BybitMarketDataClient,
)
from app.schemas.market_scanner import (
    MarketTickerBatch,
)
from app.schemas.trading_bot_strategy import (
    ArbitrageStrategyConfig,
)
PublicMarketDataClientFactory = Callable[
    [bool],
    Any,
]
class TradingBotPublicMarketDataRegistry:
    def __init__(
        self,
        providers: (
            dict[
                str,
                PublicMarketDataClientFactory,
            ]
            | None
        ) = None,
    ):
        self._providers: dict[
            str,
            PublicMarketDataClientFactory,
        ] = {}
        for exchange, factory in (
            providers or {}
        ).items():
            self.register(
                exchange=exchange,
                factory=factory,
            )
    @staticmethod
    def _normalize_exchange(
        exchange: str,
    ) -> str:
        normalized = (
            str(exchange)
            .strip()
            .upper()
        )
        if not normalized:
            raise ValueError(
                "Public market-data exchange "
                "cannot be blank"
            )
        return normalized
    @classmethod
    def default(
        cls,
    ):
        return cls({
            "BYBIT": (
                lambda is_testnet:
                BybitMarketDataClient(
                    is_testnet=is_testnet
                )
            ),
        })
    def register(
        self,
        *,
        exchange: str,
        factory: (
            PublicMarketDataClientFactory
        ),
    ) -> None:
        normalized = (
            self._normalize_exchange(
                exchange
            )
        )
        if not callable(factory):
            raise ValueError(
                "Public market-data provider "
                "factory must be callable"
            )
        if normalized in self._providers:
            raise ValueError(
                "Public market-data provider "
                f"is already registered for "
                f"{normalized}"
            )
        self._providers[
            normalized
        ] = factory
    def create_client(
        self,
        *,
        exchange: str,
        is_testnet: bool,
    ):
        normalized = (
            self._normalize_exchange(
                exchange
            )
        )
        factory = self._providers.get(
            normalized
        )
        if factory is None:
            raise ValueError(
                "Public market-data provider "
                "is not registered for "
                f"{normalized}"
            )
        return factory(
            bool(is_testnet)
        )
    def list_exchanges(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                self._providers
            )
        )
class TradingBotCrossExchangeArbitrageMarketService:
    def __init__(
        self,
        *,
        registry: (
            TradingBotPublicMarketDataRegistry
            | None
        ) = None,
    ):
        self.registry = (
            registry
            or (
                TradingBotPublicMarketDataRegistry
                .default()
            )
        )
    async def load_batches(
        self,
        *,
        bot,
        account,
        primary_batch: MarketTickerBatch,
    ) -> dict[
        str,
        MarketTickerBatch,
    ]:
        config = (
            ArbitrageStrategyConfig
            .model_validate(
                dict(
                    bot.strategy_config
                    or {}
                )
            )
        )
        if (
            config.opportunity_type
            != "CROSS_EXCHANGE"
        ):
            return {}
        category = (
            str(bot.category)
            .strip()
            .lower()
        )
        if category != "spot":
            raise ValueError(
                "Cross-exchange Arbitrage "
                "runtime currently supports "
                "spot markets only"
            )
        account_exchange = (
            str(account.exchange_name)
            .strip()
            .upper()
        )
        if (
            account_exchange
            not in config.exchanges
        ):
            raise ValueError(
                "Primary trading-bot exchange "
                "account must be included in "
                "the configured exchanges"
            )
        validated_primary = (
            MarketTickerBatch
            .model_validate(
                primary_batch
            )
        )
        primary_exchange = (
            str(
                validated_primary.exchange
            )
            .strip()
            .upper()
        )
        if (
            primary_exchange
            != account_exchange
        ):
            raise ValueError(
                "Primary market-data batch "
                "exchange does not match the "
                "trading-bot exchange account"
            )
        if (
            validated_primary.category
            != "spot"
        ):
            raise ValueError(
                "Primary cross-exchange "
                "market-data batch must use "
                "the spot category"
            )
        batches = {
            primary_exchange: (
                validated_primary
            ),
        }
        for exchange in config.exchanges:
            if exchange in batches:
                continue
            client = (
                self.registry.create_client(
                    exchange=exchange,
                    is_testnet=(
                        bool(
                            account.is_testnet
                        )
                    ),
                )
            )
            raw_batch = (
                await client.get_tickers(
                    category="spot"
                )
            )
            batch = (
                MarketTickerBatch
                .model_validate(
                    raw_batch
                )
            )
            batch_exchange = (
                str(batch.exchange)
                .strip()
                .upper()
            )
            if batch_exchange != exchange:
                raise ValueError(
                    "Public market-data provider "
                    f"for {exchange} returned "
                    f"{batch_exchange}"
                )
            if batch.category != "spot":
                raise ValueError(
                    "Cross-exchange public "
                    "market-data providers must "
                    "return spot ticker batches"
                )
            batches[exchange] = batch
        return batches
