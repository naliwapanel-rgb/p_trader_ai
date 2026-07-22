from decimal import (
    Decimal,
)
from app.schemas.arbitrage import (
    ArbitrageMarketQuote,
)
from app.schemas.market_scanner import (
    MarketTickerBatch,
)
from app.schemas.trading_bot_strategy import (
    ArbitrageStrategyConfig,
)
class TradingBotArbitrageQuoteService:
    @staticmethod
    def _decimal(
        value,
    ) -> Decimal:
        return Decimal(
            str(value)
        )
    def build_quotes(
        self,
        *,
        bot,
        account,
        batch: MarketTickerBatch,
    ) -> list[
        ArbitrageMarketQuote
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
            != "TRIANGULAR"
        ):
            return []
        category = (
            str(bot.category)
            .strip()
            .lower()
        )
        if category != "spot":
            raise ValueError(
                "Triangular Arbitrage runtime "
                "currently supports spot "
                "markets only"
            )
        account_exchange = (
            str(account.exchange_name)
            .strip()
            .upper()
        )
        expected_exchange = (
            config.exchanges[0]
        )
        if (
            account_exchange
            != expected_exchange
        ):
            raise ValueError(
                "Triangular Arbitrage exchange "
                "does not match the trading "
                "bot exchange account"
            )
        batch_exchange = (
            str(batch.exchange)
            .strip()
            .upper()
        )
        if (
            batch_exchange
            != expected_exchange
        ):
            raise ValueError(
                "Triangular Arbitrage ticker "
                "batch exchange does not match "
                "the configured exchange"
            )
        allowed_symbols = set(
            config.symbols
        )
        ticker_by_symbol = {
            ticker.symbol
            .strip()
            .upper(): ticker
            for ticker in batch.tickers
        }
        quotes = []
        for market in config.markets:
            if (
                market.exchange
                != expected_exchange
            ):
                continue
            if (
                allowed_symbols
                and market.symbol
                not in allowed_symbols
            ):
                continue
            ticker = ticker_by_symbol.get(
                market.symbol
            )
            if ticker is None:
                continue
            if (
                ticker.bid_price <= 0
                or ticker.ask_price <= 0
                or ticker.bid_size <= 0
                or ticker.ask_size <= 0
                or ticker.ask_price
                < ticker.bid_price
            ):
                continue
            observed_at_ms = (
                ticker.observed_at_ms
                or batch.observed_at_ms
            )
            quotes.append(
                ArbitrageMarketQuote(
                    exchange=(
                        expected_exchange
                    ),
                    symbol=market.symbol,
                    base_asset=(
                        market.base_asset
                    ),
                    quote_asset=(
                        market.quote_asset
                    ),
                    bid_price=self._decimal(
                        ticker.bid_price
                    ),
                    ask_price=self._decimal(
                        ticker.ask_price
                    ),
                    bid_size=self._decimal(
                        ticker.bid_size
                    ),
                    ask_size=self._decimal(
                        ticker.ask_size
                    ),
                    fee_rate_percent=(
                        self._decimal(
                            market
                            .fee_rate_percent
                        )
                    ),
                    slippage_percent=(
                        self._decimal(
                            market
                            .slippage_percent
                        )
                    ),
                    fixed_buy_cost=(
                        self._decimal(
                            market
                            .fixed_buy_cost
                        )
                    ),
                    fixed_sell_cost=(
                        self._decimal(
                            market
                            .fixed_sell_cost
                        )
                    ),
                    observed_at_ms=(
                        observed_at_ms
                    ),
                )
            )
        return quotes

    def build_cross_exchange_quotes(
        self,
        *,
        bot,
        batches: dict[
            str,
            MarketTickerBatch,
        ],
    ) -> list[
        ArbitrageMarketQuote
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
            return []
        category = (
            str(bot.category)
            .strip()
            .lower()
        )
        if category != "spot":
            raise ValueError(
                "Cross-exchange Arbitrage quote "
                "construction currently supports "
                "spot markets only"
            )
        normalized_batches: dict[
            str,
            MarketTickerBatch,
        ] = {}
        for key, raw_batch in (
            batches.items()
        ):
            exchange_key = (
                str(key)
                .strip()
                .upper()
            )
            if not exchange_key:
                raise ValueError(
                    "Cross-exchange batch key "
                    "cannot be blank"
                )
            if (
                exchange_key
                in normalized_batches
            ):
                raise ValueError(
                    "Cross-exchange batches "
                    "cannot contain duplicate "
                    "exchange keys"
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
            if (
                batch_exchange
                != exchange_key
            ):
                raise ValueError(
                    "Cross-exchange batch key "
                    "does not match its exchange"
                )
            if batch.category != "spot":
                raise ValueError(
                    "Cross-exchange ticker "
                    "batches must use the "
                    "spot category"
                )
            normalized_batches[
                exchange_key
            ] = batch
        allowed_symbols = set(
            config.symbols
        )
        ticker_maps = {
            exchange: {
                ticker.symbol
                .strip()
                .upper(): ticker
                for ticker
                in batch.tickers
            }
            for exchange, batch
            in normalized_batches.items()
        }
        quotes = []
        for market in config.markets:
            if (
                market.exchange
                not in config.exchanges
            ):
                continue
            if (
                allowed_symbols
                and market.symbol
                not in allowed_symbols
            ):
                continue
            batch = normalized_batches.get(
                market.exchange
            )
            if batch is None:
                continue
            ticker = (
                ticker_maps[
                    market.exchange
                ]
                .get(
                    market.symbol
                )
            )
            if ticker is None:
                continue
            if (
                ticker.bid_price <= 0
                or ticker.ask_price <= 0
                or ticker.bid_size <= 0
                or ticker.ask_size <= 0
                or ticker.ask_price
                < ticker.bid_price
            ):
                continue
            observed_at_ms = (
                ticker.observed_at_ms
                or batch.observed_at_ms
            )
            quotes.append(
                ArbitrageMarketQuote(
                    exchange=(
                        market.exchange
                    ),
                    symbol=market.symbol,
                    base_asset=(
                        market.base_asset
                    ),
                    quote_asset=(
                        market.quote_asset
                    ),
                    bid_price=self._decimal(
                        ticker.bid_price
                    ),
                    ask_price=self._decimal(
                        ticker.ask_price
                    ),
                    bid_size=self._decimal(
                        ticker.bid_size
                    ),
                    ask_size=self._decimal(
                        ticker.ask_size
                    ),
                    fee_rate_percent=(
                        self._decimal(
                            market
                            .fee_rate_percent
                        )
                    ),
                    slippage_percent=(
                        self._decimal(
                            market
                            .slippage_percent
                        )
                    ),
                    fixed_buy_cost=(
                        self._decimal(
                            market
                            .fixed_buy_cost
                        )
                    ),
                    fixed_sell_cost=(
                        self._decimal(
                            market
                            .fixed_sell_cost
                        )
                    ),
                    observed_at_ms=(
                        observed_at_ms
                    ),
                )
            )
        return quotes
